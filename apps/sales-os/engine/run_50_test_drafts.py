#!/usr/bin/env python3
"""
HSB Sales OS - Erzeugt 50 Test-Entwuerfe ueber den echten Power-Automate-Adapter.

Sicherheit:
  - Es werden ausschliesslich Entwuerfe angelegt (DraftEmail).
  - REAL_EXTERNAL_SEND_COUNT = 0 (kein Versand).
"""
import argparse
import base64
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from hsb_core import FLYERS
from sheet_loader import load_from_xlsx

from hsb_config import (
    FC_CLIENT_ID,
    FC_TENANT_ID,
    FC_SCOPE,
    get_joel_url,
    get_jordi_connector_url,
    get_fc_refresh_token,
)

JOEL_URL = get_joel_url()
JORDI_CONNECTOR_URL = get_jordi_connector_url()

def get_jordi_token() -> str:
    refresh_token = get_fc_refresh_token()

    token_url = f"https://login.microsoftonline.com/{FC_TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": FC_CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": FC_SCOPE
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
        return tokens["access_token"]

def create_draft(owner: str, lead: dict, recipient: str, flyer_b64: str, flyer_name: str, access_token: str = None) -> dict:
    subject = f"HSB Hexagon Säurebau GmbH · Industrieböden ({lead.get('Firma') or lead.get('Lead_ID')})"
    body_html = f"<p>Guten Tag,<br><br>anbei finden Sie Informationen zu unseren Industrieböden und Säurebau-Lösungen.<br><br>Mit freundlichen Grüßen,<br><b>{owner}</b></p>"
    payload = {
        "leadId": lead.get("Lead_ID"),
        "batchId": "BATCH-50-TEST",
        "owner": owner,
        "to": recipient,
        "subject": subject,
        "bodyHtml": body_html,
        "attachmentName": flyer_name,
        "attachmentContentBytes": flyer_b64
    }
    data = json.dumps(payload).encode("utf-8")

    if owner == "JOEL":
        req = urllib.request.Request(JOEL_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode("utf-8"))
    else:
        req = urllib.request.Request(JORDI_CONNECTOR_URL, data=data, headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }, method="POST")
        with urllib.request.urlopen(req, timeout=45) as r:
            run_id = r.headers.get("x-ms-workflow-run-id")
            return {"status": "ACCEPTED_ASYNC", "runId": run_id, "code": r.getcode()}

def main():
    parser = argparse.ArgumentParser(description="Erzeugt 50 Test-Entwuerfe")
    parser.add_argument("--owner", choices=["JORDI", "JOEL"], default="JORDI", help="Owner: JORDI oder JOEL")
    parser.add_argument("--count", type=int, default=50, help="Anzahl Entwuerfe (Default: 50)")
    parser.add_argument("--recipient", default="", help="Zieladresse (Leer = echte Leads aus Datei)")
    args = parser.parse_args()

    print(f"=== STARTE TEST: {args.count} ENTWÜRFE FÜR {args.owner} ===")
    flyer = FLYERS[args.owner]
    flyer_bytes = flyer.path.read_bytes()
    flyer_b64 = base64.b64encode(flyer_bytes).decode("ascii")
    print(f"Anlage: {flyer.attachment_name} ({len(flyer_bytes)} Bytes, Hash: {flyer.sha256[:12]}...)")

    access_token = None
    if args.owner == "JORDI":
        print("Hole frisches MSAL-Token fuer Jordi...")
        access_token = get_jordi_token()
        print("Token erhalten.")

    leads = load_from_xlsx()
    owner_str = "Jordi Post" if args.owner == "JORDI" else "Joel Cherino Diaz"
    filtered_leads = [l for l in leads if l.get("Owner") == owner_str][:args.count]
    print(f"{len(filtered_leads)} Leads ausgewaehlt.")

    success = 0
    failed = 0

    for i, lead in enumerate(filtered_leads, start=1):
        to_addr = args.recipient if args.recipient else (lead.get("Email") or "info@example.com")
        print(f"[{i}/{len(filtered_leads)}] Erzeuge Entwurf fuer {lead.get('Lead_ID')} an {to_addr} ...", end="", flush=True)
        try:
            res = create_draft(args.owner, lead, to_addr, flyer_b64, flyer.attachment_name, access_token)
            if args.owner == "JOEL":
                print(f" OK (DraftID: {res.get('draftId')[:20]}..., Anhang: {res.get('attachmentSize')} B)")
            else:
                print(f" OK (Lauf: {res.get('runId')})")
            success += 1
        except Exception as e:
            print(f" FEHLER: {e}")
            failed += 1
        time.sleep(0.5)

    print(f"\n=== FERTIG: {success} erfolgreich angelegt, {failed} fehlgeschlagen ===")

if __name__ == "__main__":
    main()
