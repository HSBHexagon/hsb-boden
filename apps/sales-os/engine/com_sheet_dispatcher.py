#!/usr/bin/env python3
"""Existing BATCHES ledger -> All-Inkl IMAP draft worker. NEVER sends mail.

Safe modes:
  --once       read-only check; doesn't touch the CRM or postboxes
  --apply      process a COM_REQUESTED row once with fail-closed gates
System of record: Google Sheets. No second queue database or HTTP endpoint.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import getaddresses
import fcntl
import hashlib
import os
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
from com_batch_selector import select_com_eligible_leads
from com_mailbox_manager import ComMailboxClient
from high_volume_matrix_engine import load_leads_authoritative
from run_com_batch import run_com_batch_in_memory
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from canonical_template_factory import CANONICAL_FLYERS
from contextlib import nullcontext
from cloud_worker_lock import singleton_cloud_lock

PINNED_ASSET_HASHES = {
    "JOEL": "6ac5ed1112c88768ac56950faab8802ceaa2817913f35a7b95e73ee79c3431d8",
    "JORDI": "a11876f02b54421bcafd9a6b8ec6f62d748e383b26fcadc8bbe834ee7ffbc4ce",
}
JOB_PATTERN = re.compile(r"^COM-(JOEL|JORDI)-[A-Za-z0-9_-]{8,90}$")
MAX_BATCH = 100


def parse_pending_jobs(rows: list[list[Any]]) -> list[dict[str, Any]]:
    result = []
    for line, values in enumerate(rows[1:], start=2):
        if len(values) < 5:
            continue
        ident, owner, kind, status, requested = (str(values[i]) for i in range(5))
        if kind != "COM_DRAFT_V2" or status != "COM_REQUESTED":
            continue
        if not JOB_PATTERN.fullmatch(ident) or ident.split("-")[1] != owner:
            continue
        try:
            count = int(float(requested))
        except (ValueError, TypeError):
            count = 0
        result.append({"batch_id": ident, "owner": owner, "count": count, "row": line})
    return result


def plan_recipients(leads: list[dict], owner: str, count: int,
                    already_drafted: set[str]) -> dict[str, Any]:
    if not 1 <= count <= MAX_BATCH:
        return {"ready": False, "eligible_count": 0, "leads": [], "reason": "INVALID_COUNT"}
    # Selector already checks legal evidence, explicit approval, suppression,
    # outbound history, owner and valid recipient address. No exceptions.
    candidates = select_com_eligible_leads(leads, owner=owner, limit=len(leads))
    existing = {email.lower().strip() for email in already_drafted}
    candidates = [x for x in candidates
                  if str(x.get("Email") or "").strip().lower() not in existing]
    pool = candidates[:count]
    return {"ready": len(pool) == count, "eligible_count": len(candidates),
            "leads": pool, "reason": "" if len(pool) == count else "INSUFFICIENT_VERIFIED_LEADS"}


def _existing_mailbox_addresses(client: ComMailboxClient) -> set[str]:
    # Includes legacy drafts without sheet IDs, preventing duplicate recipients.
    draft_headers = client.list_drafts(limit=10000)
    addresses: set[str] = set()
    for draft in draft_headers:
        for _, addr in getaddresses([str(draft.get("to") or "")]):
            if addr:
                addresses.add(addr.strip().lower())
    return addresses


def verify_manifest_on_server(client: ComMailboxClient, manifest: list[dict]) -> set[str]:
    """Only acknowledge APPENDs whose Message-IDs exist in server-side Drafts."""
    stored = {str(row.get("message_id") or "").strip()
              for row in client.list_drafts(limit=10000)}
    return {str(item.get("message_id"))
            for item in manifest
            if item.get("ok") is True
            and str(item.get("message_id") or "").strip() in stored}


def _asset_gate(owner: str) -> None:
    path = Path(CANONICAL_FLYERS[owner]["path"])
    if not path.is_file():
        raise RuntimeError("ASSET_MISSING")
    if hashlib.sha256(path.read_bytes()).hexdigest() != PINNED_ASSET_HASHES[owner]:
        raise RuntimeError("ASSET_SHA256_MISMATCH")


def _update(service, values: list[dict]) -> None:
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": values}
    ).execute()


def _mark(service, row: int, status: str, count: int, drafted: int,
          reason: str = "") -> None:
    _update(service, [
        {"range": f"BATCHES!D{row}", "values": [[status]]},
        {"range": f"BATCHES!F{row}", "values": [[drafted]]},
        {"range": f"BATCHES!N{row}:Q{row}",
         "values": [[drafted, max(0, count-drafted),
                     f"{round(100*drafted/count) if count else 0}%", reason[:250]]]}
    ])


def _write_drafts(service, batch_id: str, owner: str, manifest: list[dict]) -> int:
    values = []
    timestamp = datetime.now(timezone.utc).isoformat()
    sender = "j-cherino@hsb-boden.com" if owner == "JOEL" else "j-post@hsb-boden.com"
    drafted = 0
    for item in manifest:
        if item.get("ok") is not True:
            continue
        row = item.get("row_idx")
        mid = item.get("message_id")
        if not isinstance(row, int) or row < 2 or not mid:
            raise RuntimeError("IMAP_WRITEBACK_MISSING_ID")
        stable_id = hashlib.sha256(f"{owner}:{item['lead_id']}".encode()).hexdigest()[:24]
        fields = {
            "AN": batch_id, "AO": "drafted", "AU": "DRAFTED_COM_2026",
            "AW": str(mid), "AX": timestamp, "BA": str(mid),
            "BF": "COM-"+stable_id, "BG": sender
        }
        for col, val in fields.items():
            values.append({"range": f"ALL_LEADS!{col}{row}", "values": [[val]]})
        drafted += 1
    if values:
        _update(service, values)
    return drafted


def process_pending(service, apply: bool = False) -> list[dict]:
    rows = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="BATCHES!A1:Q1000"
    ).execute().get("values", [])
    outcomes = []
    for job in parse_pending_jobs(rows):
        row, owner, count = job["row"], job["owner"], job["count"]
        if not 1 <= count <= MAX_BATCH:
            if apply:
                _mark(service, row, "COM_BLOCKED", count, 0, "INVALID_COUNT")
            outcomes.append({**job, "status": "COM_BLOCKED", "reason": "INVALID_COUNT"})
            continue
        # In production only Google Sheets live, no stale XLSX fallback.
        leads = load_leads_authoritative(require_live=True)
        initial = plan_recipients(leads, owner, count, set())
        if not initial["ready"]:
            if apply:
                _mark(service, row, "COM_BLOCKED", count, 0, initial["reason"])
            outcomes.append({**job, "status": "COM_BLOCKED", "reason": initial["reason"]})
            continue
        _asset_gate(owner)
        client = ComMailboxClient(owner)
        existing = _existing_mailbox_addresses(client)
        plan = plan_recipients(leads, owner, count, existing)
        if not plan["ready"]:
            if apply:
                _mark(service, row, "COM_BLOCKED", count, 0, plan["reason"])
            outcomes.append({**job, "status": "COM_BLOCKED", "reason": plan["reason"]})
            continue
        if not apply:
            outcomes.append({**job, "status": "READY_PREVIEW", "selected": count})
            continue
        _mark(service, row, "COM_PROCESSING", count, 0, "IMAP_APPEND_IN_PROGRESS")
        try:
            result = run_com_batch_in_memory(plan["leads"], owner=owner,
                                              limit=count, dry_run=False)
            verified_ids = verify_manifest_on_server(client, result["manifest"])
            verified_manifest = [
                {**item, "ok": item.get("ok") is True and
                  str(item.get("message_id")) in verified_ids}
                for item in result["manifest"]
            ]
            written = _write_drafts(service, job["batch_id"], owner, verified_manifest)
            status = "COM_DRAFTED" if written == count and not result["failed_count"] else "COM_REVIEW"
            _mark(service, row, status, count, written,
                  "" if status == "COM_DRAFTED" else "PARTIAL_OR_UNKNOWN_IMAP_RESULT")
            outcomes.append({**job, "status": status, "drafted": written})
        except Exception:
            # No retry after unknown APPEND outcome. A human must reconcile
            # mailbox Message-IDs and CRM first to prevent duplicate drafts.
            _mark(service, row, "COM_REVIEW", count, 0, "IMAP_OUTCOME_UNCERTAIN_MANUAL_REVIEW")
            raise
    return outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description="HSB .com BATCHES worker, draft-only")
    parser.add_argument("--apply", action="store_true",
                        help="Process pending jobs; default is read-only.")
    args = parser.parse_args()
    lockpath = ROOT / ".com_dispatcher.lock"
    with lockpath.open("a+") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("COM_DISPATCHER_ALREADY_RUNNING")
            return
        bucket = os.getenv("HSB_COM_LOCK_BUCKET", "").strip()
        # Cloud writes only when the deployment explicitly enables them.
        apply = args.apply and (not bucket or os.getenv("HSB_COM_CLOUD_WRITE_ENABLED") == "1")
        ctx = singleton_cloud_lock(bucket) if bucket else nullcontext(True)
        with ctx as acquired:
            if not acquired:
                print("COM_CLOUD_WORKER_LOCKED")
                return
            results = process_pending(get_sheets_service(), apply=apply)
            for result in results:
                print(f"{result['batch_id']} {result['status']} "
                      f"{result.get('drafted', 0)}/{result['count']}")
            if not results:
                print("NO_NEW_COM_REQUESTS")


if __name__ == "__main__":
    main()
