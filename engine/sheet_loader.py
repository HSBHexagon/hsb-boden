"""
HSB Sales OS - Laden der Leads aus dem Sheet-Snapshot.

Das Google Sheet bleibt System of Record. Fuer lokale Laeufe (EML-Fallback,
Tests, Reports) arbeiten wir auf einem XLSX/CSV-Export, damit keine 6.424
Zeilen durch API-Aufrufe geschleift werden muessen.
"""
from __future__ import annotations

import csv
from pathlib import Path

from hsb_core import ADDITIONAL_FIELDS, FIELD_MAP, REPO_ROOT

DATA_DIR = REPO_ROOT / "data"
SPREADSHEET_ID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"
SHEET_NAME = "HSB CRM MASTER 6424 - Sales OS"


def _map_row(header: list[str], row: tuple) -> dict:
    raw = {h: (row[i] if i < len(row) else None) for i, h in enumerate(header)}
    lead = {}
    for logical, sheet_col in FIELD_MAP.items():
        lead[logical] = raw.get(sheet_col)
    for extra in ADDITIONAL_FIELDS:
        lead[extra] = raw.get(extra)
    lead["_raw"] = raw
    return lead


def load_from_xlsx(path: str | Path | None = None,
                   tab: str = "ALL_LEADS") -> list[dict]:
    import openpyxl

    path = Path(path) if path else _newest_xlsx()
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[tab]
    rows = ws.iter_rows(values_only=True)
    header = [str(h) if h is not None else "" for h in next(rows)]
    out = []
    for row in rows:
        if row is None or not any(row):
            continue
        out.append(_map_row(header, row))
    wb.close()
    return out


def load_from_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        return [_map_row(header, tuple(r)) for r in reader if any(r)]


def _newest_xlsx() -> Path:
    files = sorted(DATA_DIR.glob("*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(
            f"Kein Sheet-Export in {DATA_DIR}. "
            "Export via Google-Workspace-MCP (export_file, Format xlsx).")
    return files[-1]


def summarize(leads: list[dict]) -> dict:
    """Kennzahlen fuer das Cockpit - ohne die Daten selbst auszugeben."""
    from collections import Counter
    from hsb_core import check_eligibility, normalize_owner

    per_owner: dict[str, Counter] = {}
    reasons: Counter = Counter()
    for lead in leads:
        owner = normalize_owner(lead.get("Owner")) or "UNBEKANNT"
        c = per_owner.setdefault(owner, Counter())
        c["total"] += 1
        r = check_eligibility(lead)
        c["eligible" if r.eligible else "blocked"] += 1
        for reason in r.reasons:
            reasons[reason.split("(")[0].strip()] += 1
    return {
        "total": len(leads),
        "per_owner": {k: dict(v) for k, v in per_owner.items()},
        "top_block_reasons": dict(reasons.most_common(10)),
    }
