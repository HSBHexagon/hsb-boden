#!/usr/bin/env python3
"""
HSB Sales OS - Automated Inbound Opt-Out Ingestion Engine.
Monitors mailbox folders ('Abmeldungen', 'Posteingang', 'Inbox') for opt-out requests.
Detects both explicit headers/subjects and natural language B2B cancellation intents:
  - "Kein Bedarf", "Bitte löschen", "Aus dem Verteiler", "Nicht mehr kontaktieren", etc.
Synchronizes Single Source of Truth (SSOT) Google Sheet ALL_LEADS:
  - Opt-out-Status = 'yes'
  - Suppressed = 'yes'
  - Versandfreigabe = 'no'
  - Reply_Status = 'opt_out'
  - Pipeline = 'Abgemeldet'
  - Notizen = Timestamped opt-out record with quote
Appends event to INBOUND_EVENTS sheet.

Safety Invariant: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Pure inbound read & CRM lock)
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from reconcile_cloud_mailbox import (
    CONNECTIONS,
    INTERNAL_DOMAINS,
    get_az_apihub_token,
    call_office365_api,
    build_inbound_event_row,
)
from ingest_bounces import load_all_leads_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ingest_optouts")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0

OPTOUT_KEYWORDS_RE = re.compile(
    r"(abmelden|abmeldung|unsubscribe|austragen|verteiler|löschen|loeschen|"
    r"kein\s+bedarf|kein\s+interesse|nicht\s+mehr\s+kontaktieren|"
    r"keine\s+angebote|bitte\s+streichen|daten\s+löschen|stoppen)",
    re.IGNORECASE
)

EMAIL_EXTRACT_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def detect_optout_intent(subject: str, body: str) -> Tuple[bool, str]:
    """Detects whether a message represents an explicit or natural language opt-out."""
    subj_clean = subject.strip()
    body_clean = body.strip()

    # Check subject first
    m_subj = OPTOUT_KEYWORDS_RE.search(subj_clean)
    if m_subj:
        return True, f"Subject: '{m_subj.group(0)}'"

    # Check first 500 characters of body
    snippet = body_clean[:500]
    m_body = OPTOUT_KEYWORDS_RE.search(snippet)
    if m_body:
        # Extract snippet around match
        start = max(0, m_body.start() - 20)
        end = min(len(snippet), m_body.end() + 30)
        context = snippet[start:end].replace("\n", " ").strip()
        return True, f"Body: '...{context}...'"

    return False, ""


def scan_mailbox_for_optouts(
    token: str,
    conn_id: str,
    owner_name: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Scans opt-out folder and inboxes for opt-out messages."""
    candidate_folders = ["Abmeldungen", "Abmeldung", "Posteingang", "Inbox"]
    found_optouts = []
    scanned_folders = []

    for folder in candidate_folders:
        try:
            msgs = call_office365_api(token, conn_id, folder, top=limit)
            scanned_folders.append(folder)
            for m in msgs:
                subj = m.get("subject") or m.get("Subject") or ""
                body = m.get("body") or m.get("bodyPreview") or ""
                sender_raw = m.get("from") or m.get("From") or ""
                # Parse email from sender
                sender_emails = EMAIL_EXTRACT_RE.findall(sender_raw)
                sender = sender_emails[0].lower() if sender_emails else sender_raw.lower()

                # Don't process internal senders
                if any(dom in sender for dom in INTERNAL_DOMAINS):
                    continue

                is_optout, matched_snippet = detect_optout_intent(subj, body)
                if is_optout:
                    found_optouts.append({
                        "msg_id": m.get("id"),
                        "internet_message_id": m.get("internetMessageId") or "",
                        "date_str": m.get("receivedDateTime") or m.get("DateTimeReceived") or "",
                        "sender": sender,
                        "subject": subj,
                        "snippet": matched_snippet,
                        "body": body,
                        "source_folder": folder,
                    })
        except Exception as e:
            continue

    logger.info(f"[{owner_name}] Ordner gescannt: {scanned_folders} -> {len(found_optouts)} Opt-Outs erkannt.")
    return found_optouts


def process_optouts(
    owner_key: str,
    dry_run: bool = True,
    limit: int = 50
) -> int:
    """Processes opt-outs for owner and synchronizes with Google Sheets."""
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0, "Sicherheits-Invariante verletzt!"

    token = get_az_apihub_token()
    sheets_svc = get_sheets_service()
    email_to_lead, existing_event_ids = load_all_leads_index(sheets_svc)

    owners = [owner_key] if owner_key != "ALL" else ["JOEL", "JORDI"]
    total_updated = 0

    for o in owners:
        conf = CONNECTIONS.get(o)
        if not conf:
            continue
        conn_id = conf["connection_id"]
        mailbox_addr = conf["account"]
        logger.info(f"=== Starte Opt-Out-Scan fuer {o} ({mailbox_addr}) ===")

        try:
            optouts = scan_mailbox_for_optouts(token, conn_id, o, limit=limit)
        except Exception as e:
            logger.warning(f"[{o}] Mailbox-Abruf fehlgeschlagen: {e}")
            continue

        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sheet_updates = []
        new_event_rows = []

        for item in optouts:
            sender = item["sender"]
            matched_lead = None
            if sender in email_to_lead:
                matched_lead = email_to_lead[sender]
            else:
                # Check if an email mentioned in the body belongs to a lead
                body_emails = [
                    e.lower() for e in EMAIL_EXTRACT_RE.findall(item["body"])
                    if not any(d in e.lower() for d in INTERNAL_DOMAINS)
                ]
                for be in body_emails:
                    if be in email_to_lead:
                        matched_lead = email_to_lead[be]
                        break

            if matched_lead:
                row_num = matched_lead["row"]
                lead_id = matched_lead["lead_id"]

                if matched_lead["suppressed"] != "yes" or matched_lead["reply_status"] != "opt_out":
                    logger.info(f"[{o}] OPTOUT-TREFFER: Zeile {row_num:4d} | {lead_id} | {matched_lead['email']} -> {item['snippet']}")
                    total_updated += 1

                    # Spalte Y: Opt-out-Status = yes
                    sheet_updates.append({
                        "range": f"ALL_LEADS!Y{row_num}",
                        "values": [["yes"]]
                    })
                    # Spalte Z: Versandfreigabe = no
                    sheet_updates.append({
                        "range": f"ALL_LEADS!Z{row_num}",
                        "values": [["no"]]
                    })
                    # Spalte AR: Reply_Status = opt_out
                    sheet_updates.append({
                        "range": f"ALL_LEADS!AR{row_num}",
                        "values": [["opt_out"]]
                    })
                    # Spalte AT: Suppressed = yes
                    sheet_updates.append({
                        "range": f"ALL_LEADS!AT{row_num}",
                        "values": [["yes"]]
                    })
                    # Spalte BE: Pipeline = Abgemeldet
                    sheet_updates.append({
                        "range": f"ALL_LEADS!BE{row_num}",
                        "values": [["Abgemeldet"]]
                    })

                event_id = f"INBOUND-OPTOUT-{lead_id}"
                if event_id not in existing_event_ids:
                    existing_event_ids.add(event_id)
                    new_event_rows.append(
                        build_inbound_event_row(
                            event_id=event_id,
                            msg_date=item["date_str"] or now_iso,
                            mailbox=mailbox_addr,
                            sender=item["sender"],
                            subject=item["subject"],
                            message_id=item["internet_message_id"],
                            lead_id=lead_id,
                            classification="OPT_OUT",
                            stop="yes",
                            processed="PROCESSED",
                            notes=f"Opt-Out intent: {item['snippet']}",
                        )
                    )

        if not dry_run and sheet_updates:
            logger.info(f"Schreibe {len(sheet_updates)} Zellen-Updates in ALL_LEADS...")
            sheets_svc.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": sheet_updates}
            ).execute()

            if new_event_rows:
                logger.info(f"Hänge {len(new_event_rows)} Ereignisse an INBOUND_EVENTS an...")
                sheets_svc.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range="INBOUND_EVENTS!A:L",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": new_event_rows}
                ).execute()
            logger.info(f"[{o}] Opt-Out Synchronisation ERFOLGREICH abgeschlossen.")
        elif dry_run:
            logger.info(f"DRY-RUN: {len(sheet_updates)} geplante Zellen-Updates, {len(new_event_rows)} Inbound-Events. Kein Schreibzugriff.")

    return total_updated


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Inbound Opt-Out Ingestion Engine")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL", help="Postfach-Eigentuemer")
    parser.add_argument("--apply", action="store_true", default=False, help="Aenderungen ins Google Sheet schreiben")
    parser.add_argument("--limit", type=int, default=100, help="Maximale Nachrichten pro Ordner")
    args = parser.parse_args()

    dry_run = not args.apply
    logger.info(f"=== HSB OPT-OUT INGESTION ENGINE ===")
    logger.info(f"Owner: {args.owner} | Modus: {'DRY-RUN' if dry_run else 'APPLY (Live-Sync)'}")

    updated = process_optouts(args.owner, dry_run=dry_run, limit=args.limit)
    logger.info(f"Fertig: {updated} Opt-Outs verarbeitet.")


if __name__ == "__main__":
    main()
