#!/usr/bin/env python3
"""Klick-Zähler: Token/URL-Erzeugung (Gegenstück zu apps/website/functions/r/[token].ts)
und Abgleich der Cloudflare-KV-Klickereignisse in den CRM-Tab CLICK_EVENTS."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

CLICK_BASE_URL = "https://www.hsb-boden.de/r/"
SEGMENT_CODES = {"architekten": "a", "produktion": "p"}
KV_PREFIX = "click:"
TAB = "CLICK_EVENTS"
HEADER = ["event_id", "at", "lead_id", "class", "reasons"]
LEAD_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_FETCH_PER_RUN = 1000
CF_API = "https://api.cloudflare.com/client/v4"


def click_token(lead_id: str, secret: str) -> str:
    """`<Lead-ID>.<hmac16>`, HMAC-SHA256(secret, lead_id) auf 16 Hex gekürzt."""
    if not LEAD_PATTERN.match(lead_id or ""):
        raise ValueError(f"Ungültige Lead-ID: {lead_id!r}")
    mac = hmac.new(secret.encode("utf-8"), lead_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{lead_id}.{mac[:16]}"


def click_url(lead_id: str, segment: str, secret: Optional[str]) -> str:
    """Mit Secret: Klick-Zähler-URL; ohne Secret: Landingpage-URL ohne Lead-Bezug."""
    if not LEAD_PATTERN.match(lead_id or ""):
        raise ValueError(f"Ungültige Lead-ID: {lead_id!r}")
    if segment not in SEGMENT_CODES:
        raise ValueError(f"Unbekanntes Segment: {segment!r}")
    if not secret:
        from canonical_template_factory import FLYER_LANDING_URL
        return FLYER_LANDING_URL.format(segment=segment)
    return f"{CLICK_BASE_URL}{click_token(lead_id, secret)}?s={SEGMENT_CODES[segment]}"


class CloudflareKV:
    """Minimaler Lesezugriff auf einen KV-Namespace über die Cloudflare-API."""

    def __init__(self, account_id: str, api_token: str, namespace_id: str, opener=urllib.request.urlopen):
        self._base = f"{CF_API}/accounts/{account_id}/storage/kv/namespaces/{namespace_id}"
        self._token = api_token
        self._open = opener

    def _request(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._token}"})
        with self._open(req, timeout=30) as resp:
            return resp.read()

    def list_keys(self, prefix: str) -> List[str]:
        names: List[str] = []
        cursor = ""
        while True:
            query = {"prefix": prefix, "limit": "1000"}
            if cursor:
                query["cursor"] = cursor
            body = json.loads(self._request(f"{self._base}/keys?{urllib.parse.urlencode(query)}"))
            names.extend(item["name"] for item in body.get("result", []))
            cursor = (body.get("result_info") or {}).get("cursor") or ""
            if not cursor:
                return names

    def get(self, key: str) -> Optional[str]:
        try:
            return self._request(f"{self._base}/values/{urllib.parse.quote(key, safe='')}").decode("utf-8")
        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                raise
            return None
        except Exception:
            return None


def kv_client_from_env() -> CloudflareKV:
    names = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "HSB_EMAIL_CLICKS_NAMESPACE_ID")
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError("Fehlende Umgebungsvariablen: " + ", ".join(missing))
    return CloudflareKV(*(os.environ[n] for n in names))


def _lead_from_key(key: str) -> str:
    parts = key.split(":")
    if len(parts) != 3 or parts[1] == "invalid":
        return ""
    return parts[1]


def _event_row(key: str, raw: Optional[str]) -> Optional[List[str]]:
    try:
        value = json.loads(raw or "")
    except ValueError:
        return None
    if not isinstance(value, dict):
        return None
    lead = _lead_from_key(key)
    cls = value.get("class")
    reasons = value.get("reasons") if isinstance(value.get("reasons"), list) else []
    # Nie Bot -> Mensch: nur ein ausdrückliches "human" ohne Gründe an einem gültigen Lead bleibt human.
    if cls != "human" or not lead or reasons:
        cls = "bot"
    return [key, str(value.get("at") or ""), lead, cls, ";".join(str(r) for r in reasons)]


def _tab_exists(svc, spreadsheet_id: str) -> bool:
    meta = svc.spreadsheets().get(
        spreadsheetId=spreadsheet_id, fields="sheets.properties.title"
    ).execute()
    return any(s["properties"]["title"] == TAB for s in meta.get("sheets", []))


def _pad(row: List[Any]) -> List[str]:
    cells = [str(c) for c in row]
    return cells + [""] * (len(HEADER) - len(cells))


def _readback(svc, spreadsheet_id: str, response: Dict[str, Any], sent: List[List[str]]) -> None:
    """Geschriebene Zeilen über updates.updatedRange zurücklesen und vergleichen."""
    updated_range = (response.get("updates") or {}).get("updatedRange")
    if not updated_range:
        raise RuntimeError("CRM_READBACK_MISMATCH")
    back = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=updated_range
    ).execute().get("values", [])
    if [_pad(r) for r in back] != [_pad(r) for r in sent]:
        raise RuntimeError("CRM_READBACK_MISMATCH")


def sync_clicks(
    apply: bool,
    *,
    kv_client=None,
    sheets_svc=None,
    spreadsheet_id: Optional[str] = None,
    max_fetch: int = MAX_FETCH_PER_RUN,
) -> Dict[str, Any]:
    """Neue KV-Klicks in CLICK_EVENTS anhängen, idempotent über event_id (= KV-Key).

    Je Lauf höchstens `max_fetch` KV-Werte (ein GET je Key); der Rest wird als `remaining` gemeldet.
    """
    from hsb_config import CANONICAL_SPREADSHEET_ID
    spreadsheet_id = spreadsheet_id or CANONICAL_SPREADSHEET_ID
    kv = kv_client or kv_client_from_env()
    if sheets_svc is None:
        from sync_to_google_sheet import get_sheets_service
        sheets_svc = get_sheets_service()

    keys = sorted(kv.list_keys(KV_PREFIX))
    tab_exists = _tab_exists(sheets_svc, spreadsheet_id)
    known: set = set()
    if tab_exists:
        head = sheets_svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"{TAB}!A1:E1"
        ).execute().get("values", [])
        if [_pad(r) for r in head] != [HEADER]:
            raise RuntimeError("CLICK_EVENTS_HEADER_MISMATCH")
        res = sheets_svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"{TAB}!A:A"
        ).execute()
        known = {row[0] for row in res.get("values", []) if row}
    new_keys = [k for k in keys if k not in known]
    batch = new_keys[:max_fetch]

    rows: List[List[str]] = []
    skipped = 0
    for key in batch:
        row = _event_row(key, kv.get(key))
        if row is None:
            skipped += 1
        else:
            rows.append(row)
    result = {
        "mode": "apply" if apply else "dry-run",
        "kv_keys": len(keys),
        "already_synced": len(keys) - len(new_keys),
        "new": len(rows),
        "remaining": len(new_keys) - len(batch),
        "skipped_unreadable": skipped,
        "human": sum(1 for r in rows if r[3] == "human"),
        "bot": sum(1 for r in rows if r[3] == "bot"),
        "tab_missing": not tab_exists,
    }
    if not apply:
        return result

    if not tab_exists:
        sheets_svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
        ).execute()
        # Header und erste Zeilen in einem Append, damit kein Tab ohne Header zurückbleibt.
        rows = [HEADER] + rows
    if rows:
        response = sheets_svc.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{TAB}!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
        _readback(sheets_svc, spreadsheet_id, response, rows)
    return result
