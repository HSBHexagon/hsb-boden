#!/usr/bin/env python3
"""
HSB Sales OS - Industrial Full Mailbox Sweeper & Overhaul Engine.

Solves the 1.000+ drafts issue systematically:
1. Paginates/drains the entire mailbox folder 'Entwürfe' in batches of 50.
2. Identifies and PURGES all broken drafts (empty recipient, Mustermann, test dummies).
3. Identifies and OVERHAULS all outdated drafts (generic "Ihr Unternehmen", old 1.5 MB flyer, missing logo).
4. Replaces them in-place with pristine canonical 2026 drafts:
   - Real recipient email from ALL_LEADS
   - Enriched company name (via enrich_company_names / Exa)
   - Proper salutation
   - Canonical 241 KB flyer (HSB-HEXAGON-Industrieboeden-Flyer.pdf)
   - Bicubic 102x75 logo
   - Unsubscribe table (Hier abmelden -> /abmelden)
   - § 35a GmbHG legal footer (Jordie Post GF)
5. Synchronizes IDs back to Google Sheet ALL_LEADS.

Safety Invariant: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Strict Draft-only governance)
"""
from __future__ import annotations

import argparse
import base64
import datetime
import html
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT / "engine" / "operator_layer"))

from hsb_core import FLYERS, assert_asset_gate, normalize_owner, sanitize_company_name
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from reconcile_cloud_mailbox import (
    CONNECTIONS,
    RUNTIME_URL,
    get_az_apihub_token,
    call_office365_api,
)
from enrich_company_names import enrich_lead, check_domain_mx
from run_100_batch import anrede_fuer, create_single_draft

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("mailbox_sweeper")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


def delete_draft(token: str, conn_id: str, msg_id: str) -> bool:
    """Deletes a draft from the mailbox via APIHub."""
    del_url = f"{RUNTIME_URL}/{conn_id}/Mail/{urllib.parse.quote(msg_id, safe='')}"
    req = urllib.request.Request(del_url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        logger.warning(f"Fehler beim Löschen des Entwurfs ({msg_id[:20]}...): {e}")
        return False


def load_sheet_index(sheets_svc: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[int, Dict[str, Any]]]]:
    """Loads all leads from ALL_LEADS into memory with fast email lookup."""
    logger.info("Lade und indiziere Google Sheet ALL_LEADS...")
    res = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="ALL_LEADS!A:BE"
    ).execute()
    rows = res.get("values", [])
    if not rows:
        return [], {}

    header = rows[0]
    email_map = {}
    all_leads = []

    for idx, r in enumerate(rows[1:], start=2):
        d = {}
        for h, v in zip(header, r):
            d[h] = v
        d["_row"] = idx
        email = (d.get("E-Mail") or d.get("Email") or "").strip()
        if email:
            d["Email"] = email
            d["E-Mail"] = email
            if "@" in email:
                email_map[email.lower()] = (idx, d)
        all_leads.append(d)

    logger.info(f"{len(all_leads)} Leads aus Sheet indiziert ({len(email_map)} mit valider E-Mail).")
    return all_leads, email_map


def classify_draft(d: Dict[str, Any], email_map: Dict[str, Tuple[int, Dict[str, Any]]]) -> Tuple[str, str]:
    """
    Classifies a draft:
    - PURGE: Empty recipient, Mustermann, test dummy, or unlinked garbage
    - OVERHAUL: Valid lead recipient, but generic copy ("Ihr Unternehmen"), old flyer, or missing logo
    - PRISTINE: Already matches full 2026 canonical standard
    """
    to_recip = (d.get("toRecipients") or "").strip().lower()
    subj = d.get("subject") or ""
    body = d.get("body") or ""

    if not to_recip:
        return "PURGE", "Empfängeradresse ist komplett leer"

    if any(x in to_recip or x in subj.lower() for x in ["mustermann", "example.com", "knopftest"]):
        return "PURGE", "Test-Dummy / Mustermann"

    lead_entry = email_map.get(to_recip)
    if not lead_entry:
        return "PURGE", f"Empfänger {to_recip} existiert nicht in ALL_LEADS"

    row_num, lead_data = lead_entry

    # Check if overhaul needed
    is_generic = "für Ihr Unternehmen" in subj or "für ihr unternehmen" in subj.lower()
    has_logo = "hsb-boden-logo.png" in body
    has_unsub = "abmelden" in body.lower()
    has_canonical_signer = "Jordie Post" in body or "Joel Cherino Diaz" in body

    if is_generic or not has_logo or not has_unsub or not has_canonical_signer:
        return "OVERHAUL", f"Veralteter Stand (Generic={is_generic}, Logo={has_logo}, Unsub={has_unsub})"

    return "PRISTINE", "Entspricht dem kanonischen 2026-Standard"


def run_sweep(owner: str = "JOEL", max_batches: int = 20, batch_size: int = 50, dry_run: bool = True):
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0, "Sicherheits-Invariante verletzt!"
    owner = normalize_owner(owner)
    conf = CONNECTIONS[owner]
    conn_id = conf["connection_id"]

    flyer = assert_asset_gate(owner)
    flyer_bytes = flyer.path.read_bytes()
    flyer_b64 = base64.b64encode(flyer_bytes).decode("ascii")

    token = get_az_apihub_token()
    sheets_svc = get_sheets_service()
    all_leads, email_map = load_sheet_index(sheets_svc)

    logger.info(f"=== STARTE MAILBOX SWEEPER FUER {owner} ({conf['account']}) ===")
    logger.info(f"Modus: {'DRY-RUN (Vorschau)' if dry_run else 'LIVE EXECUTION'}")
    logger.info(f"Max Batches: {max_batches} | Batch-Größe: {batch_size}")

    total_purged = 0
    total_overhauled = 0
    total_pristine = 0
    total_scanned = 0

    batch_nr = 0
    sheet_updates = []

    while batch_nr < max_batches:
        batch_nr += 1
        logger.info(f"\n--- Batch {batch_nr}/{max_batches}: Hole Entwürfe aus Exchange... ---")
        try:
            drafts = call_office365_api(token, conn_id, "Entwürfe", top=batch_size)
        except Exception as e:
            logger.error(f"Fehler beim Abruf von Entwürfen: {e}")
            break

        if not drafts:
            logger.info("Keine weiteren Entwürfe im Ordner gefunden. Mailbox vollständig durchlaufen.")
            break

        total_scanned += len(drafts)
        logger.info(f"{len(drafts)} Entwürfe in diesem Batch analysiert.")

        purge_list = []
        overhaul_list = []

        for d in drafts:
            action, reason = classify_draft(d, email_map)
            mid = d.get("id")
            to = (d.get("toRecipients") or "").strip()
            subj = d.get("subject") or ""

            if action == "PURGE":
                purge_list.append((mid, to, subj, reason))
            elif action == "OVERHAUL":
                lead_entry = email_map.get(to.lower())
                overhaul_list.append((d, lead_entry, reason))
            else:
                total_pristine += 1

        logger.info(f"Batch-Klassifizierung: PURGE={len(purge_list)}, OVERHAUL={len(overhaul_list)}, PRISTINE={len(drafts) - len(purge_list) - len(overhaul_list)}")

        if dry_run:
            for mid, to, subj, reason in purge_list[:5]:
                logger.info(f"  [DRY-PURGE] To: '{to}' | Subj: '{subj[:35]}' | Grund: {reason}")
            for d, (row, lead), reason in overhaul_list[:5]:
                logger.info(f"  [DRY-OVERHAUL] Z.{row} {lead.get('Lead_ID')} ({lead.get('Email')}) | Grund: {reason}")
            if batch_nr >= 3:
                logger.info("Dry-Run Limit von 3 Batches erreicht. Beende Vorschau.")
                break
            continue

        # LIVE EXECUTION
        # 1. Execute Purges
        for mid, to, subj, reason in purge_list:
            ok = delete_draft(token, conn_id, mid)
            if ok:
                total_purged += 1
                logger.info(f"  [PURGED] '{subj[:30]}' ({to}) -> {reason}")

        # 2. Execute Overhauls
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        batch_id = f"OVERHAUL-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M')}"

        for d, (row_num, lead_data), reason in overhaul_list:
            old_id = d.get("id")
            to_email = (d.get("toRecipients") or "").strip().lower()

            # Run Enrichment for best company & contact
            enr_res = enrich_lead(row_num, lead_data)
            new_company = enr_res.enriched_company or sanitize_company_name(lead_data.get("Firma") or "", to_email)
            new_contact = enr_res.enriched_contact or lead_data.get("Ansprechpartner") or ""

            lead_data_updated = dict(lead_data)
            lead_data_updated["Email"] = to_email
            lead_data_updated["E-Mail"] = to_email
            lead_data_updated["Firma"] = new_company
            lead_data_updated["Company"] = new_company
            lead_data_updated["Ansprechpartner"] = new_contact
            lead_data_updated["Contact"] = new_contact

            # Delete old draft
            delete_draft(token, conn_id, old_id)

            # Create fresh draft
            try:
                flow_res = create_single_draft(
                    owner=owner,
                    lead=lead_data_updated,
                    flyer_b64=flyer_b64,
                    flyer_name=flyer.attachment_name,
                    access_token=None,
                    batch_id=batch_id
                )
                new_draft_id = flow_res.get("draftId", "")
                int_msg_id = flow_res.get("internetMessageId", "")
                total_overhauled += 1
                logger.info(f"  [OVERHAULED] Z.{row_num} {to_email} -> {new_company} ({new_draft_id[:20]}...)")

                # Track sheet updates
                sheet_updates.append({"range": f"ALL_LEADS!B{row_num}", "values": [[new_company]]})
                sheet_updates.append({"range": f"ALL_LEADS!AN{row_num}", "values": [[batch_id]]})
                sheet_updates.append({"range": f"ALL_LEADS!AO{row_num}", "values": [["drafted"]]})
                sheet_updates.append({"range": f"ALL_LEADS!AU{row_num}", "values": [["DRAFTED"]]})
                sheet_updates.append({"range": f"ALL_LEADS!AW{row_num}", "values": [[new_draft_id]]})
                sheet_updates.append({"range": f"ALL_LEADS!AX{row_num}", "values": [[now_iso]]})
                sheet_updates.append({"range": f"ALL_LEADS!AZ{row_num}", "values": [[new_draft_id]]})
                sheet_updates.append({"range": f"ALL_LEADS!BA{row_num}", "values": [[int_msg_id]]})

            except Exception as ex:
                logger.error(f"Fehler bei Neuerstellung für Z.{row_num} ({to_email}): {ex}")

        # Batch writeback to Google Sheet every 25 updates
        if sheet_updates and len(sheet_updates) >= 20:
            logger.info(f"Schreibe {len(sheet_updates)} Updates ins Google Sheet ALL_LEADS zurück...")
            body = {"valueInputOption": "USER_ENTERED", "data": sheet_updates}
            sheets_svc.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            sheet_updates = []

    # Final flush
    if sheet_updates:
        logger.info(f"Schreibe letzte {len(sheet_updates)} Updates ins Google Sheet zurück...")
        body = {"valueInputOption": "USER_ENTERED", "data": sheet_updates}
        sheets_svc.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

    print("\n" + "=" * 80)
    print(f" MAILBOX SWEEPER BERICHT FUER {owner}")
    print("=" * 80)
    print(f"Gesamt gescannt    : {total_scanned}")
    print(f"Gelöscht (Purged)  : {total_purged}")
    print(f"Veredelt (Overhaul): {total_overhauled}")
    print(f"Bereits Kanonisch  : {total_pristine}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS Full Mailbox Sweeper")
    parser.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument("--batches", type=int, default=5, help="Anzahl Batches (je 50 Entwürfe)")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    run_sweep(
        owner=args.owner,
        max_batches=args.batches,
        batch_size=args.batch_size,
        dry_run=not args.apply
    )


if __name__ == "__main__":
    main()
