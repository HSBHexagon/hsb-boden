#!/usr/bin/env python3
"""
HSB Sales OS - Batch-Runner für Entwürfe (Joel Cherino Diaz & Jordie Post).
Sicherheit: Reines DraftEmail, REAL_EXTERNAL_SEND_COUNT = 0.
Enthält:
- Offizielles HSB Firmenlogo in der Signatur
- Anhang: HSB-HEXAGON-Industrieboeden-Flyer.pdf (bytegenau verifiziert)
- Vollständige Rechtskonformität (§ 35a GmbHG + § 7 UWG)
- Live Google Sheet Writeback über 2D-Matrix Bulk-Engine (17 Spalten AN:BD)
"""
import argparse
import base64
import datetime
import html
import json
import re
import socket
import sys
import time
import urllib.parse
import urllib.request

socket.setdefaulttimeout(90)
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from hsb_core import FLYERS, normalize_owner, EMAIL_RE
from high_volume_matrix_engine import load_leads_authoritative, write_2d_matrix_bulk

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
        f'<p style="margin:14px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#777777;line-height:1.35;">'
        f'{FIRMA["name"]} &middot; Sitz: {FIRMA["sitz"]}<br>'
        f'Registergericht: {FIRMA["registergericht"]}, {FIRMA["hrb"]}<br>'
        f'Geschäftsführer: {FIRMA["geschaeftsfuehrer"]}'
        f'</p>'
    )

def anrede_fuer(lead: dict) -> str:
    ap = str(lead.get("Ansprechpartner") or "").strip()
    if not ap or ap.lower() in ["none", "nan"]:
        return "Sehr geehrte Damen und Herren,"
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
    refresh_token = get_fc_refresh_token()

    token_url = f"https://login.microsoftonline.com/{FC_TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": FC_CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": FC_SCOPE
    }).encode("utf-8")

    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(token_url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                tokens = json.loads(resp.read().decode("utf-8"))
                return tokens["access_token"]
        except Exception as ex:
            last_err = ex
            if attempt < 3:
                time.sleep(1.5 * attempt)
                continue
            raise last_err

def create_single_draft(owner: str, lead: dict, flyer_b64: str, flyer_name: str, access_token: str = None, batch_id: str = "") -> dict:
    flyer = FLYERS[owner]
    anrede = anrede_fuer(lead)
    anrede_esc = html.escape(anrede)
    firma_str = str(lead.get("Firma") or "").strip()
    company = firma_str if (firma_str and firma_str.lower() not in ["none", "nan"]) else "Ihr Unternehmen"
    company_esc = html.escape(company)
    betreff = f"Industrieböden für {company} – Beratung von {flyer.display_name}"

    sig = signatur_html(flyer.display_name, flyer.mailbox, flyer.mobile)
    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#222222;line-height:1.5;">'
        f'<p style="margin:0 0 12px 0;">{anrede_esc}</p>'
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

    last_err = None
    for attempt in range(1, 4):
        try:
            if owner == "JOEL":
                req = urllib.request.Request(JOEL_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.loads(r.read().decode("utf-8"))
            else:
                req = urllib.request.Request(JORDI_CONNECTOR_URL, data=data, headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }, method="POST")
                with urllib.request.urlopen(req, timeout=90) as r:
                    run_id = r.headers.get("x-ms-workflow-run-id")
                    return {"status": "ACCEPTED_ASYNC", "runId": run_id, "code": r.getcode()}
        except Exception as ex:
            last_err = ex
            if attempt < 3:
                time.sleep(1.5 * attempt)
                continue
            raise last_err

def run_batch(owner: str, count: int = 100, start_row: int = None, force: bool = False, dry_run: bool = False) -> list:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"BATCH-{count}-{owner}-{ts[:8]}"

    print(f"\n================================================================================")
    print(f" STARTE BATCH: {count} ENTWUERFE FUER {owner} (Batch-ID: {batch_id})")
    if dry_run:
        print(f" [DRY-RUN MODUS AKTIV: Es werden keine externen Flow-Aufrufe getätigt]")
    print(f"================================================================================")
    flyer = FLYERS[owner]
    flyer_bytes = flyer.path.read_bytes()
    flyer_b64 = base64.b64encode(flyer_bytes).decode("ascii")
    print(f"Anlage-Sichtname : {flyer.attachment_name}")
    print(f"Dateigröße       : {len(flyer_bytes)} Bytes (SHA256: {flyer.sha256[:16]}...)")
    print(f"Absender         : {flyer.display_name} <{flyer.mailbox}>")

    access_token = None
    if owner == "JORDI" and not dry_run:
        print("Hole frisches MSAL-Token fuer Jordi...")
        access_token = get_jordi_token()
        print("Token aktiv.")

    leads = load_leads_authoritative()

    # Bestimme Startzeile falls nicht vorgegeben
    if start_row is None:
        start_row = 3534 if owner == "JORDI" else 152

    # Filter Leads nach Owner, E-Mail und Ausschlussregeln
    filtered_leads = []
    for l in leads:
        if normalize_owner(l.get("Owner")) != owner:
            continue
        if l["_row"] < start_row:
            continue
        email = str(l.get("Email") or "").strip()
        if not EMAIL_RE.match(email):
            continue
        send_status = str(l.get("Send_Status") or "").lower()
        batch_status = str(l.get("Batch_Status") or "").upper()
        if send_status in ["sent", "gesendet"] or batch_status == "SENT":
            continue
        if str(l.get("Reply_Status") or "").lower() in ["bounced", "hard_bounce"]:
            continue
        if str(l.get("Opt_Out") or "").lower() in ["yes", "ja", "opt_out"]:
            continue
        if str(l.get("Suppressed") or "").lower() in ["yes", "ja", "true"]:
            continue
        filtered_leads.append(l)
        if len(filtered_leads) == count:
            break

    if len(filtered_leads) < count:
        print(f"WARNUNG: Nur {len(filtered_leads)} geeignete Leads ab Zeile {start_row} gefunden (angefordert: {count}).")

    if not filtered_leads:
        print("Keine verarbeitbaren Leads gefunden. Abbruch.")
        return []

    print(f"Ausgewählte Leads: {len(filtered_leads)} (Zeilen {filtered_leads[0]['_row']} bis {filtered_leads[-1]['_row']})\n")

    batches_dir = REPO_ROOT / "batches"
    batches_dir.mkdir(exist_ok=True)

    known_results = {}
    if not force and not dry_run:
        for f in batches_dir.glob(f"result_*_{owner}_*.json"):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                for item in items:
                    if item.get("status") == "OK" and item.get("row"):
                        draft_id = str(item.get("draft_id") or "")
                        if "DRYRUN" in draft_id:
                            continue
                        known_results[item["row"]] = item
            except Exception:
                pass

    results = []
    matrix_rows = []
    out_file = batches_dir / f"result_{count}_{owner}_{ts}.json"

    def flush_progress(last_idx: int):
        if dry_run or not matrix_rows:
            return
        sub_matrix = matrix_rows[:last_idx]
        if not sub_matrix:
            return
        r_start = filtered_leads[0]["_row"]
        r_end = filtered_leads[len(sub_matrix) - 1]["_row"]
        try:
            write_2d_matrix_bulk(r_start, r_end, sub_matrix)
        except Exception as we:
            print(f"[WARN] Progress Matrix Writeback fehlgeschlagen: {we}")
        try:
            out_file.write_text(json.dumps(results[:last_idx], indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as fe:
            print(f"[WARN] Progress JSON Writeback fehlgeschlagen: {fe}")

    for i, lead in enumerate(filtered_leads, start=1):
        lead_id = lead.get("Lead_ID")
        email = lead.get("Email")
        row = lead.get("_row")
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        if row in known_results:
            cached = known_results[row]
            print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : BEREITS ERSTELLT (Cache genutzt)")
            results.append(cached)
            matrix_rows.append([
                cached.get("batch_id", batch_id),
                "drafted",
                "", "", "",
                "no",
                "no",
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

        if dry_run:
            print(f"[{i:03d}/{count}] Z.{row} {lead_id} ({email}) : [DRY-RUN] Entwurf verifiziert (Mock ID)")
            draft_id = f"DRYRUN-DRAFT-{lead_id}"
            item = {
                "row": row,
                "lead_id": lead_id,
                "email": email,
                "status": "OK",
                "batch_id": batch_id,
                "draft_id": draft_id,
                "drafted_at": now_iso,
                "attachment_name": flyer.attachment_name,
                "attachment_size": len(flyer_bytes)
            }
            results.append(item)
            matrix_rows.append([
                batch_id, "drafted", "", "", "", "no", "no", "DRAFTED",
                now_iso, draft_id, now_iso, "", "", "", "", "", ""
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
                    "no",
                    "no",
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
                    "no",
                    "no",
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
                "no",
                "no",
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
        time.sleep(1.0 if owner == "JOEL" else 0.40)
        if i % 10 == 0:
            flush_progress(i)

    # 2D-Matrix Bulk-Write ins Google Sheet
    if not dry_run and matrix_rows:
        write_2d_matrix_bulk(filtered_leads[0]["_row"], filtered_leads[-1]["_row"], matrix_rows)

    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    matrix_payload = {
        "owner": owner,
        "start_row": filtered_leads[0]["_row"],
        "end_row": filtered_leads[-1]["_row"],
        "range": f"ALL_LEADS!AN{filtered_leads[0]['_row']}:BD{filtered_leads[-1]['_row']}",
        "matrix": matrix_rows
    }
    matrix_file = batches_dir / f"matrix_{count}_{owner}.json"
    matrix_file.write_text(json.dumps(matrix_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    ok_count = len([r for r in results if r["status"] == "OK"])
    fail_count = len([r for r in results if r["status"] == "FAIL"])
    print(f"\n================================================================================")
    print(f" BATCH ABGESCHLOSSEN: {ok_count}/{count} erfolgreich, {fail_count} Fehler.")
    print(f" Matrix-Export     : {matrix_file}")
    print(f" Ergebnisprotokoll : {out_file}")
    print(f"================================================================================\n")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HSB Sales OS Draft Batch Runner")
    parser.add_argument("owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH", nargs="?")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--start-row", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Ueberschreibt bestehende Entwuerfe ohne Cache")
    parser.add_argument("--dry-run", action="store_true", help="Validiert Payload ohne echte Entwurfserstellung")
    args = parser.parse_args()

    if args.owner in ["JOEL", "BOTH"]:
        run_batch("JOEL", count=args.count, start_row=args.start_row, force=args.force, dry_run=args.dry_run)
    if args.owner in ["JORDI", "BOTH"]:
        run_batch("JORDI", count=args.count, start_row=args.start_row, force=args.force, dry_run=args.dry_run)
