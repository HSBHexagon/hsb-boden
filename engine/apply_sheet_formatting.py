#!/usr/bin/env python3
"""
HSB Sales OS - Konditionale Formatierung & Visuelles Farb-Leitsystem im Google Sheet:
1. Gesendete E-Mails (Send_Status == 'sent'): Soft-Blau (#e8f0fe / #174ea6) ueber AN:BD
2. Status-Pill Sent (Send_Status == 'sent'): Chip-Blau (#c2e7ff / #001b36)
3. Hot Lead / Kaufinteresse (Reply_Status == 'positive_reply'): Smaragdgruen (#ceead6 / #0d652d)
4. Antwort erhalten (Reply_Status == 'replied'): Soft-Gruen (#e6f4ea / #137333)
5. Abwesenheit / Urlaub (Reply_Status == 'auto_reply_ooo'): Sonnengelb (#fef7e0 / #b06000)
6. Hard Bounce / Unzustellbar (Bounce_Status == 'hard_bounce'): Zartrot (#fce8e6 / #c5221f, durchgestrichen)
7. Soft Bounce / Mailbox voll (Bounce_Status == 'soft_bounce'): Soft-Orange (#feefe3 / #c26401)
8. Opt-Out / DSGVO-Widerspruch (Opt_Out == 'yes'): Flieder (#f3e8fd / #7627bb)
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

def apply_full_formatting():
    service = get_sheets_service()
    
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    all_leads_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == "ALL_LEADS":
            all_leads_id = s["properties"]["sheetId"]
            break
            
    if all_leads_id is None:
        raise RuntimeError("ALL_LEADS Sheet nicht gefunden!")

    print(f"ALL_LEADS Sheet ID: {all_leads_id}")

    # Spalten-Indizes 0-basiert:
    # AN=39, AO=40, AP=41, AQ=42, AR=43, AS=44, AT=45, AU=46, BD=56
    requests = [
        # 1. Zeilenweises Blau fuer versendete Mails ($AO2="sent")
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 39, "endColumnIndex": 56}],
                    "booleanRule": {
                        "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$AO2="sent"'}]},
                        "format": {
                            "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 0.996},
                            "textFormat": {"foregroundColor": {"red": 0.09, "green": 0.31, "blue": 0.65}, "bold": True}
                        }
                    }
                },
                "index": 0
            }
        },
        # 2. Chip-Blau fuer Send_Status (AO)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 40, "endColumnIndex": 41}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "sent"}]},
                        "format": {
                            "backgroundColor": {"red": 0.76, "green": 0.90, "blue": 1.0},
                            "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.11, "blue": 0.21}, "bold": True}
                        }
                    }
                },
                "index": 1
            }
        },
        # 3. Smaragdgruen fuer Hot Leads (Reply_Status = positive_reply)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 43, "endColumnIndex": 44}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "positive_reply"}]},
                        "format": {
                            "backgroundColor": {"red": 0.81, "green": 0.92, "blue": 0.84}, # #ceead6
                            "textFormat": {"foregroundColor": {"red": 0.05, "green": 0.40, "blue": 0.18}, "bold": True}
                        }
                    }
                },
                "index": 2
            }
        },
        # 4. Soft-Gruen fuer Antworten (Reply_Status = replied)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 43, "endColumnIndex": 44}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "replied"}]},
                        "format": {
                            "backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, # #e6f4ea
                            "textFormat": {"foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}, "bold": True}
                        }
                    }
                },
                "index": 3
            }
        },
        # 5. Sonnengelb fuer Abwesenheitsnotiz (Reply_Status = auto_reply_ooo)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 43, "endColumnIndex": 44}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "auto_reply_ooo"}]},
                        "format": {
                            "backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}, # #fef7e0
                            "textFormat": {"foregroundColor": {"red": 0.69, "green": 0.38, "blue": 0.0}, "bold": True}
                        }
                    }
                },
                "index": 4
            }
        },
        # 6. Zartrot & durchgestrichen fuer Hard Bounce (Bounce_Status = hard_bounce)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 42, "endColumnIndex": 43}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "hard_bounce"}]},
                        "format": {
                            "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}, # #fce8e6
                            "textFormat": {"foregroundColor": {"red": 0.77, "green": 0.13, "blue": 0.12}, "bold": True, "strikethrough": True}
                        }
                    }
                },
                "index": 5
            }
        },
        # 7. Soft-Orange fuer Soft Bounce (Bounce_Status = soft_bounce)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 42, "endColumnIndex": 43}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "soft_bounce"}]},
                        "format": {
                            "backgroundColor": {"red": 0.996, "green": 0.937, "blue": 0.890}, # #feefe3
                            "textFormat": {"foregroundColor": {"red": 0.76, "green": 0.39, "blue": 0.0}, "bold": True}
                        }
                    }
                },
                "index": 6
            }
        },
        # 8. Flieder fuer Opt-Out / DSGVO (Opt_Out = yes)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": all_leads_id, "startRowIndex": 1, "endRowIndex": 6500, "startColumnIndex": 45, "endColumnIndex": 46}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "yes"}]},
                        "format": {
                            "backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, # #f3e8fd
                            "textFormat": {"foregroundColor": {"red": 0.46, "green": 0.15, "blue": 0.73}, "bold": True}
                        }
                    }
                },
                "index": 7
            }
        }
    ]

    body = {"requests": requests}
    res = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print("Vollstaendiges Farb-Leitsystem (Blau, Gruen, Gelb, Rot, Orange, Flieder) erfolgreich im Google Sheet eingerichtet!")
    return res

if __name__ == "__main__":
    apply_full_formatting()
