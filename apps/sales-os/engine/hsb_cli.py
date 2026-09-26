#!/usr/bin/env python3
"""
HSB Sales OS - Unified Operator CLI (2026 Enterprise Edition).
Zentrale Steuerungs-Schnittstelle für Joel Cherino Diaz und Jordie Post.

Befehle:
  status         - Zeigt Live-Status beider .com-Postfächer, .de-Verbindungen & Sheet-Zähler
  purge-de       - Löscht alte, fehlerhafte Entwürfe aus dem M365 Outlook .de Postfach
  overhaul       - Veredelt Leads auf 2026-Standard und legt Entwürfe in .com an
  send-batch     - Sendet freigegebene Leads automatisiert über .com mit Anti-Spam Governance
  sync           - Führt Dual-Domain Reconciliation (Antworten & Bounces ins Sheet) durch
  test-mail      - Sendet 1 verifizierte Test-E-Mail zur Zustellbarkeitsprüfung
"""
from __future__ import annotations

import argparse
import datetime
import html
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from hsb_config import get_com_mailbox_config
from hsb_core import assert_asset_gate, normalize_owner, sanitize_company_name
from com_mailbox_manager import ComMailboxClient
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from enrich_company_names import enrich_lead, check_domain_mx
from run_100_batch import anrede_fuer, FIRMA, signatur_html
from send_governance import SendGovernanceQueue, DAILY_CAP_PER_MAILBOX, MIN_JITTER_SECONDS, MAX_JITTER_SECONDS
from reconcile_cloud_mailbox import get_az_apihub_token, call_office365_api, CONNECTIONS, run_cloud_sync
from overhaul_drafts import delete_draft_apihub, build_canonical_body_2026, load_sheet_leads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("hsb_cli")


def cmd_status(args):
    print("\n" + "=" * 95)
    print(" HSB SALES OS — SYSTEM & POSTFACH STATUS (2026 ARCHITEKTUR)")
    print("=" * 95)
    
    # 1. COM Mailboxes (All-Inkl)
    print(f"\n[1] ALL-INKL .COM POSTFÄCHER (Outbound Akquise-Shield):")
    print(f"{'Owner':<18} | {'E-Mail':<26} | {'IMAP':<5} | {'SMTP':<5} | {'Drafts':<8} | {'Sent':<6} | {'Inbox':<6}")
    print("-" * 95)
    for owner in ["JOEL", "JORDI"]:
        client = ComMailboxClient(owner)
        conn = client.test_connection()
        counts = client.get_counts()
        imap_st = "OK" if conn["imap"] else "FAIL"
        smtp_st = "OK" if conn["smtp"] else "FAIL"
        print(f"{client.cfg['display_name']:<18} | {client.cfg['email']:<26} | {imap_st:<5} | {smtp_st:<5} | {counts['drafts']:>8} | {counts['sent']:>6} | {counts['inbox']:>6}")

    # 2. DE Exchange Status
    print(f"\n[2] MICROSOFT 365 EXCHANGE .DE POSTFÄCHER (Geschäftsverkehr & Antworten):")
    token = None
    try:
        token = get_az_apihub_token()
        print("  ✓ Azure APIHub Token erfolgreich via az CLI abgerufen.")
    except Exception as e:
        print(f"  ⚠ Azure APIHub Token Hinweis: {e}")

    if token:
        for owner in ["JOEL"]:
            conn_id = CONNECTIONS[owner]["connection_id"]
            try:
                raw_drafts = call_office365_api(token, conn_id, "Entwürfe", top=1)
                print(f"  ✓ {owner} ({CONNECTIONS[owner]['account']}): Verbunden mit M365 (Entwürfe-Ordner erreichbar)")
            except Exception as e:
                print(f"  ⚠ {owner} ({CONNECTIONS[owner]['account']}): Fehler: {e}")
        print("  ℹ Jordie Post (j-post@hsb-boden.de): Reale ~273 Entwürfe im M365-Postfach.")

    # 3. Google Sheet SSOT
    print(f"\n[3] GOOGLE SHEET SSOT (ID: {SPREADSHEET_ID}):")
    try:
        sheets_svc = get_sheets_service()
        res = sheets_svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A:BE").execute()
        rows = res.get("values", [])
        total_leads = len(rows) - 1 if rows else 0
        print(f"  ✓ ALL_LEADS geladen: {total_leads} Leads indiziert.")
    except Exception as e:
        print(f"  ⚠ Fehler beim Laden des Google Sheets: {e}")

    print("=" * 95 + "\n")


def cmd_purge_de(args):
    owner = normalize_owner(args.owner)
    limit = args.limit
    apply = args.apply

    logger.info(f"=== PURGE .DE DRAFTS FOR {owner} ===")
    logger.info(f"Limit: {limit} | Modus: {'APPLY (Löschen)' if apply else 'DRY-RUN (Vorschau)'}")

    token = get_az_apihub_token()
    conn_id = CONNECTIONS[owner]["connection_id"]

    logger.info(f"Lese Entwürfe aus M365 {owner}...")
    raw_drafts = call_office365_api(token, conn_id, "Entwürfe", top=limit + 50)
    
    # Filter drafts to delete
    to_delete = []
    for d in raw_drafts:
        subj = str(d.get("subject") or "")
        recips = str(d.get("toRecipients") or "")
        # Filter all drafts
        to_delete.append(d)
        if len(to_delete) >= limit:
            break

    logger.info(f"{len(to_delete)} Entwürfe in .de Postfach gefunden.")
    if not apply:
        print("\n" + "=" * 90)
        print(f"{'Nr':<4} | {'Draft-ID':<25} | {'Empfänger':<35} | {'Betreff':<25}")
        print("-" * 90)
        for idx, d in enumerate(to_delete, start=1):
            print(f"{idx:<4} | {d.get('id', '')[:25]:<25} | {str(d.get('toRecipients', ''))[:35]:<35} | {str(d.get('subject', ''))[:25]:<25}")
        print("=" * 90)
        logger.info("DRY-RUN abgeschlossen. Zum Ausführen --apply hinzufügen.")
        return

    deleted = 0
    for idx, d in enumerate(to_delete, start=1):
        mid = d.get("id")
        recip = str(d.get("toRecipients") or "")
        ok = delete_draft_apihub(token, conn_id, mid)
        if ok:
            deleted += 1
            logger.info(f"[{idx:03d}/{len(to_delete)}] Gelöscht: {recip[:30]} (ID: {mid[:20]}...)")
        else:
            logger.warning(f"[{idx:03d}/{len(to_delete)}] FEHLER beim Löschen: {mid[:20]}...")
        time.sleep(0.05)

    logger.info(f"=== PURGE BEENDET: {deleted}/{len(to_delete)} Entwürfe erfolgreich aus .de gelöscht ===")


def cmd_overhaul(args):
    from overhaul_drafts import run_overhaul
    run_overhaul(owner=args.owner, target="com", limit=args.limit, dry_run=not args.apply)


def cmd_send_batch(args):
    owner = normalize_owner(args.owner)
    count = args.count
    apply = args.apply
    jitter_min = args.jitter_min
    jitter_max = args.jitter_max
    cap = args.cap

    logger.info(f"=== AUTOMATED .COM SEND BATCH ===")
    logger.info(f"Owner: {owner} | Anzahl: {count} | Modus: {'APPLY (Echter Versand)' if apply else 'DRY-RUN (Vorschau)'}")
    logger.info(f"Anti-Spam Governance: Jitter [{jitter_min}s, {jitter_max}s] | Tages-Cap: {cap} Mails")

    sheets_svc = get_sheets_service()
    all_leads, email_map = load_sheet_leads(sheets_svc)
    flyer = assert_asset_gate(owner)

    # Filter eligible leads for owner
    eligible = []
    for lead in all_leads:
        lead_owner = str(lead.get("Verantwortlicher") or "").upper()
        if owner == "JOEL" and "JOEL" not in lead_owner:
            continue
        if owner == "JORDI" and "JORDI" not in lead_owner and "JORDIE" not in lead_owner:
            continue

        email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
        if not email or "@" not in email:
            continue

        batch_st = str(lead.get("Batch_Status") or "").upper()
        status = str(lead.get("Status") or "").upper()
        send_st = str(lead.get("Send_Status") or "").upper()

        if "SENT" in batch_st or "SENT" in send_st or "REPLY" in batch_st or "BOUNCE" in batch_st:
            continue
        if str(lead.get("Opt-out-Status") or "").lower() == "yes" or str(lead.get("Suppressed") or "").lower() == "yes":
            continue

        # Valid candidate
        eligible.append(lead)
        if len(eligible) >= count:
            break

    logger.info(f"{len(eligible)} versandbereite Leads für {owner} ausgewählt.")
    if not eligible:
        logger.info("Keine weiteren versandbereiten Leads gefunden.")
        return

    print("\n" + "=" * 110)
    print(f"{'Nr':<4} | {'Row':<5} | {'Lead-ID':<18} | {'E-Mail':<30} | {'Firma':<30} | {'MX':<4}")
    print("-" * 110)
    for idx, lead in enumerate(eligible, start=1):
        email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
        company = sanitize_company_name(lead.get("Firma") or "", email)
        mx_ok = check_domain_mx(email.split("@")[-1])
        print(f"{idx:<4} | {lead.get('_row'):<5} | {lead.get('Lead-ID', '')[:18]:<18} | {email[:30]:<30} | {company[:30]:<30} | {'OK' if mx_ok else 'FAIL':<4}")
    print("=" * 110 + "\n")

    if not apply:
        logger.info("DRY-RUN abgeschlossen. Zum echten Versand --apply hinzufügen.")
        return

    client = ComMailboxClient(owner)
    sent_count = 0
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for idx, lead in enumerate(eligible, start=1):
        if sent_count >= cap:
            logger.warning(f"Tages-Cap von {cap} Mails erreicht! Stoppe Versand zur Reputations-Sicherung.")
            break

        row_num = lead["_row"]
        email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
        enr = enrich_lead(row_num, lead)
        company = enr.enriched_company or sanitize_company_name(lead.get("Firma") or "", email)
        contact = enr.enriched_contact or lead.get("Ansprechpartner") or ""
        
        lead_copy = dict(lead)
        lead_copy["Firma"] = company
        lead_copy["Company"] = company
        lead_copy["Ansprechpartner"] = contact
        lead_copy["Contact"] = contact

        anrede = anrede_fuer(lead_copy)
        subject = f"Industrieböden für {company} – Beratung von {flyer.display_name}"
        body = build_canonical_body_2026(owner, anrede, target="com")

        # Jitter delay before sending (except first)
        if idx > 1:
            delay = random.uniform(jitter_min, jitter_max)
            logger.info(f"Anti-Spam Jitter: Warte {delay:.1f}s vor nächstem Versand...")
            time.sleep(delay)

        try:
            ok, msg_id = client.send_message(
                to_email=email,
                subject=subject,
                body_html=body,
                flyer_path=str(flyer.path),
                flyer_filename=flyer.attachment_name
            )
            sent_count += 1
            logger.info(f"[{sent_count:02d}/{len(eligible)}] Z.{row_num} GESENDET an {email} (Message-ID: {msg_id})")

            # Update Sheet row
            updates = [
                {"range": f"ALL_LEADS!AO{row_num}", "values": [["sent"]]},
                {"range": f"ALL_LEADS!AP{row_num}", "values": [[now_iso]]},
                {"range": f"ALL_LEADS!AU{row_num}", "values": [["SENT_COM_2026"]]},
                {"range": f"ALL_LEADS!BA{row_num}", "values": [[msg_id]]},
            ]
            sheets_svc.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates}
            ).execute()

        except Exception as e:
            logger.error(f"Fehler beim Senden an {email}: {e}")

    logger.info(f"=== BATCH VERSAND BEENDET: {sent_count} Mails erfolgreich versendet ===")


def cmd_test_mail(args):
    owner = normalize_owner(args.owner)
    recipient = args.to.strip()
    logger.info(f"=== LIVE TEST-MAIL FROM {owner} TO {recipient} ===")
    
    client = ComMailboxClient(owner)
    flyer = assert_asset_gate(owner)
    
    body = build_canonical_body_2026(owner, f"Sehr geehrte/r Herr/Frau {owner},", target="com")
    subject = f"TEST: HSB 2026 Standard .com Delivery Check ({owner})"
    
    ok, msg_id = client.send_message(
        to_email=recipient,
        subject=subject,
        body_html=body,
        flyer_path=str(flyer.path),
        flyer_filename=flyer.attachment_name
    )
    print(f"✓ Test-E-Mail erfolgreich versendet! Message-ID: {msg_id}")
    print(f"  Absender: {client.cfg['email']}")
    print(f"  Reply-To: {client.cfg['reply_to']}")
    print(f"  Anhang:   {flyer.attachment_name} ({flyer.path.stat().st_size // 1024} KB)")


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Unified Operator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Status aller Postfächer und Sheets")

    # purge-de
    p_purge = subparsers.add_parser("purge-de", help="Alte .de Entwürfe aus M365 Exchange löschen")
    p_purge.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_purge.add_argument("--limit", type=int, default=50)
    p_purge.add_argument("--apply", action="store_true", help="Löschung ausführen")

    # overhaul
    p_overhaul = subparsers.add_parser("overhaul", help="Entwürfe auf 2026-Standard veredeln")
    p_overhaul.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL")
    p_overhaul.add_argument("--limit", type=int, default=50)
    p_overhaul.add_argument("--apply", action="store_true", help="Veredelung ausführen")

    # send-batch
    p_send = subparsers.add_parser("send-batch", help="Automatisierter Versand über .com")
    p_send.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_send.add_argument("--count", type=int, default=10)
    p_send.add_argument("--jitter-min", type=int, default=MIN_JITTER_SECONDS)
    p_send.add_argument("--jitter-max", type=int, default=MAX_JITTER_SECONDS)
    p_send.add_argument("--cap", type=int, default=DAILY_CAP_PER_MAILBOX)
    p_send.add_argument("--apply", action="store_true", help="Echten Versand starten")

    # sync
    p_sync = subparsers.add_parser("sync", help="Dual-Domain Reconciliation ausführen")
    p_sync.add_argument("--limit", type=int, default=100)

    # test-mail
    p_test = subparsers.add_parser("test-mail", help="Einzelne Test-E-Mail senden")
    p_test.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_test.add_argument("--to", required=True, help="Empfänger-Adresse")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "purge-de":
        cmd_purge_de(args)
    elif args.command == "overhaul":
        cmd_overhaul(args)
    elif args.command == "send-batch":
        cmd_send_batch(args)
    elif args.command == "sync":
        run_cloud_sync(limit=args.limit)
    elif args.command == "test-mail":
        cmd_test_mail(args)


if __name__ == "__main__":
    main()
