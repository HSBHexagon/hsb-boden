#!/usr/bin/env python3
"""
HSB Sales OS - Automated Dual-Mailbox Outreach Dispatcher.
Führt den echten E-Mail-Versand kontrolliert und spam-geschützt für beide Postfächer durch:
- Joel Cherino Diaz: j-cherino@hsb-boden.com
- Jordie Post: j-post@hsb-boden.com

Anti-Spam & Deliverability Governance:
1. Interleaved Sending: Mails wechseln sich zwischen Joel und Jordi ab (maximaler Abstand pro Postfach).
2. Stochastischer Jitter: 45 bis 90 Sekunden Pause zwischen den Versendungen.
3. Pre-Send MX-Check: Domains ohne gültigen MX-Record werden übersprungen.
4. Forensischer Schutz: 0 Überschneidungen mit DE_VERSENDUNGEN_FORENSIK.
5. Automatischer Draft-Cleanup: Gesendete Entwürfe werden sofort aus IMAP bereinigt.
6. CRM-Sync: Google Sheet ALL_LEADS wird atomar auf 'sent' mit ISO-Zeitstempel und Message-ID gesetzt.
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from com_mailbox_manager import ComMailboxClient
from hsb_core import assert_asset_gate, check_eligibility, normalize_owner, sanitize_company_name
from enrich_company_names import check_domain_mx, enrich_lead
from run_100_batch import anrede_fuer
from overhaul_drafts import build_canonical_body_2026, load_sheet_leads
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("dual_outreach")


def load_forensic_sent_recipients(sheets_svc) -> Set[str]:
    """Der aktuelle Master-CRM-Forensikstand ist Pflicht vor Live-Versand."""
    forensic_file = REPO_ROOT / "data" / "forensic_sent_recipients.json"
    if not forensic_file.is_file():
        raise RuntimeError("Lokaler Forensik-Abgleich fehlt: Versand gesperrt")
    with forensic_file.open("r", encoding="utf-8") as fh:
        historic = json.load(fh)
    if not isinstance(historic, (dict, list)):
        raise RuntimeError("Lokaler Forensik-Abgleich ungueltig")
    sent = {str(em).strip().lower() for em in historic if isinstance(em, str) and "@" in em}
    remote = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="DE_VERSENDUNGEN_FORENSIK!A:H",
    ).execute().get("values", [])
    if not remote or "Empfaenger_Email" not in remote[0]:
        raise RuntimeError("Master-CRM-Forensik nicht lesbar: Versand gesperrt")
    col = remote[0].index("Empfaenger_Email")
    for entry in remote[1:]:
        if len(entry) > col and "@" in str(entry[col]):
            sent.add(str(entry[col]).strip().lower())
    return sent


def select_send_candidates(
    all_leads: List[Dict[str, Any]],
    owner: str,
    limit: int,
    forensic_sent: Set[str]
) -> List[Dict[str, Any]]:
    norm_owner = normalize_owner(owner)
    candidates = []
    selected_emails = set()

    for lead in all_leads:
        lead_owner = str(lead.get("Verantwortlicher") or "").upper()
        if norm_owner == "JOEL" and "JOEL" not in lead_owner:
            continue
        if norm_owner == "JORDI" and "JORDI" not in lead_owner and "JORDIE" not in lead_owner:
            continue

        email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
        if not email or "@" not in email:
            continue

        if email in forensic_sent:
            continue

        send_st = str(lead.get("Send_Status") or "").lower()
        batch_st = str(lead.get("Batch_Status") or "").lower()
        if "sent" in send_st or "gesendet" in send_st or "bounce" in send_st or "reply" in batch_st:
            continue

        optout = str(lead.get("Opt_Out") or lead.get("Opt-out-Status") or "").lower()
        pipeline = str(lead.get("Pipeline") or lead.get("Pipeline_Status") or "").lower()
        if optout in ("yes", "ja") or "abgemeldet" in pipeline or "widerspruch" in pipeline:
            continue

        # Kanonische CRM-Versandfreigabe fail-closed pruefen.
        verdict = check_eligibility(lead)
        if not verdict.eligible or email in selected_emails:
            continue

        # Vorab-MX-Check
        domain = email.split("@")[-1]
        if not check_domain_mx(domain):
            continue

        selected_emails.add(email)
        candidates.append(lead)
        if len(candidates) >= limit:
            break

    return candidates


def run_dual_dispatch(count_per_owner=25, jitter_min=45, jitter_max=90, dry_run=True):
    from outbound_safety import dispatch_verified
    return dispatch_verified(count_per_owner=count_per_owner, dry_run=dry_run,
        jitter_min=jitter_min, jitter_max=jitter_max)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS Dual Outreach Dispatcher")
    parser.add_argument("--count", type=int, default=25, help="Anzahl Mails pro Postfach")
    parser.add_argument("--jitter-min", type=int, default=45, help="Minimale Pause in Sekunden")
    parser.add_argument("--jitter-max", type=int, default=90, help="Maximale Pause in Sekunden")
    parser.add_argument("--apply", action="store_true", help="Echten Versand starten (Standard: Dry-Run)")
    args = parser.parse_args()

    run_dual_dispatch(
        count_per_owner=args.count,
        jitter_min=args.jitter_min,
        jitter_max=args.jitter_max,
        dry_run=not args.apply
    )


if __name__ == "__main__":
    main()
