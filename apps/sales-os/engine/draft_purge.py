"""Batched IMAP UID helper for purging already-sent drafts."""
from __future__ import annotations

import email
from email.utils import getaddresses
import re

PURGE_BATCH_SIZE = 200
_UID_RE = re.compile(rb"\bUID (\d+)\b")


def purge_owner_sent_drafts(
    imap,
    drafts_folder: str,
    sent_emails: set[str],
    *,
    apply: bool = False,
    batch_size: int = PURGE_BATCH_SIZE,
) -> int:
    """Count and optionally delete drafts whose To address is already marked sent."""
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

    to_delete: list[bytes] = []
    for start in range(0, len(uids), batch_size):
        chunk = uids[start : start + batch_size]
        typ_f, fetched = imap.uid("fetch", b",".join(chunk), "(UID BODY.PEEK[HEADER.FIELDS (TO)])")
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
            if recipients & sent_emails:
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
