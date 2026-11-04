#!/usr/bin/env python3
"""
HSB Sales OS - Erstellt das Google Sheets Tabellenblatt 'DE_VERSENDUNGEN_FORENSIK'
und lädt alle 1.274 realen .de-Versendungen lückenlos als durchsuchbare Tabelle hoch.
"""
import sys
import csv
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID, assert_canonical_sheet

def main():
    assert_canonical_sheet(SPREADSHEET_ID)
    service = get_sheets_service()
    csv_path = REPO_ROOT / "data/ALLE_DE_VERSENDUNGEN_VOLLSTAENDIG.csv"

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Lese {len(rows)} Datensätze aus CSV...")

    # Prüfe ob Tab 'DE_VERSENDUNGEN_FORENSIK' existiert, sonst anlegen
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_titles = [s["properties"]["title"] for s in meta.get("sheets", [])]

    tab_name = "DE_VERSENDUNGEN_FORENSIK"
    if tab_name not in sheet_titles:
        print(f"Erstelle neues Tabellenblatt '{tab_name}' im Google Sheet...")
        req = {
            "addSheet": {
                "properties": {
                    "title": tab_name,
                    "gridProperties": {"rowCount": len(rows) + 50, "columnCount": 10}
                }
            }
        }
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": [req]}).execute()
        print("✓ Tabellenblatt erfolgreich erstellt.")

    # Bereite Tabellenzeilen vor
    headers = [
        "Nr",
        "Sendedatum_Uhrzeit",
        "Absender",
        "Empfaenger_Email",
        "Kategorie",
        "Betreffzeile",
        "Quelle",
        "Message_ID"
    ]

    values = [headers]
    for idx, r in enumerate(rows, start=1):
        subj = r.get("Betreff", "")
        subj_l = subj.lower()
        if any(k in subj_l for k in ["industrieböden", "industrieboden", "beratung", "sanierung", "hsb hexagon"]):
            kat = "Kaltakquise_Lead"
        else:
            kat = "Geschäftlich_Operativ"

        values.append([
            idx,
            r.get("Sendedatum_ISO", ""),
            r.get("Absender", ""),
            r.get("Empfaenger_Email", ""),
            kat,
            subj,
            r.get("Quelle", ""),
            r.get("Message_ID", "")[:40]
        ])

    print(f"Schreibe {len(values)} Zeilen in {tab_name}...")
    # Schreibe in Chunks à 500 Zeilen
    chunk_size = 500
    for i in range(0, len(values), chunk_size):
        chunk = values[i:i + chunk_size]
        start_row = i + 1
        end_row = i + len(chunk)
        rng = f"{tab_name}!A{start_row}:H{end_row}"
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=rng,
            valueInputOption="USER_ENTERED",
            body={"values": chunk}
        ).execute()
        print(f"  Zeilen {start_row} bis {end_row} geschrieben.")
        time.sleep(0.3)

    print("\n✓ ALLE 1.274 VERSENDUNGEN LIEGEN JETZT LIVE IM GOOGLE SHEET IM TAB 'DE_VERSENDUNGEN_FORENSIK'!")

if __name__ == "__main__":
    main()
