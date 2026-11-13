"""Batched IMAP UID helper for purging already-sent drafts."""
from __future__ import annotations

import email
from email.utils import getaddresses
import re

PURGE_BATCH_SIZE = 200
_UID_RE = re.compile(rb"\bUID (\d+)\b")


def _normalize_set(values) -> set[str]:
    return {str(v).strip().lower() for v in (values or ()) if v is not None and str(v).strip()}


def collect_sent_identities(imap, sent_folder: str, batch_size: int = PURGE_BATCH_SIZE) -> tuple[set[str], set[str], set[str]]:
    """Scan sent_folder and return sets of (recipients, lead_ids, message_ids)."""
    try:
        res, _ = imap.select(sent_folder, readonly=True)
    except TypeError:
        res, _ = imap.select(sent_folder)
    if res != "OK":
        raise RuntimeError(f"SENT_FOLDER_UNAVAILABLE: {sent_folder}")
    typ, data = imap.uid("search", None, "ALL")
    if typ != "OK":
        raise RuntimeError("SENT_SEARCH_FAILED")
    raw_uids = data[0].split() if data and data[0] else []
    uids = [u if isinstance(u, bytes) else str(u).encode() for u in raw_uids]
    sent_emails: set[str] = set()
    sent_lead_ids: set[str] = set()
    sent_mids: set[str] = set()
    if not uids:
        return sent_emails, sent_lead_ids, sent_mids

    for start in range(0, len(uids), batch_size):
        chunk = uids[start : start + batch_size]
        typ_f, fetched = imap.uid("fetch", b",".join(chunk), "(UID BODY.PEEK[HEADER.FIELDS (TO MESSAGE-ID X-HSB-LEAD-ID)])")
        if typ_f != "OK":
            raise RuntimeError("SENT_FETCH_FAILED")
        for item in fetched or []:
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            parsed = email.message_from_bytes(item[1] or b"")
            for _, addr in getaddresses(parsed.get_all("To", [])):
                if addr and addr.strip():
                    sent_emails.add(addr.strip().lower())
            lid = parsed.get("X-HSB-Lead-ID", "").strip().lower()
            if lid:
                sent_lead_ids.add(lid)
            mid = parsed.get("Message-ID", "").strip().lower()
            if mid:
                sent_mids.add(mid)
    return sent_emails, sent_lead_ids, sent_mids


def purge_owner_sent_drafts(
    imap,
    drafts_folder: str,
    sent_emails: set[str],
    *,
    sent_lead_ids: set[str] | None = None,
    sent_message_ids: set[str] | None = None,
    apply: bool = False,
    batch_size: int = PURGE_BATCH_SIZE,
) -> int:
    """Count and optionally delete drafts whose recipient, Lead-ID or Message-ID is already sent."""
    res, _ = imap.select(drafts_folder)
    if res != "OK":
        raise RuntimeError("PURGE_FOLDER_UNAVAILABLE")

    typ, data = imap.uid("search", None, "ALL")
    if typ != "OK":
        raise RuntimeError("PURGE_SEARCH_FAILED")

    raw_uids = data[0].split() if data and data[0] else []
    uids = [u if isinstance(u, bytes) else str(u).encode() for u in raw_uids]
    if not uids:
        return 0

    email_targets = _normalize_set(sent_emails)
    lead_ids = _normalize_set(sent_lead_ids)
    mids = _normalize_set(sent_message_ids)
    to_delete: list[bytes] = []
    for start in range(0, len(uids), batch_size):
        chunk = uids[start : start + batch_size]
        typ_f, fetched = imap.uid("fetch", b",".join(chunk), "(UID BODY.PEEK[HEADER.FIELDS (TO MESSAGE-ID X-HSB-LEAD-ID)])")
        if typ_f != "OK":
            raise RuntimeError("PURGE_FETCH_FAILED")

        seen_uids: set[bytes] = set()
        items = fetched or []
        for idx, item in enumerate(items):
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            uid_match = _UID_RE.search(item[0])
            if not uid_match and idx + 1 < len(items) and isinstance(items[idx + 1], bytes):
                uid_match = _UID_RE.search(items[idx + 1])
            if not uid_match:
                raise RuntimeError("PURGE_UID_MISSING")

            uid_bytes = uid_match.group(1)
            seen_uids.add(uid_bytes)
            parsed = email.message_from_bytes(item[1] or b"")
            recipients = {
                addr.strip().lower()
                for _, addr in getaddresses(parsed.get_all("To", []))
                if addr and addr.strip()
            }
            lead_id = parsed.get("X-HSB-Lead-ID", "").strip().lower()
            msg_id = parsed.get("Message-ID", "").strip().lower()

            matched = False
            if recipients & email_targets:
                matched = True
            elif lead_id and lead_id in lead_ids:
                matched = True
            elif msg_id and msg_id in mids:
                matched = True

            if matched:
                to_delete.append(uid_bytes)

        if seen_uids != set(chunk):
            raise RuntimeError("PURGE_FETCH_INCOMPLETE")

    if apply and to_delete:
        for start in range(0, len(to_delete), batch_size):
            del_chunk = to_delete[start : start + batch_size]
            typ_s, _ = imap.uid("store", b",".join(del_chunk), "+FLAGS", r"(\Deleted)")
            if typ_s != "OK":
                raise RuntimeError("PURGE_STORE_FAILED")
        if hasattr(imap, "expunge"):
            imap.expunge()

    return len(to_delete)
