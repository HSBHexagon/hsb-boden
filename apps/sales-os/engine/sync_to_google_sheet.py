#!/usr/bin/env python3
"""
HSB Sales OS - Direkte Synchronisation der 100+100 Drafts in Google Sheet 'ALL_LEADS'.
Single Source of Truth.
"""
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO_ROOT = Path(__file__).resolve().parent.parent
SPREADSHEET_ID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"

def get_sheets_service():
    with open('/Users/joelcherinodiaz/.config/google-workspace-mcp/profiles/cherinodiaz/tokens.json') as f:
        token_data = json.load(f)

    with open('/Users/joelcherinodiaz/.config/google-workspace-mcp/credentials.json') as f:
        client_data = json.load(f)

    cinfo = client_data.get('installed') or client_data.get('web')

    creds = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=cinfo.get('client_id'),
        client_secret=cinfo.get('client_secret'),
        scopes=token_data.get('scope', '').split()
    )
    return build('sheets', 'v4', credentials=creds)

def sync_matrices():
    service = get_sheets_service()

    # 1. Joel
    joel_file = REPO_ROOT / "batches" / "matrix_100_JOEL_final.json"
    joel_data = json.loads(joel_file.read_text(encoding="utf-8"))
    joel_range = joel_data["range"]
    joel_matrix = joel_data["matrix"]

    print(f"Schreibe Joel Matrix ({len(joel_matrix)} Zeilen) nach {joel_range}...")
    res_joel = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=joel_range,
        valueInputOption="USER_ENTERED",
        body={"values": joel_matrix}
    ).execute()
    print(f"Joel aktualisiert: {res_joel.get('updatedRows')} Zeilen, {res_joel.get('updatedCells')} Zellen.")

    # 2. Jordi
    jordi_file = REPO_ROOT / "batches" / "matrix_100_JORDI_final.json"
    jordi_data = json.loads(jordi_file.read_text(encoding="utf-8"))
    jordi_range = jordi_data["range"]
    jordi_matrix = jordi_data["matrix"]

    print(f"Schreibe Jordi Matrix ({len(jordi_matrix)} Zeilen) nach {jordi_range}...")
    res_jordi = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=jordi_range,
        valueInputOption="USER_ENTERED",
        body={"values": jordi_matrix}
    ).execute()
    print(f"Jordi aktualisiert: {res_jordi.get('updatedRows')} Zeilen, {res_jordi.get('updatedCells')} Zellen.")

    # 3. Verification Readback
    print("\n--- VERIFIKATIONSLIESUNG ---")
    check_joel = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"ALL_LEADS!AN52:BD151"
    ).execute().get("values", [])

    check_jordi = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"ALL_LEADS!AN3214:BD3313"
    ).execute().get("values", [])

    print(f"Joel Zeilen im Sheet gelesen: {len(check_joel)} (erwartet 100)")
    print(f"Jordi Zeilen im Sheet gelesen: {len(check_jordi)} (erwartet 100)")

    joel_drafted = [r for r in check_joel if len(r) > 7 and r[7] == 'DRAFTED']
    jordi_drafted = [r for r in check_jordi if len(r) > 7 and r[7] == 'DRAFTED']

    print(f"Joel Status DRAFTED: {len(joel_drafted)}/100")
    print(f"Jordi Status DRAFTED: {len(jordi_drafted)}/100")

    if len(joel_drafted) == 100 and len(jordi_drafted) == 100:
        print("\n>>> ERFOLG: 100% aller 200 Zeilen stehen als einzige Wahrheit (Single Source of Truth) im Google Sheet! <<<")
    else:
        print("\n>>> WARNUNG: Unvollständige Einträge im Google Sheet! <<<")

if __name__ == "__main__":
    sync_matrices()
