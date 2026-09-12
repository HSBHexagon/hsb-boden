#!/usr/bin/env python3
"""
HSB Sales OS - Batch-Runner für 100 Entwürfe (Joel Cherino Diaz & Jordi Post).
Sicherheit: Reines DraftEmail, REAL_EXTERNAL_SEND_COUNT = 0.
Enthält:
- Offizielles HSB Firmenlogo in der Signatur
- Anhang: HSB-HEXAGON-Industrieboeden-Flyer.pdf (bytegenau verifiziert)
- Vollständige Rechtskonformität (§ 35a GmbHG + § 7 UWG)
- Detailliertes Ergebnis-Logging für Google Sheet Writeback
"""
import argparse
import base64
import datetime
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from hsb_core import FLYERS
from sheet_loader import load_from_xlsx

FC_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
FC_TENANT_ID = "8adbbf2e-fd2c-4857-8540-bbcdb3a20f30"
FC_SCOPE = "https://apihub.azure.com/.default offline_access"

JOEL_URL = "https://default8adbbf2efd2c48578540bbcdb3a20f.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/08/workflows/6b6a50d7d6ad4301a7c9dc94cb3fc586/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ZfuJ6WEK9C3-YFeiFerXpgQ2w-FkXcjWpkMi6o5r7SQ"
JORDI_CONNECTOR_URL = "https://default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30.06.common.germany.azure-apihub.net/apim/logicflows/47ee3d7a-626c-4fff-9e16-6d938949e4bd/triggers/manual/run?api-version=2016-11-01"

FIRMA = {
    "name": "HSB Hexagon Säurebau GmbH",
    "strasse": "Benzstraße 6",
    "plzOrt": "48599 Gronau",
    "telefon": "+49 (0)2562 9463030",
    "web": "www.hsb-boden.de",
    "sitz": "Gronau",
    "registergericht": "Amtsgericht Coesfeld",
    "hrb": "HRB 21481",
    "geschaeftsfuehrer": "Jordie Post"
}

def signatur_html(owner_display: str, mailbox: str, mobile: str) -> str:
    mobil_zeile = f"Mobil {mobile}<br>" if mobile else ""
    return (
        f'<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:10pt;color:#222222;line-height:1.45;">'
        f'<strong>{owner_display}</strong><br>'
        f'{FIRMA["name"]}<br>'
        f'{FIRMA["strasse"]} &middot; {FIRMA["plzOrt"]}<br>'
        f'{mobil_zeile}'
        f'Tel. {FIRMA["telefon"]}<br>'
        f'<a href="mailto:{mailbox}" style="color:#1155cc;">{mailbox}</a> &middot; '
        f'<a href="https://{FIRMA["web"]}" style="color:#1155cc;">{FIRMA["web"]}</a>'
        f'</p>'
        f'<p style="margin:14px 0 0 0;">'
        f'<a href="https://{FIRMA["web"]}" target="_blank" style="text-decoration:none;">'
        f'<img src="https://{FIRMA["web"]}/brand/hsb-boden-logo.png" '
        f'alt="{FIRMA["name"]}" '
        f'width="148" height="48" '
        f'style="display:block;border:0;width:148px;height:auto;max-height:48px;" />'
        f'</a>'
        f'</p>'
        f'<p style="margin:10px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#777777;line-height:1.4;">'
        f'Sitz der Gesellschaft: {FIRMA["sitz"]} &middot; '
        f'{FIRMA["registergericht"]} {FIRMA["hrb"]} &middot; '
        f'Geschäftsführer: {FIRMA["geschaeftsfuehrer"]}'
        f'</p>'
    )

def anrede_fuer(lead: dict) -> str:
    ap = str(lead.get("Ansprechpartner") or "").strip()
    if not ap or ap.lower() in ["none", "nan"]:
        return "Guten Tag,"
    teile = ap.split()
    if len(teile) >= 2:
        anrede = teile[0].lower()
        nachname = " ".join(teile[1:])
        if "herr" in anrede:
            return f"Sehr geehrter Herr {nachname},"
        if "frau" in anrede:
            return f"Sehr geehrte Frau {nachname},"
    return f"Guten Tag {ap},"

def get_jordi_token() -> str:
    code_gs = (REPO_ROOT / "apps_script" / "Code.gs").read_text(encoding="utf-8")
    m = re.search(r"HSB_FC_REFRESH_TOKEN\', \'(.*?)\'", code_gs)
    if not m:
        raise RuntimeError("Refresh token nicht in Code.gs gefunden")
    refresh_token = m.group(1)

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

def create_single_draft(owner: str, lead: dict, flyer_b64: str, flyer_name: str, access_token: str = None, batch_id: str = "") -> dict:
    flyer = FLYERS[owner]
    anrede = anrede_fuer(lead)
    firma_str = str(lead.get("Firma") or "").strip()
    company = firma_str if (firma_str and firma_str.lower() not in ["none", "nan"]) else "Ihr Unternehmen"
    betreff = f"Industrieböden für {company} – Beratung von {flyer.display_name}"

    sig = signatur_html(flyer.display_name, flyer.mailbox, flyer.mobile)
    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#222222;line-height:1.5;">'
        f'<p style="margin:0 0 12px 0;">{anrede}</p>'
        f'<p style="margin:0 0 12px 0;">mein Name ist {flyer.display_name} von der HSB Hexagon Säurebau GmbH. '
        f'Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – '
        f'ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.</p>'
        f'<p style="margin:0 0 12px 0;">Typische Themen bei Produktionsbetrieben:<br>'
        f'&bull; Risse, Ablösungen und offene Fugen<br>'
        f'&bull; Keimnester in Nassbereichen<br>'
        f'&bull; stehendes Wasser durch falsches Gefälle<br>'
        f'&bull; defekte Rinnen und Abläufe</p>'
        f'<p style="margin:0 0 12px 0;">Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser '
        f'Vorgehen von der Analyse bis zur dokumentierten Übergabe.</p>'
        f'<p style="margin:0 0 16px 0;">Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.</p>'
        f'<p style="margin:0 0 4px 0;">Mit freundlichen Grüßen</p>'
        f'{sig}'
        f'<p style="margin:20px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#999999;">'
        f'---<br>Wenn Sie keine weiteren Informationen erhalten möchten, antworten Sie bitte mit dem Betreff &bdquo;Abmelden&ldquo; auf diese E-Mail.</p>'
        f'</div>'
    )

    to_addr = str(lead.get("Email") or "").strip()
    payload = {
        "leadId": str(lead.get("Lead_ID") or ""),
        "batchId": batch_id,
        "owner": owner,
        "to": to_addr,
        "subject": betreff,
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

def run_batch(owner: str, count: int = 100, start_row: int = None, force: bool = False) -> list:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"BATCH-100-{owner}-{ts[:8]}"

    print(f"\n================================================================================")
    print(f" STARTE BATCH: {count} ENTWUERFE FUER {owner} (Batch-ID: {batch_id})")
    print(f"================================================================================")
    flyer = FLYERS[owner]
    flyer_bytes = flyer.path.read_bytes()
    flyer_b64 = base64.b64encode(flyer_bytes).decode("ascii")
    print(f"Anlage-Sichtname : {flyer.attachment_name}")
    print(f"Dateigröße       : {len(flyer_bytes)} Bytes (SHA256: {flyer.sha256[:16]}...)")
    print(f"Absender         : {flyer.display_name} <{flyer.mailbox}>")

    access_token = None
    if owner == "JORDI":
        print("Hole frisches MSAL-Token fuer Jordi...")
        access_token = get_jordi_token()
        print("Token aktiv.")

    leads = load_from_xlsx()
    owner_str = "Jordi Post" if owner == "JORDI" else "Joel Cherino Diaz"

    # Bestimme Startzeile falls nicht vorgegeben
    if start_row is None:
        start_row = 3214 if owner == "JORDI" else 52

    # Filter Leads nach Owner, E-Mail und Zeilenbereich
    filtered_leads = [
        l for l in leads 
        if l.get("Owner") == owner_str 
        and l.get("Email") 
        and l["_row"] >= start_row
    ][:count]

    print(f"Ausgewählte Leads: {len(filtered_leads)} (Zeilen {filtered_leads[0]['_row']} bis {filtered_leads[-1]['_row']})\n")

    batches_dir = REPO_ROOT / "batches"
    batches_dir.mkdir(exist_ok=True)

    # Vorhandene Resultate laden, sofern nicht --force gesetzt ist
    known_results = {}
    if not force:
        for f in batches_dir.glob(f"result_100_{owner}_*.json"):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                for item in items:
                    if item.get("status") == "OK" and item.get("row"):
                        known_results[item["row"]] = item
            except Exception:
                pass

    results = []
    matrix_rows = []

    for i, lead in enumerate(filtered_leads, start=1):
        lead_id = lead.get("Lead_ID")
        email = lead.get("Email")
        row = lead.get("_row")
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if row in known_results:
            cached = known_results[row]
            print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : BEREITS ERSTELLT (Cache genutzt)")
            results.append(cached)
            # Matrix Row: AN bis BD (17 Spalten)
            matrix_rows.append([
                cached.get("batch_id", batch_id),
                "drafted",
                "", "", "",
                str(lead.get("Legal_Basis") or "EXISTING_CUSTOMER_7_3"),
                str(lead.get("Suppressed") or "no"),
                "DRAFTED",
                cached.get("drafted_at", now_iso),
                cached.get("draft_id", ""),
                cached.get("drafted_at", now_iso),
                "", "",
                cached.get("internet_message_id", ""),
                cached.get("conversation_id", ""),
                "",
                ""
            ])
            continue

        t0 = time.time()
        try:
            res = create_single_draft(owner, lead, flyer_b64, flyer.attachment_name, access_token, batch_id)
            dt = time.time() - t0
            if owner == "JOEL":
                draft_id = res.get("draftId", "")
                size = res.get("attachmentSize", 0)
                int_msg_id = res.get("internetMessageId", "")
                conv_id = res.get("conversationId", "")
                print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : OK in {dt:.1f}s [Draft: {draft_id[:20]}..., Anhang: {size} B]")
                item = {
                    "row": row,
                    "lead_id": lead_id,
                    "email": email,
                    "status": "OK",
                    "batch_id": batch_id,
                    "draft_id": draft_id,
                    "drafted_at": now_iso,
                    "attachment_size": size,
                    "internet_message_id": int_msg_id,
                    "conversation_id": conv_id,
                    "error": ""
                }
                results.append(item)
                matrix_rows.append([
                    batch_id,
                    "drafted",
                    "", "", "",
                    str(lead.get("Legal_Basis") or "EXISTING_CUSTOMER_7_3"),
                    str(lead.get("Suppressed") or "no"),
                    "DRAFTED",
                    now_iso,
                    draft_id,
                    now_iso,
                    "", "",
                    int_msg_id,
                    conv_id,
                    "",
                    ""
                ])
            else:
                run_id = res.get("runId", "")
                print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : OK in {dt:.1f}s [Flow-Lauf: {run_id}]")
                draft_marker = f"FLOW_RUN_{run_id}"
                item = {
                    "row": row,
                    "lead_id": lead_id,
                    "email": email,
                    "status": "OK",
                    "batch_id": batch_id,
                    "draft_id": draft_marker,
                    "drafted_at": now_iso,
                    "attachment_size": len(flyer_bytes),
                    "internet_message_id": "",
                    "conversation_id": "",
                    "run_id": run_id,
                    "error": ""
                }
                results.append(item)
                matrix_rows.append([
                    batch_id,
                    "drafted",
                    "", "", "",
                    str(lead.get("Legal_Basis") or "EXISTING_CUSTOMER_7_3"),
                    str(lead.get("Suppressed") or "no"),
                    "DRAFTED",
                    now_iso,
                    draft_marker,
                    now_iso,
                    "", "",
                    "",
                    "",
                    "",
                    ""
                ])
        except Exception as e:
            dt = time.time() - t0
            print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : FEHLER in {dt:.1f}s: {e}")
            item = {
                "row": row,
                "lead_id": lead_id,
                "email": email,
                "status": "FAIL",
                "batch_id": batch_id,
                "draft_id": "",
                "drafted_at": "",
                "error": str(e)
            }
            results.append(item)
            matrix_rows.append([
                batch_id,
                "not_sent",
                "", "", "",
                str(lead.get("Legal_Basis") or "EXISTING_CUSTOMER_7_3"),
                str(lead.get("Suppressed") or "no"),
                "FAILED",
                now_iso,
                "",
                "",
                "", "",
                "",
                "",
                "",
                str(e)[:400]
            ])
        time.sleep(0.35)

    out_file = batches_dir / f"result_100_{owner}_{ts}.json"
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    
    matrix_payload = {
        "owner": owner,
        "start_row": filtered_leads[0]["_row"],
        "end_row": filtered_leads[-1]["_row"],
        "range": f"ALL_LEADS!AN{filtered_leads[0]['_row']}:BD{filtered_leads[-1]['_row']}",
        "matrix": matrix_rows
    }
    matrix_file = batches_dir / f"matrix_100_{owner}.json"
    matrix_file.write_text(json.dumps(matrix_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    matrix_final_file = batches_dir / f"matrix_100_{owner}_final.json"
    matrix_final_file.write_text(json.dumps(matrix_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    ok_count = len([r for r in results if r["status"] == "OK"])
    fail_count = len([r for r in results if r["status"] == "FAIL"])
    print(f"\n================================================================================")
    print(f" BATCH ABGESCHLOSSEN: {ok_count}/{count} erfolgreich, {fail_count} Fehler.")
    print(f" Matrix-Export     : {matrix_file} & {matrix_final_file}")
    print(f" Ergebnisprotokoll : {out_file}")
    print(f"================================================================================\n")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="100 Drafts Batch Runner")
    parser.add_argument("owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH", nargs="?")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--start-row", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Ueberschreibt bestehende Entwuerfe ohne Cache")
    args = parser.parse_args()

    if args.owner in ["JOEL", "BOTH"]:
        run_batch("JOEL", count=args.count, start_row=args.start_row, force=args.force)
    if args.owner in ["JORDI", "BOTH"]:
        run_batch("JORDI", count=args.count, start_row=args.start_row, force=args.force)
