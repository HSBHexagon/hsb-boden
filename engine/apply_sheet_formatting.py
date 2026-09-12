#!/usr/bin/env python3
"""
HSB Sales OS - Konditionale Formatierung im Google Sheet:
- Gesendete E-Mails (Send_Status == 'sent') werden BLAU hervorgehoben (Zeilen AN:BD).
- Antworten (Reply_Status == 'replied') werden GRUEN hervorgehoben.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

def apply_blue_formatting():
    service = get_sheets_service()
    
    # Hole Sheet-Metadaten fuer Sheet-ID von ALL_LEADS
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    all_leads_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == "ALL_LEADS":
            all_leads_id = s["properties"]["sheetId"]
            break
            
    if all_leads_id is None:
        raise RuntimeError("ALL_LEADS Sheet nicht gefunden!")

    print(f"ALL_LEADS Sheet ID: {all_leads_id}")

    # Loesche alte Regeln und erstelle neue konditionale Formatierung
    # AN ist Spalte 40 (0-basiert: 39), BD ist Spalte 56 (0-basiert: 56)
    # AO ist Spalte 41 (0-basiert: 40)
    requests = [
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": all_leads_id,
                        "startRowIndex": 1,
                        "endRowIndex": 6500,
                        "startColumnIndex": 39,
                        "endColumnIndex": 56
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=$AO2="sent"'}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 0.996}, # #e8f0fe Soft Blue
                            "textFormat": {
                                "foregroundColor": {"red": 0.09, "green": 0.31, "blue": 0.65}, # #174ea6 Deep Blue
                                "bold": True
                            }
                        }
                    }
                },
                "index": 0
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": all_leads_id,
                        "startRowIndex": 1,
                        "endRowIndex": 6500,
                        "startColumnIndex": 40,
                        "endColumnIndex": 41
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "TEXT_EQ",
                            "values": [{"userEnteredValue": "sent"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.76, "green": 0.90, "blue": 1.0}, # #c2e7ff Pill Blue
                            "textFormat": {
                                "foregroundColor": {"red": 0.0, "green": 0.11, "blue": 0.21}, # Dark Blue
                                "bold": True
                            }
                        }
                    }
                },
                "index": 1
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": all_leads_id,
                        "startRowIndex": 1,
                        "endRowIndex": 6500,
                        "startColumnIndex": 44,
                        "endColumnIndex": 45
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "TEXT_EQ",
                            "values": [{"userEnteredValue": "replied"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.88}, # Soft Green
                            "textFormat": {
                                "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}, # Deep Green
                                "bold": True
                            }
                        }
                    }
                },
                "index": 2
            }
        }
    ]

    body = {"requests": requests}
    res = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print("Konditionale Formatierung (Blau für gesendet, Grün für Antwort) erfolgreich im Google Sheet eingerichtet!")
    return res

if __name__ == "__main__":
    apply_blue_formatting()
