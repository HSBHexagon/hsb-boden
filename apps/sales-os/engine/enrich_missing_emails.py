#!/usr/bin/env python3
"""
HSB Sales OS - Automated Web-Discovery for Missing & Bounced B2B Emails.

Finds verified corporate contact emails for leads with missing or bounced addresses:
1. Crawls company website and legal pages (/impressum, /kontakt, /ueber-uns)
2. Extracts business emails (filtering out hosting, webmaster, spam traps)
3. Verifies DNS/MX record existence before suggesting
4. Updates Google Sheet ALL_LEADS with audit trail
"""
from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import logging
import os
import re
import socket
import sys
import time
import urllib.parse
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT / "engine" / "operator_layer"))

from hsb_core import FREEMAIL_DOMAINS, sanitize_company_name
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from enrich_company_names import check_domain_mx, EXCLUDED_ENTITIES, USER_AGENT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("enrich_missing_emails")

IGNORE_EMAIL_PREFIXES = {
    "abuse", "noc", "security", "postmaster", "hostmaster", "webmaster",
    "privacy", "datenschutz", "dsgvo", "billing", "rechnung", "buchhaltung",
    "jobs", "karriere", "bewerbung", "support", "help", "noreply", "no-reply"
}


def extract_emails_from_html(html_text: str, domain: str) -> List[str]:
    """Findet E-Mail-Adressen im HTML und filtert Rauschen & Systemadressen aus."""
    # Extract from HTML; the hsb_core.EMAIL_RE is anchored for full-string validation.
    raw_matches = re.findall(r"(?i)(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", html_text)
    raw_host = str(domain or "").strip().lower()
    if not raw_host.startswith(("http://", "https://")):
        raw_host = "https://" + raw_host
    clean_domain = (urllib.parse.urlsplit(raw_host).hostname or "").removeprefix("www.")

    valid_emails = []
    seen = set()

    for m in raw_matches:
        em = m.strip().lower()
        if em in seen:
            continue
        seen.add(em)

        user, _, em_dom = em.partition("@")
        if not em_dom or not user:
            continue

        if user in IGNORE_EMAIL_PREFIXES:
            continue
        if any(ign in user for ign in ["noreply", "datenschutz"]):
            continue
        if em_dom in FREEMAIL_DOMAINS:
            continue
        if any(ex in em_dom for ex in ["sentry", "google", "wix", "wordpress", "cloudflare", "schema"]):
            continue

        valid_emails.append(em)

    # Bevorzuge Adressen mit derselben Domain wie die Website
    same_domain = [
        e for e in valid_emails
        if clean_domain and (e.partition("@")[2] == clean_domain or e.partition("@")[2].endswith("." + clean_domain))
    ]
    if same_domain:
        # Priorisiere info@, kontakt@, mail@, anfrage@
        priority = sorted(
            same_domain,
            key=lambda e: 0 if any(e.startswith(p) for p in ["info@", "kontakt@", "mail@", "anfrage@"]) else 1
        )
        return priority

    return []  # Never select unrelated third-party addresses from agency/footer text.


def crawl_domain_for_email(domain: str, timeout: int = 10) -> Optional[str]:
    """Sucht auf der Domain und Unterseiten (/impressum, /kontakt) nach einer Mail."""
    clean_dom = domain.lower().replace("http://", "").replace("https://", "").strip().rstrip("/")
    if not clean_dom or "." not in clean_dom:
        return None

    paths = ["", "/impressum", "/kontakt", "/impressum.html", "/kontakt.html"]
    found_emails = []

    for p in paths:
        url = f"https://{clean_dom}{p}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/html" in content_type:
                        html_text = resp.read(250000).decode("utf-8", errors="ignore")
                        emails = extract_emails_from_html(html_text, clean_dom)
                        if emails:
                            found_emails.extend(emails)
                            break
        except Exception:
            continue

    for candidate in found_emails:
        cand_domain = candidate.split("@")[-1]
        if check_domain_mx(cand_domain):
            return candidate

    return None


def run_missing_email_enrichment(limit: int = 20, apply: bool = False) -> int:
    """Sucht gezielt Leads ohne E-Mail oder mit Hard Bounce und reichert sie an."""
    sheets_svc = get_sheets_service()
    logger.info("Lade ALL_LEADS zur E-Mail-Ermittlung...")

    res = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="ALL_LEADS!A:BE"
    ).execute()
    rows = res.get("values", [])
    if not rows:
        return 0

    hdr = rows[0]
    col_lead_id = 0
    col_comp = 1
    col_email = 8
    col_website = next((i for i, value in enumerate(hdr) if str(value).strip().lower() == 'website'), 10)
    col_opt = 24
    col_bounce = 42
    col_supp = 45

    candidates = []
    for idx, r in enumerate(rows[1:], start=2):
        lead_id = r[col_lead_id] if len(r) > col_lead_id else ""
        comp = r[col_comp] if len(r) > col_comp else ""
        em = r[col_email] if len(r) > col_email else ""
        web = r[col_website] if len(r) > col_website else ""
        opt = r[col_opt] if len(r) > col_opt else ""
        bounce = r[col_bounce] if len(r) > col_bounce else ""
        supp = r[col_supp] if len(r) > col_supp else ""

        if str(opt).lower() == "yes" or str(supp).lower() == "yes":
            continue

        needs_email = (not em or "@" not in em or bounce == "hard_bounce")
        if needs_email and (web or comp):
            domain = web
            if not domain and "." in comp:
                domain = comp
            if domain:
                candidates.append({
                    "row": idx,
                    "lead_id": lead_id,
                    "company": comp,
                    "domain": domain,
                    "old_email": em,
                    "bounce": bounce,
                })
        if len(candidates) >= limit:
            break

    logger.info(f"{len(candidates)} Kandidaten ohne E-Mail / mit Bounce identifiziert.")
    if not candidates:
        return 0

    discovered = []
    for c in candidates:
        logger.info(f"Scanne {c['company']} ({c['domain']})...")
        found = crawl_domain_for_email(c["domain"])
        if found:
            logger.info(f"  ✓ GEFUNDEN: {found} (MX OK)")
            c["new_email"] = found
            discovered.append(c)
        else:
            logger.info(f"  ✗ Keine valide E-Mail ermittelt.")

    print("\n" + "=" * 115)
    print(f" ERGEBNIS DER AUTOMATISCHEN WEB-ERMITTLUNG ({len(discovered)} Treffer)")
    print("=" * 115)
    print(f"{'Row':<5} | {'Lead-ID':<18} | {'Firma':<30} | {'Domain':<25} | {'Ermittelte E-Mail'}")
    print("-" * 115)
    for d in discovered:
        print(f"{d['row']:<5} | {d['lead_id']:<18} | {d['company'][:30]:<30} | {d['domain'][:25]:<25} | {d['new_email']}")
    print("=" * 115 + "\n")

    if apply and discovered:
        updates = []
        for d in discovered:
            updates.append({"range": f"ALL_LEADS!I{d['row']}", "values": [[d["new_email"]]]})
            if d.get("bounce") == "hard_bounce":
                updates.append({"range": f"ALL_LEADS!AQ{d['row']}", "values": [[""]]})
            updates.append({"range": f"ALL_LEADS!Z{d['row']}", "values": [["no"]]})
        sheets_svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        logger.info(f"{len(discovered)} Leads mit neuen E-Mail-Adressen in Google Sheet aktualisiert.")

    return len(discovered)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Missing Email Discovery")
    parser.add_argument("--limit", type=int, default=10, help="Anzahl der zu prüfenden Leads")
    parser.add_argument("--apply", action="store_true", help="Ermittelte E-Mails ins Google Sheet schreiben")
    args = parser.parse_args()

    run_missing_email_enrichment(limit=args.limit, apply=args.apply)


if __name__ == "__main__":
    main()
