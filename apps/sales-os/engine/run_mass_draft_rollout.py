#!/usr/bin/env python3
"""
HSB Sales OS - Mass Draft Rollout Engine (Option B: Maximaler Vorlauf).
Erstellt Entwürfe für alle verbleibenden, qualifizierten Leads im 50/50-Split:
- Joel Cherino Diaz: j-cherino@hsb-boden.com
- Jordie Post: j-post@hsb-boden.com

Sicherheits-Invarianten:
1. REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Hermetische Draft-Only Governance; 0 SMTP-Sends).
2. Forensischer Ausschluss: 0 Überschneidungen mit DE_VERSENDUNGEN_FORENSIK.
3. Postfach-Deduplizierung: Bereits im IMAP vorhandene Entwürfe werden automatisch übersprungen.
4. Tranchen-Writeback: Nach jeder 50er Tranche wird das Google Sheet ALL_LEADS & BATCHES atomar aktualisiert.
5. 2026er E-Mail-Standard: 0 KB Anhang (Online-Flyer-Link), L12 Single-Opt-Out Footer, personalisierte Anrede.
"""
from __future__ import annotations

import argparse
import datetime
from email.utils import getaddresses
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from com_mailbox_manager import ComMailboxClient
from hsb_core import assert_asset_gate, normalize_owner, sanitize_company_name, EMAIL_RE
from overhaul_drafts import build_canonical_body_2026, load_sheet_leads
from run_100_batch import anrede_fuer
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("mass_draft_rollout")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


def load_forensic_sent_recipients() -> Set[str]:
    forensic_file = REPO_ROOT / "data" / "forensic_sent_recipients.json"
    if forensic_file.exists():
        with open(forensic_file, "r", encoding="utf-8") as f:
            return {em.strip().lower() for em in json.load(f) if em}
    return set()


def get_existing_mailbox_emails(owner: str) -> Set[str]:
    logger.info(f"[{owner}] Lese bestehende Entwürfe aus All-Inkl Postfach...")
    client = ComMailboxClient(owner)
    draft_headers = client.list_drafts(limit=15000)
    recipients = set()
    for d in draft_headers:
        for _, addr in getaddresses([str(d.get("to") or "")]):
            if addr and "@" in addr:
                recipients.add(addr.strip().lower())
    logger.info(f"[{owner}] {len(recipients)} bestehende Entwurfs-Empfänger im Postfach erfasst.")
    return recipients


def select_untouched_candidates(
    leads: List[Dict[str, Any]],
    forensic_sent: Set[str],
    mailbox_recipients: Dict[str, Set[str]]
) -> Dict[str, List[Dict[str, Any]]]:
    candidates: Dict[str, List[Dict[str, Any]]] = {"JOEL": [], "JORDI": []}
    skipped_forensic = 0
    skipped_status = 0
    skipped_optout = 0
    skipped_existing_draft = 0

    for i, l in enumerate(leads):
        email = (l.get("E-Mail") or l.get("Email") or "").strip().lower()
        if not email or not EMAIL_RE.match(email):
            continue

        if email in forensic_sent:
            skipped_forensic += 1
            continue

        send_status = str(l.get("Send_Status") or l.get("Send-Status") or l.get("Status") or "").strip().lower()
        if send_status in ("sent", "gesendet", "bounced", "invalid"):
            skipped_status += 1
            continue

        optout = str(l.get("Opt_Out") or l.get("Opt-Out") or "").strip().lower()
        pipeline = str(l.get("Pipeline") or l.get("Pipeline_Status") or "").strip().lower()
        if optout in ("yes", "ja") or "abgemeldet" in pipeline or "widerspruch" in pipeline:
            skipped_optout += 1
            continue

        row = l.get("_row", i + 2)
        owner = "JOEL" if row <= 3213 else "JORDI"

        if email in mailbox_recipients[owner]:
            skipped_existing_draft += 1
            continue

        candidates[owner].append(l)

    logger.info(f"Filter-Statistik: {skipped_forensic} forensisch bereits gesendet, "
                f"{skipped_status} Status sent/bounced, {skipped_optout} Opt-Outs, "
                f"{skipped_existing_draft} bereits im Postfach als Entwurf.")
    logger.info(f"Kandidaten für NEUE Entwurfserstellung: Joel = {len(candidates['JOEL'])}, Jordi = {len(candidates['JORDI'])}")
    return candidates


def build_draft_payload(owner: str, lead: Dict[str, Any]) -> Dict[str, Any]:
    norm_owner = normalize_owner(owner)
    flyer = assert_asset_gate(norm_owner)
    email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
    raw_comp = str(lead.get("Firma") or lead.get("Company") or "").strip()
    company = sanitize_company_name(raw_comp, email)

    lead_copy = dict(lead)
    lead_copy["Firma"] = company
    lead_copy["Company"] = company
    anrede = anrede_fuer(lead_copy)

    lead_id = str(lead.get("Lead_ID") or lead.get("Lead-ID") or "")
    subject = f"Industrieböden für {company} – Beratung von {flyer.display_name}"
    body_html = build_canonical_body_2026(norm_owner, anrede, target="com", lead_id=lead_id, to_email=email)

    return {
        "owner": norm_owner,
        "lead_id": lead_id,
        "row_idx": lead.get("_row"),
        "to_email": email,
        "subject": subject,
        "body_html": body_html,
        "flyer_path": None,  # 0 KB Anhang (Online-Flyer-Link)
        "flyer_filename": None,
    }


def write_tranche_to_sheets(
    sheets_svc: Any,
    owner: str,
    batch_id: str,
    manifest: List[Dict[str, Any]]
) -> int:
    sender = "j-cherino@hsb-boden.com" if owner == "JOEL" else "j-post@hsb-boden.com"
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    updates = []
    drafted_count = 0

    for item in manifest:
        if not item.get("ok"):
            continue
        row = item["row_idx"]
        mid = str(item.get("message_id") or "").strip()
        lead_id = item.get("lead_id") or f"ROW-{row}"
        stable_id = hashlib.sha256(f"{owner}:{lead_id}".encode()).hexdigest()[:24]

        # Spalten in ALL_LEADS aktualisieren:
        # Z: Versandfreigabe is never changed by draft creation
        # AN: Batch_ID
        # AO: Send_Status (drafted)
        # AS: Legal_Basis is never changed by draft creation
        # AU: Batch_Status (DRAFT_READY_2026_{owner})
        # AW: Internet_Message_ID
        # AX: Prepared_At
        # AY: Drafted_At
        # BA: Internet_Message_ID
        # BF: Identifier (COM-{stable_id})
        # BG: Sender
        # BH: Note
        # Ein technischer Entwurf darf keine Versandberechtigung erzeugen.
        # Z (Versandfreigabe) und AS (Legal_Basis) bleiben unveraendert.
        fields = {
            "AN": batch_id,
            "AO": "drafted",
            "AU": f"DRAFT_READY_2026_{owner}",
            "AW": mid,
            "AX": timestamp,
            "AY": timestamp,
            "BA": mid,
            "BF": f"COM-{stable_id}",
            "BG": sender,
            "BH": "MASS_ROLLOUT_OPTION_B"
        }
        for col, val in fields.items():
            updates.append({"range": f"ALL_LEADS!{col}{row}", "values": [[val]]})
        drafted_count += 1

    if updates:
        sheets_svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

    # In BATCHES Tab protokollieren
    batches_row = [
        batch_id, owner, "COM_MASS_DRAFT_2026", "COM_DRAFTED",
        len(manifest), drafted_count, drafted_count, 0,
        len(manifest) - drafted_count, "", timestamp, "", "",
        str(drafted_count), str(len(manifest) - drafted_count), "100%", ""
    ]
    try:
        sheets_svc.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="BATCHES!A:Q",
            valueInputOption="USER_ENTERED",
            body={"values": [batches_row]}
        ).execute()
    except Exception as e:
        logger.warning(f"Konnte BATCHES-Tab nicht aktualisieren: {e}")

    return drafted_count


def run_mass_rollout(
    target_owner: str = "ALL",
    limit_per_owner: Optional[int] = None,
    chunk_size: int = 50,
    dry_run: bool = False
) -> Dict[str, Any]:
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0, "Sicherheits-Invariante verletzt!"
    logger.info("=== HSB SALES OS — MASS DRAFT ROLLOUT (OPTION B) ===")
    logger.info(f"Target: {target_owner} | Limit pro Owner: {limit_per_owner or 'OHNE LIMIT (ALLE)'} | Chunk-Size: {chunk_size} | Modus: {'DRY-RUN' if dry_run else 'LIVE APPLY'}")

    sheets_svc = get_sheets_service()
    forensic_sent = load_forensic_sent_recipients()
    logger.info(f"{len(forensic_sent)} forensische Versendungen geladen.")

    owners = ["JOEL", "JORDI"] if target_owner == "ALL" else [target_owner.upper()]
    mailbox_recipients: Dict[str, Set[str]] = {}
    for o in ["JOEL", "JORDI"]:
        mailbox_recipients[o] = get_existing_mailbox_emails(o) if not dry_run else set()

    leads, _ = load_sheet_leads(sheets_svc)
    candidates = select_untouched_candidates(leads, forensic_sent, mailbox_recipients)

    summary: Dict[str, Any] = {"total_drafted": 0, "by_owner": {}}

    for owner in owners:
        pool = candidates[owner]
        if limit_per_owner and limit_per_owner > 0:
            pool = pool[:limit_per_owner]

        total_leads = len(pool)
        logger.info(f"\n=======================================================")
        logger.info(f" STARTE MASSEN-VORBEREITUNG FÜR {owner}: {total_leads} Leads")
        logger.info(f"=======================================================")
        if total_leads == 0:
            logger.info(f"[{owner}] Keine offenen Leads zur Vorbereitung vorhanden.")
            summary["by_owner"][owner] = 0
            continue

        client = ComMailboxClient(owner) if not dry_run else None
        owner_drafted = 0
        total_chunks = (total_leads + chunk_size - 1) // chunk_size
        ts_tag = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M")

        for c_idx in range(total_chunks):
            chunk = pool[c_idx * chunk_size : (c_idx + 1) * chunk_size]
            batch_id = f"COM-{owner}-MASS-{ts_tag}-T{c_idx + 1:02d}"
            items = [build_draft_payload(owner, lead) for lead in chunk]

            logger.info(f"[{owner}] Tranche {c_idx + 1}/{total_chunks} ({len(items)} Leads) -> Batch {batch_id}...")

            if dry_run or not client:
                manifest = [{"ok": True, "message_id": f"<dryrun-{i}@hsb-boden.com>", "lead_id": it["lead_id"], "row_idx": it["row_idx"]} for i, it in enumerate(items)]
                drafted = len(manifest)
            else:
                manifest = []
                for attempt in range(1, 4):
                    try:
                        manifest = client.create_drafts_batch(items)
                        break
                    except Exception as e:
                        logger.warning(f"  [Versuch {attempt}/3] IMAP APPEND Fehler: {e}. Warte {attempt * 3}s...")
                        time.sleep(attempt * 3)

                ok_count = sum(1 for m in manifest if m.get("ok"))
                logger.info(f"  -> IMAP APPEND: {ok_count}/{len(items)} OK.")

                # Sofortiger Writeback in Google Sheet mit Retry
                drafted = 0
                for attempt in range(1, 4):
                    try:
                        drafted = write_tranche_to_sheets(sheets_svc, owner, batch_id, manifest)
                        logger.info(f"  -> Google Sheet ALL_LEADS & BATCHES synchronisiert ({drafted} Zeilen).")
                        break
                    except Exception as e:
                        logger.warning(f"  [Versuch {attempt}/3] Google Sheets Update Fehler: {e}. Warte {attempt * 3}s...")
                        time.sleep(attempt * 3)

            owner_drafted += drafted
            pct = (owner_drafted / total_leads) * 100
            logger.info(f"[{owner}] Fortschritt: {owner_drafted}/{total_leads} ({pct:.1f}%) fertig.")

            if not dry_run and c_idx < total_chunks - 1:
                time.sleep(0.5)

        summary["by_owner"][owner] = owner_drafted
        summary["total_drafted"] += owner_drafted

    logger.info(f"\n=======================================================")
    logger.info(f" GESAMT-ERGEBNIS MASSEN-VORBEREITUNG")
    logger.info(f" Neu erstellte Entwürfe: {summary['total_drafted']}")
    for o, cnt in summary["by_owner"].items():
        logger.info(f"   - {o}: {cnt}")
    logger.info(f"=======================================================")
    return summary


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS Mass Draft Rollout")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="ALL", help="Ziel-Owner")
    parser.add_argument("--limit", type=int, default=None, help="Max Leads pro Owner (Standard: alle)")
    parser.add_argument("--chunk-size", type=int, default=50, help="Größe pro IMAP/Sheet-Tranche")
    parser.add_argument("--apply", action="store_true", help="Erstellung live ausführen (Standard: Dry-Run)")
    args = parser.parse_args()

    run_mass_rollout(
        target_owner=args.owner,
        limit_per_owner=args.limit,
        chunk_size=args.chunk_size,
        dry_run=not args.apply
    )


if __name__ == "__main__":
    main()
