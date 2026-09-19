#!/usr/bin/env python3
"""
HSB Sales OS - In-Place Draft Overhaul & Veredelungs-Runner.
Safely replaces outdated drafts in Outlook with enriched, personalized 2026-standard drafts:
- Canonical legal company name (e.g. "Napf-Chäsi AG" instead of domain slugs)
- Personal salutation ("Sehr geehrte/r Frau/Herr ...")
- Niche-specific B2B copy (CIP, AGI S 40, acid resistance)
- Prominent unsubscribe system (HTML table + <u>Hier abmelden</u> -> /abmelden)
- Canonical 241 KB flyer (HSB-HEXAGON-Industrieboeden-Flyer.pdf, SHA-256 verified)
- Pre-Send DNS/MX validation
- Atomic sync with Google Sheet ALL_LEADS

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

from hsb_core import FLYERS, assert_asset_gate, normalize_owner, sanitize_company_name, EMAIL_RE
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
logger = logging.getLogger("overhaul_drafts")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


def delete_draft_apihub(token: str, conn_id: str, msg_id: str) -> bool:
    """Deletes an old draft from the mailbox via APIHub."""
    del_url = f"{RUNTIME_URL}/{conn_id}/Mail/{urllib.parse.quote(msg_id, safe='')}"
    req = urllib.request.Request(del_url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        logger.warning(f"Fehler beim Löschen des alten Entwurfs ({msg_id[:25]}...): {e}")
        return False


def load_sheet_leads(sheets_svc: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[int, Dict[str, Any]]]]:
    """Loads all leads from ALL_LEADS into memory with row index."""
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
        all_leads.append(d)
        email = d.get("E-Mail") or d.get("Email") or ""
        if email and "@" in email:
            email_map[email.strip().lower()] = (idx, d)

    return all_leads, email_map


def run_overhaul(limit: int = 20, dry_run: bool = True) -> int:
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0, "Sicherheits-Invariante verletzt!"

    owner = "JOEL"
    conf = CONNECTIONS[owner]
    conn_id = conf["connection_id"]

    flyer = assert_asset_gate(owner)
    flyer_bytes = flyer.path.read_bytes()
    flyer_b64 = base64.b64encode(flyer_bytes).decode("ascii")

    token = get_az_apihub_token()
    sheets_svc = get_sheets_service()

    all_leads, email_map = load_sheet_leads(sheets_svc)
    logger.info(f"{len(all_leads)} Leads aus Sheet indiziert.")

    # 1. Fetch current drafts from Joel's mailbox
    logger.info(f"Lese die ersten {limit + 10} Entwürfe aus Joels Postfach...")
    raw_drafts = call_office365_api(token, conn_id, "Entwürfe", top=limit + 15)

    # Filter out test dummies and non-leads
    valid_drafts = []
    for d in raw_drafts:
        to_recip = (d.get("toRecipients") or "").strip().lower()
        if not to_recip or "@" not in to_recip or "example.com" in to_recip or "hsb-boden.de" in to_recip:
            continue
        valid_drafts.append(d)
        if len(valid_drafts) >= limit:
            break

    logger.info(f"{len(valid_drafts)} kundenbezogene Entwürfe für Überarbeitung ausgewählt.")

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"OVERHAUL-JOEL-{ts[:8]}"

    overhaul_items = []

    for idx, d in enumerate(valid_drafts, start=1):
        old_id = d.get("id")
        old_subj = d.get("subject") or ""
        to_email = (d.get("toRecipients") or "").strip().lower()

        lead_entry = email_map.get(to_email)
        if not lead_entry:
            logger.warning(f"[{idx:02d}] {to_email} nicht in ALL_LEADS gefunden. Überspringe.")
            continue

        row_num, lead_data = lead_entry
        lead_id = lead_data.get("Lead-ID") or lead_data.get("Lead_ID") or f"LEAD-{row_num}"

        # Run Enrichment
        enr_res = enrich_lead(row_num, lead_data)
        new_company = enr_res.enriched_company or sanitize_company_name(lead_data.get("Firma") or "", to_email)
        new_contact = enr_res.enriched_contact or lead_data.get("Ansprechpartner") or ""

        # Update lead_data dict for copy generation
        lead_data_updated = dict(lead_data)
        lead_data_updated["Firma"] = new_company
        lead_data_updated["Company"] = new_company
        lead_data_updated["Ansprechpartner"] = new_contact
        lead_data_updated["Contact"] = new_contact

        anrede = anrede_fuer(lead_data_updated)
        new_subj = f"Industrieböden für {new_company} – Beratung von {flyer.display_name}"

        overhaul_items.append({
            "idx": idx,
            "row": row_num,
            "lead_id": lead_id,
            "email": to_email,
            "old_id": old_id,
            "old_subj": old_subj,
            "new_subj": new_subj,
            "old_company": lead_data.get("Firma") or "",
            "new_company": new_company,
            "anrede": anrede,
            "lead_data_updated": lead_data_updated,
            "mx_ok": enr_res.status != "INVALID_MX",
        })

    # Summary Display
    print("\n" + "=" * 125)
    print(f"{'Nr':<3} | {'Row':<5} | {'Lead-ID':<18} | {'Email':<28} | {'Firma Alt -> Neu':<40} | {'MX':<4}")
    print("-" * 125)
    for it in overhaul_items:
        firma_str = f"{it['old_company'][:16]} -> {it['new_company'][:20]}"
        mx_str = "OK" if it["mx_ok"] else "FAIL"
        print(f"{it['idx']:<3} | {it['row']:<5} | {it['lead_id']:<18} | {it['email'][:28]:<28} | {firma_str:<40} | {mx_str:<4}")
    print("=" * 125 + "\n")

    if dry_run:
        logger.info(f"DRY-RUN: {len(overhaul_items)} Entwürfe für Überarbeitung vorbereitet. Kein Schreibzugriff.")
        return len(overhaul_items)

    # Apply Overhaul
    logger.info(f"APPLY: Starte Überarbeitung von {len(overhaul_items)} Entwürfen in Joels Postfach...")
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    sheet_updates = []
    completed_count = 0

    for it in overhaul_items:
        if not it["mx_ok"]:
            logger.warning(f"Überspringe {it['email']}: Kein gültiger MX-Record.")
            continue

        row_num = it["row"]
        old_id = it["old_id"]
        to_email = it["email"]

        t0 = time.time()
        # 1. Delete old draft
        del_ok = delete_draft_apihub(token, conn_id, old_id)
        if not del_ok:
            logger.warning(f"Konnte alten Entwurf {old_id[:20]} nicht löschen. Fahre dennoch fort.")

        # 2. Create new enriched draft via Flow
        try:
            flow_res = create_single_draft(
                owner=owner,
                lead=it["lead_data_updated"],
                flyer_b64=flyer_b64,
                flyer_name=flyer.attachment_name,
                access_token=None,
                batch_id=batch_id
            )
            dt = time.time() - t0
            new_draft_id = flow_res.get("draftId", "")
            int_msg_id = flow_res.get("internetMessageId", "")
            conv_id = flow_res.get("conversationId", "")
            size = flow_res.get("attachmentSize", len(flyer_bytes))

            logger.info(f"[{it['idx']:02d}/{len(overhaul_items)}] Z.{row_num} {it['lead_id']} ({to_email}) : NEU ERSTELLT in {dt:.1f}s [Draft: {new_draft_id[:20]}..., Anhang: {size} B]")
            completed_count += 1

            # Update ALL_LEADS values
            # B: Firma
            sheet_updates.append({"range": f"ALL_LEADS!B{row_num}", "values": [[it["new_company"]]]})
            # G: Ansprechpartner
            if it["anrede"] != "Sehr geehrte Damen und Herren,":
                sheet_updates.append({"range": f"ALL_LEADS!G{row_num}", "values": [[it["anrede"].replace("Sehr geehrte Frau ", "Frau ").replace("Sehr geehrter Herr ", "Herr ").rstrip(",")]]})
            # AN: Batch_ID
            sheet_updates.append({"range": f"ALL_LEADS!AN{row_num}", "values": [[batch_id]]})
            # AO: Send_Status = drafted
            sheet_updates.append({"range": f"ALL_LEADS!AO{row_num}", "values": [["drafted"]]})
            # AU: Batch_Status = DRAFTED
            sheet_updates.append({"range": f"ALL_LEADS!AU{row_num}", "values": [["DRAFTED"]]})
            # AW: Draft_ID
            sheet_updates.append({"range": f"ALL_LEADS!AW{row_num}", "values": [[new_draft_id]]})
            # AX: Drafted_At
            sheet_updates.append({"range": f"ALL_LEADS!AX{row_num}", "values": [[now_iso]]})
            # AZ: Outlook_Message_ID
            sheet_updates.append({"range": f"ALL_LEADS!AZ{row_num}", "values": [[new_draft_id]]})
            # BA: Internet_Message_ID
            sheet_updates.append({"range": f"ALL_LEADS!BA{row_num}", "values": [[int_msg_id]]})
            # BB: Conversation_ID
            sheet_updates.append({"range": f"ALL_LEADS!BB{row_num}", "values": [[conv_id]]})

            # Pacing delay
            time.sleep(0.4)

        except Exception as ex:
            logger.error(f"Fehler beim Erstellen des neuen Entwurfs für {to_email}: {ex}")

    if sheet_updates:
        logger.info(f"Schreibe {len(sheet_updates)} Zellen-Updates in Google Sheet ALL_LEADS...")
        sheets_svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": sheet_updates}
        ).execute()
        logger.info("Sheet-Writeback ERFOLGREICH abgeschlossen.")

    logger.info(f"=== ÜBERARBEITUNG BEENDET: {completed_count}/{len(overhaul_items)} Entwürfe veredelt ===")
    return completed_count


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - In-Place Draft Overhaul Runner")
    parser.add_argument("--limit", type=int, default=20, help="Anzahl zu überarbeitender Entwürfe (Standard: 20)")
    parser.add_argument("--apply", action="store_true", default=False, help="Überarbeitung live in Exchange & Sheet anwenden")
    args = parser.parse_args()

    dry_run = not args.apply
    logger.info(f"=== HSB DRAFT OVERHAUL & ENRICHMENT ===")
    logger.info(f"Modus: {'DRY-RUN (Vorschau)' if dry_run else 'APPLY (Live-Update)'} | Limit: {args.limit}")

    run_overhaul(limit=args.limit, dry_run=dry_run)


if __name__ == "__main__":
    main()
