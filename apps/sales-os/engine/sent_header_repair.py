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


def purge_verified_backups(client, archive_dir=None, *, apply=False):
    """Sichert Backups aus HSB-SALES-OS-SENT-ORIGINALS-20261111 lokal und löscht sie nur,
    wenn für jede Message-ID eine saubere Sent-Kopie ohne X-Unsent verifiziert ist."""
    import email as email_mod
    import hashlib
    from pathlib import Path

    sent_folder = client.cfg.get("sent_folder")
    if not sent_folder:
        raise RuntimeError("SENT_FOLDER_MISSING")

    arc_path = Path(archive_dir) if archive_dir else None
    with client._get_imap() as imap:
        try:
            res, _ = imap.select(BACKUP, readonly=True)
        except TypeError:
            res, _ = imap.select(BACKUP)
        if res != "OK":
            return {"verified_backups": 0, "purged_backups": 0, "applied": apply, "archive_dir": str(arc_path) if arc_path else ""}

        typ, data = imap.uid("search", None, "ALL")
        if typ != "OK":
            raise RuntimeError("BACKUP_SEARCH_FAILED")
        raw_uids = data[0].split() if data and data[0] else []
        backup_uids = [u.decode() if isinstance(u, bytes) else str(u) for u in raw_uids]
        if not backup_uids:
            return {"verified_backups": 0, "purged_backups": 0, "applied": apply, "archive_dir": str(arc_path) if arc_path else ""}

        backups = []
        for start in range(0, len(backup_uids), 100):
            chunk = backup_uids[start : start + 100]
            typ_f, fetched = imap.uid("fetch", ",".join(chunk), "(UID BODY.PEEK[])")
            if typ_f != "OK":
                raise RuntimeError("BACKUP_FETCH_FAILED")
            items = fetched or []
            for idx, item in enumerate(items):
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                m_uid = re.search(rb"\bUID (\d+)\b", item[0])
                if not m_uid and idx + 1 < len(items) and isinstance(items[idx + 1], bytes):
                    m_uid = re.search(rb"\bUID (\d+)\b", items[idx + 1])
                if not m_uid:
                    raise RuntimeError("BACKUP_UID_MISSING")
                raw = item[1] or b""
                parsed = email_mod.message_from_bytes(raw)
                backups.append({
                    "uid": m_uid.group(1).decode(),
                    "message_id": str(parsed.get("Message-ID") or "").strip().lower(),
                    "lead_id": str(parsed.get("X-HSB-Lead-ID") or "").strip(),
                    "to": str(parsed.get("To") or "").strip(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "raw": raw,
                })

        if len(backups) != len(backup_uids):
            raise RuntimeError("BACKUP_FETCH_INCOMPLETE")

        try:
            res_s, _ = imap.select(sent_folder, readonly=True)
        except TypeError:
            res_s, _ = imap.select(sent_folder)
        if res_s != "OK":
            raise RuntimeError("SENT_FOLDER_UNAVAILABLE")

        typ_s, data_s = imap.uid("search", None, "ALL")
        if typ_s != "OK":
            raise RuntimeError("SENT_SEARCH_FAILED")
        sent_raw_uids = data_s[0].split() if data_s and data_s[0] else []
        sent_uids = [u.decode() if isinstance(u, bytes) else str(u) for u in sent_raw_uids]
        clean_sent_mids = set()
        unsent_sent_mids = set()
        for start in range(0, len(sent_uids), 200):
            chunk = sent_uids[start : start + 200]
            typ_f, fetched = imap.uid(
                "fetch",
                ",".join(chunk),
                "(UID BODY.PEEK[HEADER.FIELDS (MESSAGE-ID X-UNSENT)])",
            )
            if typ_f != "OK":
                raise RuntimeError("SENT_FETCH_FAILED")
            for item in (fetched or []):
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                parsed = email_mod.message_from_bytes(item[1] or b"")
                mid = str(parsed.get("Message-ID") or "").strip().lower()
                if not mid:
                    continue
                if "X-Unsent" in parsed and str(parsed.get("X-Unsent") or "").strip() != "":
                    unsent_sent_mids.add(mid)
                else:
                    clean_sent_mids.add(mid)

        for entry in backups:
            mid = entry["message_id"]
            if not mid or mid not in clean_sent_mids or mid in unsent_sent_mids:
                raise RuntimeError(f"SENT_BACKUP_UNVERIFIED:{entry['uid']}:{mid}")

        if arc_path is not None:
            arc_path.mkdir(parents=True, exist_ok=True)
            manifest = []
            for entry in backups:
                eml_path = arc_path / f"{entry['uid']}.eml"
                eml_path.write_bytes(entry["raw"])
                manifest.append({
                    "uid": entry["uid"],
                    "message_id": entry["message_id"],
                    "lead_id": entry["lead_id"],
                    "to": entry["to"],
                    "sha256": entry["sha256"],
                    "file": eml_path.name,
                })
            (arc_path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

        purged = 0
        if apply:
            res_w, _ = imap.select(BACKUP)
            if res_w != "OK":
                raise RuntimeError("BACKUP_WRITE_SELECT_FAILED")
            verified_uids = [entry["uid"] for entry in backups]
            for start in range(0, len(verified_uids), 100):
                del_chunk = ",".join(verified_uids[start : start + 100])
                typ_del, _ = imap.uid("store", del_chunk, "+FLAGS", r"(\Deleted)")
                if typ_del != "OK":
                    raise RuntimeError("BACKUP_STORE_FAILED")
            if hasattr(imap, "expunge"):
                imap.expunge()
            purged = len(verified_uids)

    return {
        "verified_backups": len(backups),
        "purged_backups": purged,
        "applied": apply,
        "archive_dir": str(arc_path) if arc_path else "",
    }


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
    parser.add_argument("--purge-verified-backups", action="store_true")
    parser.add_argument("--archive-dir", default=None)
    args = parser.parse_args()
    if os.environ.get("HSB_CUSTOMER_SEND_ENABLED", "no") == "yes":
        raise RuntimeError("REPAIR_CANNOT_RUN_WITH_SMTP_ENABLED")
    if args.purge_verified_backups:
        owners = list(OWNERS) if args.owner == "ALL" else [args.owner]
        report = {"mode": "purge_apply" if args.apply else "purge_preview", "owners": {},
                  "customer_emails_sent": 0, "checked_at": datetime.now(timezone.utc).isoformat()}
        for owner in owners:
            client = ComMailboxClient(owner, timeout=60)
            arc = Path(args.archive_dir) / owner if args.archive_dir else None
            report["owners"][owner] = purge_verified_backups(client, archive_dir=arc, apply=args.apply)
        print(json.dumps(report, ensure_ascii=False))
        return
    if args.limit < 1 or args.limit > 400:
        raise ValueError("INVALID_REPAIR_BATCH_LIMIT")
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
