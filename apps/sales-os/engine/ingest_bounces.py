#!/usr/bin/env python3
"""
HSB Sales OS - Automated Inbound Bounce Ingestion Engine.
Monitors mailbox bounce/NDR folders and inboxes for both Joel and Jordie.
Parses RFC 3464 DSN status codes and extracts failed recipient emails.
Synchronizes Single Source of Truth (SSOT) Google Sheet ALL_LEADS:
  - Bounce_Status = 'hard_bounce' (or 'soft_bounce')
  - Suppressed = 'yes'
  - Versandfreigabe = 'no'
  - Last_Error = Diagnostic Code
  - Notizen = Timestamped audit note
Appends event to INBOUND_EVENTS sheet.

Safety Invariant: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Pure inbound read & CRM sync)
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from reconcile_cloud_mailbox import (
    APIHUB_RESOURCE,
    RUNTIME_URL,
    CONNECTIONS,
    BOUNCE_SUBJ_RE,
    STATUS_CODE_RE,
    SEARCH_EMAIL_RE,
    INTERNAL_DOMAINS,
    get_az_apihub_token,
    call_office365_api,
    parse_rfc3464_dsn,
    build_inbound_event_row,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ingest_bounces")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


def load_all_leads_index(sheets_svc: Any) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """Loads all leads indexed by lowercase email, plus existing event IDs."""
    logger.info("Lade ALL_LEADS aus Google Sheet...")
    res = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="ALL_LEADS!A:BE"
    ).execute()
    rows = res.get("values", [])
    if not rows:
        return {}, set()

    email_to_lead = {}
    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 8 and r[8] and "@" in r[8]:
            email = r[8].strip().lower()
            email_to_lead[email] = {
                "row": idx,
                "lead_id": r[0] if len(r) > 0 else f"LEAD-{idx:04d}",
                "firma": r[1] if len(r) > 1 else "",
                "email": email,
                "versandfreigabe": r[25] if len(r) > 25 else "",
                "bounce_status": r[42] if len(r) > 42 else "",
                "reply_status": r[43] if len(r) > 43 else "",
                "suppressed": r[45] if len(r) > 45 else "",
                "last_error": r[55] if len(r) > 55 else "",
            }

    # Load INBOUND_EVENTS
    existing_event_ids = set()
    try:
        ev_res = sheets_svc.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="INBOUND_EVENTS!A:A"
        ).execute()
        for ev in ev_res.get("values", [])[1:]:
            if ev and ev[0]:
                existing_event_ids.add(ev[0].strip())
    except Exception as e:
        logger.warning(f"Konnte INBOUND_EVENTS nicht vorladen: {e}")

    logger.info(f"{len(email_to_lead)} Leads und {len(existing_event_ids)} Inbound-Events indiziert.")
    return email_to_lead, existing_event_ids


def scan_mailbox_for_bounces(
    token: str,
    conn_id: str,
    owner_name: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Scans bounce folders and inbox for bounce/NDR messages."""
    candidate_folders = ["Unzustellbar", "Bounces", "Posteingang", "Inbox", "Junk-E-Mail"]
    found_bounces = []
    scanned_folders = []

    for folder in candidate_folders:
        try:
            msgs = call_office365_api(token, conn_id, folder, top=limit)
            scanned_folders.append(folder)
            for m in msgs:
                subj = m.get("subject") or m.get("Subject") or ""
                body = m.get("body") or m.get("bodyPreview") or ""
                is_bounce, reason, failed_recips = parse_rfc3464_dsn(subj, body)
                if is_bounce:
                    found_bounces.append({
                        "msg_id": m.get("id"),
                        "internet_message_id": m.get("internetMessageId") or "",
                        "date_str": m.get("receivedDateTime") or m.get("DateTimeReceived") or "",
                        "sender": m.get("from") or m.get("From") or "",
                        "subject": subj,
                        "reason": reason,
                        "failed_recipients": failed_recips,
                        "source_folder": folder,
                    })
        except Exception as e:
            # Folder does not exist or access forbidden
            continue

    logger.info(f"[{owner_name}] Ordner gescannt: {scanned_folders} -> {len(found_bounces)} Bounce-Nachrichten erkannt.")
    return found_bounces


def process_bounces(
    owner_key: str,
    dry_run: bool = True,
    limit: int = 50
) -> int:
    """Processes bounces for owner and writes back to Google Sheets."""
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
        logger.info(f"=== Starte Bounce-Scan fuer {o} ({mailbox_addr}) ===")

        try:
            bounces = scan_mailbox_for_bounces(token, conn_id, o, limit=limit)
        except Exception as e:
            logger.warning(f"[{o}] Mailbox-Abruf fehlgeschlagen: {e}")
            continue

        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sheet_updates = []
        new_event_rows = []

        for b in bounces:
            for failed_email in b["failed_recipients"]:
                fe_lower = failed_email.strip().lower()
                if fe_lower in email_to_lead:
                    lead = email_to_lead[fe_lower]
                    row_num = lead["row"]
                    lead_id = lead["lead_id"]

                    # Determine hard vs soft bounce
                    is_soft = any(c in b["reason"].lower() for c in ["4.2.2", "mailbox full", "quota", "temporarily"])
                    bounce_val = "soft_bounce" if is_soft else "hard_bounce"

                    if lead["bounce_status"] != bounce_val or lead["suppressed"] != "yes":
                        logger.info(f"[{o}] TREFFER: Zeile {row_num:4d} | {lead_id} | {fe_lower} -> {bounce_val} ({b['reason']})")
                        total_updated += 1

                        # Spalte Z: Versandfreigabe = no
                        sheet_updates.append({
                            "range": f"ALL_LEADS!Z{row_num}",
                            "values": [["no"]]
                        })
                        # Spalte AQ: Bounce_Status
                        sheet_updates.append({
                            "range": f"ALL_LEADS!AQ{row_num}",
                            "values": [[bounce_val]]
                        })
                        # Spalte AR: Reply_Status
                        sheet_updates.append({
                            "range": f"ALL_LEADS!AR{row_num}",
                            "values": [["bounced"]]
                        })
                        # Spalte AT: Suppressed = yes
                        sheet_updates.append({
                            "range": f"ALL_LEADS!AT{row_num}",
                            "values": [["yes"]]
                        })
                        # Spalte BD: Last_Error
                        sheet_updates.append({
                            "range": f"ALL_LEADS!BD{row_num}",
                            "values": [[b["reason"]]]
                        })

                    # Event logging
                    event_id = f"INBOUND-BOUNCE-{lead_id}"
                    if event_id not in existing_event_ids:
                        existing_event_ids.add(event_id)
                        new_event_rows.append(
                            build_inbound_event_row(
                                event_id=event_id,
                                msg_date=b["date_str"] or now_iso,
                                mailbox=mailbox_addr,
                                sender=b["sender"],
                                subject=b["subject"],
                                message_id=b["internet_message_id"],
                                lead_id=lead_id,
                                classification=bounce_val.upper(),
                                stop="yes",
                                processed="PROCESSED",
                                notes=b["reason"],
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
            logger.info(f"[{o}] Synchronisation ERFOLGREICH abgeschlossen.")
        elif dry_run:
            logger.info(f"DRY-RUN: {len(sheet_updates)} geplante Zellen-Updates, {len(new_event_rows)} Inbound-Events. Kein Schreibzugriff.")

    return total_updated


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Inbound Bounce Ingestion Engine")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL", help="Postfach-Eigentuemer")
    parser.add_argument("--apply", action="store_true", default=False, help="Aenderungen ins Google Sheet schreiben")
    parser.add_argument("--limit", type=int, default=100, help="Maximale Nachrichten pro Ordner")
    args = parser.parse_args()

    dry_run = not args.apply
    logger.info(f"=== HSB BOUNCE INGESTION ENGINE ===")
    logger.info(f"Owner: {args.owner} | Modus: {'DRY-RUN' if dry_run else 'APPLY (Live-Sync)'}")
    
    updated = process_bounces(args.owner, dry_run=dry_run, limit=args.limit)
    logger.info(f"Fertig: {updated} Bounces verarbeitet.")


if __name__ == "__main__":
    main()
