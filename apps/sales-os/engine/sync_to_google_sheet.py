#!/usr/bin/env python3
"""
HSB Sales OS - Direkte Synchronisation der 100+100 Drafts in Google Sheet 'ALL_LEADS'.
Single Source of Truth (SSOT).
"""
import json
import re
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO_ROOT = Path(__file__).resolve().parent.parent

# ==============================================================================
# UNVERRÜCKBARE SINGLE SOURCE OF TRUTH (SSOT)
# Master-Sheet ID: 1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg
# Name: HSB CRM MASTER SSOT (EINZIGE WAHRHEIT 6424 LEADS) – 2026
# ==============================================================================
CANONICAL_SPREADSHEET_ID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"
SPREADSHEET_ID = CANONICAL_SPREADSHEET_ID

FORBIDDEN_SPREADSHEET_IDS = {
    "1ITFextI-EuDXNG2p9yfmAvzA_7AbFk4HDO-GqB7WyLI",  # Jordi Alt
    "1FBY9tsDT6ode8QzkSsTQJZxVE81bLZ4DtgDCmojCFoQ",  # Joel Alt
    "1JJ49g_P-gVSAE0eG9zlAJBAjopBoG0Ntb7tThJvrIvs",  # Master v2 Alt
    "1mQCHlJ08BUgyBTk5gSwHfWsS7jvW1FkrcPlo5eHoARk",  # Snapshot vor Sales-Ops
    "1NqAQNuXl3W1OjIQ47ix9ZNYTP0-sLKjVRfeTjXCXR7Q",  # CRM Light Alt
    "1XmbTXyPS5U0tp6PwT5HdF4zE2E3xdrFL9bIvdUtsCD0",  # HSB Sales OS Alt
}

def assert_canonical_sheet(spreadsheet_id: str):
    """Verhindert jeglichen Lese- oder Schreibzugriff auf alte Neben-Sheets."""
    if spreadsheet_id in FORBIDDEN_SPREADSHEET_IDS:
        raise PermissionError(
            f"SSOT SECURITY VIOLATION: Zugriff auf veraltetes/archiviertes Sheet '{spreadsheet_id}' verweigert! "
            f"Einzige kanonische Wahrheit ist Master-Sheet: '{CANONICAL_SPREADSHEET_ID}'."
        )
    if spreadsheet_id != CANONICAL_SPREADSHEET_ID:
        raise ValueError(
            f"UNZULÄSSIGE SPREADSHEET-ID: '{spreadsheet_id}'. Nur das Master-SSOT-Sheet "
            f"'{CANONICAL_SPREADSHEET_ID}' ist für HSB freigegeben."
        )

HSB_PRINCIPAL_RE = re.compile(r'@hsb-boden\.(de|com)$', re.I)
_VERIFIED_PRINCIPALS = {}


def _profile_credentials(profile):
    with open(Path.home() / f'.config/google-workspace-mcp/profiles/{profile}/tokens.json') as f:
        token_data = json.load(f)
    with open(Path.home() / '.config/google-workspace-mcp/credentials.json') as f:
        client_data = json.load(f)
    cinfo = client_data.get('installed') or client_data.get('web')
    return Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=cinfo.get('client_id'),
        client_secret=cinfo.get('client_secret'),
        scopes=token_data.get('scope', '').split()
    )


def assert_hsb_principal(creds, cache_key):
    """Nur HSB-Konten (@hsb-boden.de/.com) dürfen das CRM lesen/schreiben; kein privater Fallback."""
    if cache_key not in _VERIFIED_PRINCIPALS:
        about = build('drive', 'v3', credentials=creds, cache_discovery=False).about().get(fields='user(emailAddress)').execute()
        _VERIFIED_PRINCIPALS[cache_key] = str(about.get('user', {}).get('emailAddress', ''))
    email = _VERIFIED_PRINCIPALS[cache_key]
    if not HSB_PRINCIPAL_RE.search(email):
        raise RuntimeError('CRM_AUTH_NOT_HSB: Google-Konto ist kein HSB-Konto')
    return email


def get_sheets_service(spreadsheet_id: str = CANONICAL_SPREADSHEET_ID):
    """Sheets-Service ausschließlich mit HSB-Identität (Cloud-JSON oder Profil HSB_GOOGLE_PROFILE, Standard 'hsb-boden')."""
    assert_canonical_sheet(spreadsheet_id)
    cloud_auth = os.environ.get('HSB_GOOGLE_AUTHORIZED_USER_JSON', '').strip()
    if cloud_auth:
        creds = Credentials.from_authorized_user_info(json.loads(cloud_auth))
        key = 'cloud'
    else:
        profile = os.environ.get('HSB_GOOGLE_PROFILE', 'hsb-boden').strip()
        creds = _profile_credentials(profile)
        key = f'profile:{profile}'
    assert_hsb_principal(creds, key)
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)

def sync_matrices():
    assert_canonical_sheet(SPREADSHEET_ID)
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
