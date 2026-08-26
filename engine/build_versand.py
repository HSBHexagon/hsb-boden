#!/usr/bin/env python3
"""
Baut die Zeilen fuer das Sheet-Blatt VERSAND.

VERSAND ist die eine Tabelle, die im Alltag geoeffnet wird: pro Kontakt eine
Zeile, chronologisch nach Batch. Sie ersetzt das Durchsuchen der uebrigen
Blaetter, ohne sie zu loeschen.

Wichtig zur Ehrlichkeit der Daten: "Versendet am" kann das System nicht
messen. Gesendet wird von Hand in Outlook; es gibt auf dem Prospekt-Pfad
systemweit keine Send-Aktion. Die Spalte ist deshalb eine Bestaetigung, die
der Bearbeiter setzt - kein Messwert.

    python3 engine/build_versand.py > /tmp/versand.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_engine import Batch, BatchStats, render_email
from hsb_core import FLYERS, normalize_owner
from sheet_loader import load_from_xlsx

KOPF = ["Nr", "Batch", "Firma", "Ansprechpartner", "E-Mail", "Betreff",
        "Absender", "Entwurf erstellt", "Versendet am", "Antwort",
        "Notiz", "Lead-ID"]


def _batch_huelle(owner_key: str) -> Batch:
    """Minimale Huelle, damit render_email den korrekten Absender einsetzt."""
    f = FLYERS[owner_key]
    return Batch(batch_id="", owner_key=owner_key, owner_display=f.display_name,
                 mailbox=f.mailbox, campaign="", created_at="",
                 asset_filename=f.path.name, asset_drive_id=f.drive_id,
                 asset_sha256=f.sha256, status="", stats=BatchStats())


def zeilen(xlsx: str | None = None) -> list[list[str]]:
    leads = [l for l in load_from_xlsx(xlsx)
             if str(l.get("Batch_ID") or "").strip()]
    leads.sort(key=lambda l: (str(l.get("Batch_ID")), str(l.get("Lead_ID"))))

    huellen: dict[str, Batch] = {}
    out: list[list[str]] = []
    for i, lead in enumerate(leads, 1):
        ok = normalize_owner(lead.get("Owner"))
        if ok not in huellen:
            huellen[ok] = _batch_huelle(ok)
        b = huellen[ok]
        betreff, _ = render_email(lead, b)
        gesendet = str(lead.get("Sent_At") or "").strip()
        antwort = str(lead.get("Reply_Status") or "").strip()
        out.append([
            str(i),
            str(lead.get("Batch_ID") or ""),
            str(lead.get("Company") or ""),
            str(lead.get("Contact") or ""),
            str(lead.get("Email") or ""),
            betreff,
            f"{b.owner_display} <{b.mailbox}>",
            str(lead.get("Drafted_At") or ""),
            gesendet,
            antwort if antwort.lower() not in {"none", "unknown"} else "",
            str(lead.get("Notes") or ""),
            str(lead.get("Lead_ID") or ""),
        ])
    return out


if __name__ == "__main__":
    daten = zeilen(sys.argv[1] if len(sys.argv) > 1 else None)
    json.dump([KOPF] + daten, sys.stdout, ensure_ascii=False)
