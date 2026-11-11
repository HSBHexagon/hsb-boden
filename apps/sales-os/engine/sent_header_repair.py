"""Repair proven Sent copies incorrectly carrying X-Unsent, without SMTP.

Server-side originals are moved into a dedicated backup folder only AFTER a
corrected copy has been appended and verified in Sent. All other mail untouched.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
import hashlib
import json
import os
import re
from pathlib import Path

from hsb_core import normalize_owner
from mailbox_inventory import scan_headers

BACKUP = "HSB-SALES-OS-SENT-ORIGINALS-20261111"
OWNERS = {"JOEL": "j-cherino@hsb-boden.com", "JORDI": "j-post@hsb-boden.com"}


def addresses(value):
    return [a.strip().lower() for _, a in getaddresses([str(value or "")]) if a]


def strip_x_unsent(raw: bytes) -> bytes:
    marker = b"\r\n\r\n"
    idx = raw.find(marker)
    if idx < 0:
        raise ValueError("MIME_HEADER_BODY_SEPARATOR_MISSING")
    header, body = raw[:idx], raw[idx + len(marker):]
    lines = header.split(b"\r\n")
    hit = [i for i, line in enumerate(lines) if line.lower().startswith(b"x-unsent:")]
    if len(hit) != 1 or lines[hit[0]].split(b":", 1)[1].strip() != b"1":
        raise ValueError("UNSENT_HEADER_UNEXPECTED")
    if hit[0] + 1 < len(lines) and lines[hit[0] + 1].startswith((b" ", b"\t")):
        raise ValueError("UNSENT_HEADER_FOLDED")
    corrected = b"\r\n".join(line for i, line in enumerate(lines) if i != hit[0]) + marker + body
    oldmsg = BytesParser(policy=policy.default).parsebytes(raw)
    msg = BytesParser(policy=policy.default).parsebytes(corrected)
    if (msg.get("X-Unsent") is not None
            or msg.get("Message-ID") != oldmsg.get("Message-ID")
            or msg.get("To") != oldmsg.get("To")
            or msg.get("From") != oldmsg.get("From")
            or corrected.split(marker, 1)[1] != body):
        raise ValueError("CORRECTED_MIME_INVALID")
    return corrected


def plan_sent_repairs(leads: list[dict], box: dict, owner: str):
    sender = OWNERS[owner]
    proof = defaultdict(list)
    for lead in leads:
        if (normalize_owner(lead.get("Verantwortlicher")) != owner
                or str(lead.get("Send_Status") or "").lower() != "sent"
                or not lead.get("Send_Datum")):
            continue
        account = str(lead.get("Sender_Account") or "").strip().lower()
        if account and account != sender:
            continue
        for mid in {str(lead.get(k) or "").strip()
                    for k in ("Internet_Message_ID", "Outbound_ID")} - {""}:
            proof[mid].append(lead)
    sent = box["sent"]
    midcounts = Counter(s.get("message_id") for s in sent if s.get("message_id"))
    drafts = {d.get("message_id") for d in box["drafts"] if d.get("message_id")}
    flagged = [s for s in sent if s.get("x_unsent")]
    planned = []
    for s in flagged:
        mid = str(s.get("message_id") or "").strip()
        matches = {str(l.get("Lead-ID") or ""): l for l in proof[mid]}
        if (not mid or midcounts[mid] != 1 or mid in drafts
                or s.get("draft_flag") or len(matches) != 1
                or s.get("senders") != [sender]
                or len(s.get("recipients") or []) != 1
                or not s.get("uid") or not s.get("uidvalidity")):
            continue
        lead = next(iter(matches.values()))
        if (s["recipients"] != [str(lead.get("E-Mail") or "").strip().lower()]
                or (s.get("lead_id") and s["lead_id"] != lead.get("Lead-ID"))):
            continue
        planned.append({"uid": s["uid"], "uidvalidity": s["uidvalidity"],
                        "message_id": mid, "recipient": s["recipients"][0],
                        "sender": sender})
    summary = {"sent_with_unsent_header": len(flagged),
               "eligible_to_correct": len(planned),
               "held": len(flagged) - len(planned)}
    return planned, summary


def _uid_search(imap, mid):
    typ, data = imap.uid("SEARCH", None, "HEADER", "Message-ID", f'"{mid}"')
    if typ != "OK" or not data or not isinstance(data[0], bytes):
        raise RuntimeError("UID_SEARCH_UNAVAILABLE")
    return data[0].split()


def _read_uid(imap, uid):
    typ, data = imap.uid("FETCH", str(uid), "(UID INTERNALDATE FLAGS BODY.PEEK[])")
    pairs = [entry for entry in (data or []) if isinstance(entry, tuple)]
    if typ != "OK" or len(pairs) != 1:
        raise RuntimeError("ORIGINAL_FETCH_NOT_UNIQUE")
    meta, raw = pairs[0]
    found = re.search(rb"\bUID (\d+)\b", meta)
    internal_date = re.search(rb'INTERNALDATE "([^"]+)"', meta)
    if not found or found[1].decode() != str(uid) or not internal_date:
        raise RuntimeError("ORIGINAL_UID_OR_DATE_MISSING")
    return raw, '"' + internal_date[1].decode("ascii") + '"'


def _validity(imap):
    val = imap.response("UIDVALIDITY")[1]
    if not val or not val[0]:
        raise RuntimeError("UIDVALIDITY_UNAVAILABLE")
    return val[0].decode() if isinstance(val[0], bytes) else str(val[0])


def _ensure_backup(imap):
    typ, data = imap.list("", BACKUP)
    if typ != "OK":
        raise RuntimeError("BACKUP_LIST_UNAVAILABLE")
    if not data or not any(x for x in data):
        typ, _ = imap.create(BACKUP)
        if typ != "OK":
            raise RuntimeError("BACKUP_CREATE_FAILED")


def _fetch_hash_by_mid(imap, mid):
    hashes = []
    for uid in _uid_search(imap, mid):
        raw, _ = _read_uid(imap, uid.decode())
        hashes.append((uid.decode(), hashlib.sha256(raw).digest(), raw))
    return hashes


def apply_one(client, candidate):
    sent = client.cfg["sent_folder"]
    with client._get_imap() as imap:
        typ, _ = imap.select(sent, readonly=False)
        if typ != "OK" or _validity(imap) != candidate["uidvalidity"]:
            raise RuntimeError("SENT_FOLDER_UIDVALIDITY_CHANGED")
        if _uid_search(imap, candidate["message_id"]) != [candidate["uid"].encode()]:
            raise RuntimeError("SENT_IDENTITY_CHANGED")
        raw, internal_date = _read_uid(imap, candidate["uid"])
        message = BytesParser(policy=policy.default).parsebytes(raw)
        if (message.get("Message-ID") != candidate["message_id"]
                or addresses(message.get("To")) != [candidate["recipient"]]
                or addresses(message.get("From")) != [candidate["sender"]]):
            raise RuntimeError("ORIGINAL_MIME_IDENTITY_CHANGED")
        corrected = strip_x_unsent(raw)
        old_digest = hashlib.sha256(raw).digest()
        new_digest = hashlib.sha256(corrected).digest()
        _ensure_backup(imap)
        # A short-lived duplicate is safer than moving the only Sent copy first.
        typ, _ = imap.append(sent, r"(\Seen)", internal_date, corrected)
        if typ != "OK":
            raise RuntimeError("CORRECTED_APPEND_FAILED")
        typ, _ = imap.select(sent, readonly=False)
        if typ != "OK":
            raise RuntimeError("SENT_RESELECT_FAILED")
        variants = _fetch_hash_by_mid(imap, candidate["message_id"])
        if (len(variants) != 2
                or len([v for v in variants if v[1] == old_digest]) != 1
                or len([v for v in variants if v[1] == new_digest]) != 1
                or not any(v[0] == candidate["uid"] and v[1] == old_digest for v in variants)):
            raise RuntimeError("CORRECTED_SENT_READBACK_FAILED")
        typ, _ = imap.uid("MOVE", candidate["uid"], BACKUP)
        if typ != "OK":
            raise RuntimeError("ORIGINAL_MOVE_TO_BACKUP_FAILED")
        typ, _ = imap.select(sent, readonly=True)
        if typ != "OK":
            raise RuntimeError("SENT_POST_MOVE_UNAVAILABLE")
        remaining = _fetch_hash_by_mid(imap, candidate["message_id"])
        if len(remaining) != 1 or remaining[0][1] != new_digest:
            raise RuntimeError("SENT_POST_MOVE_NOT_UNIQUE")
        typ, _ = imap.select(BACKUP, readonly=True)
        if typ != "OK":
            raise RuntimeError("BACKUP_FOLDER_UNREADABLE")
        archived = _fetch_hash_by_mid(imap, candidate["message_id"])
        if not any(item[1] == old_digest for item in archived):
            raise RuntimeError("BACKUP_ORIGINAL_READBACK_FAILED")


def main():
    from com_mailbox_manager import ComMailboxClient
    from sync_to_google_sheet import SPREADSHEET_ID, get_sheets_service

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--owner", choices=list(OWNERS) + ["ALL"], default="JORDI")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 400:
        raise ValueError("INVALID_REPAIR_BATCH_LIMIT")
    if os.environ.get("HSB_CUSTOMER_SEND_ENABLED", "no") == "yes":
        raise RuntimeError("REPAIR_CANNOT_RUN_WITH_SMTP_ENABLED")
    rows = get_sheets_service().spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425"
    ).execute().get("values", [])
    if len(rows) != 6425 or not rows[0] or rows[0][0] != "Lead-ID":
        raise RuntimeError("CRM_SHAPE_INVALID")
    leads = [dict(zip(rows[0], row)) for row in rows[1:]]
    owners = list(OWNERS) if args.owner == "ALL" else [args.owner]
    report = {"mode": "apply" if args.apply else "preview", "owners": {},
              "customer_emails_sent": 0, "checked_at": datetime.now(timezone.utc).isoformat()}
    for owner in owners:
        client = ComMailboxClient(owner, timeout=60)
        box = scan_headers(owner, client)
        plan, summary = plan_sent_repairs(leads, box, owner)
        report["owners"][owner] = summary
        applied = 0
        if args.apply:
            for candidate in plan[:args.limit]:
                apply_one(client, candidate)
                applied += 1
        summary["corrected_and_verified"] = applied
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
