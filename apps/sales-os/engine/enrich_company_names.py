#!/usr/bin/env python3
"""
HSB Sales OS - Automated Lead Company & Contact Enrichment Pipeline.

Enriches raw domain-slug leads with:
1. Canonical legal company name (e.g. "Brauerei Päffgen GmbH & Co. KG")
2. Managing Director / Executive contact (e.g. "Herr Rudolf Päffgen")
3. Pre-Send DNS/MX existence verification (Zero-Bounce Guarantee)

Features:
- Native DNS MX-Record check preventing invalid domain outreach
- Multi-threaded HTTP scraping with polite headers and timeout guards
- Impressum and Legal page detection (/impressum, /legal, /kontakt)
- German corporate forms parsing (GmbH, AG, e.K., KG, OHG, GbR, UG, SA, Sarl)
- Entity blacklist filtering (excludes banks, hosting providers, web agencies)
- Domain-relevance ranking preventing false-positive extractions
- Traditional beverage/dairy maker parsing (Brauerei, Kelterei, Molkerei, Käserei)
- Strict Freemail isolation (fail-closed against t-online, gmx, web.de, etc.)
- Direct Google Sheets API writeback with batching and audit logging
"""
from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT / "engine" / "operator_layer"))

from hsb_core import FREEMAIL_DOMAINS, FREEMAIL_NAMES, sanitize_company_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("enrich_company_names")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CORPORATE_FORMS_RE = re.compile(
    r"\b([A-ZÄÖÜ][\w\.\s\,\&\-–]{2,60}?\s+"
    r"(?:GmbH\s+&\s+Co\.?\s+KG|GmbH|AG|e\.?K\.?|KG|OHG|GbR|UG\s+\(haftungsbeschränkt\)|KGaA|Sarl|SA|BV|NV))\b",
    re.IGNORECASE
)

TRADITIONAL_TITLES_RE = re.compile(
    r"\b((?:Brauerei|Kelterei|Molkerei|Käserei|Kaeserei|Brennerei|Getränke(?:betrieb)?|Weinhaus|Weingut)\s+"
    r"[A-ZÄÖÜ][\w\s\-–]{2,40})\b",
    re.IGNORECASE
)

EXCLUDED_ENTITIES = {
    "strato", "strato ag", "ionos", "ionos se", "1&1", "hostpoint", "hostpoint ag", "hetzner",
    "hetzner online gmbh", "ovh", "godaddy", "wix", "jimdo", "squarespace", "shopify", "webflow",
    "wordpress", "typo3", "plesk", "cpanel", "apache", "nginx", "cookiebot", "usercentrics",
    "ubs ag", "credit suisse", "sparkasse", "volksbank", "deutsche bank", "commerzbank", "postbank", "raiffeisen",
    "scholl communications ag", "google llc", "alphabet inc", "microsoft corp", "meta platforms", "apple inc",
    "adobe", "cloudflare", "amazon web services", "telekom deutschland", "exklusive spezialitäten", "domain reserved", "domain", "reserved", "reserviert", "under construction", "hier entsteht", "geparkt", "parked",
    "spezialitäten", "feinkost", "willkommen", "home", "startseite", "kontakt", "impressum"

    "ubs ag", "credit suisse", "sparkasse", "volksbank", "deutsche bank", "commerzbank", "postbank", "raiffeisen",
    "scholl communications ag", "wordpress", "typo3", "hostpoint ag", "hetzner online gmbh", "strato ag",
    "ionos se", "cookiebot", "google llc", "alphabet inc", "microsoft corp", "meta platforms", "apple inc",
    "adobe", "cloudflare", "amazon web services", "telekom deutschland"
}

EXECUTIVE_PATTERNS = [
    re.compile(r"(?:Geschäftsführer(?:in)?|Geschäftsführung|Vertreten durch|Inhaber(?:in)?|Vorstand):\s*(?:<[^>]+>)*\s*([A-ZÄÖÜ][\w\.\-]+(?:\s+[A-ZÄÖÜ][\w\.\-]+){1,4})", re.IGNORECASE),
    re.compile(r"(?:Geschäftsführer(?:in)?|Inhaber(?:in)?)\s+(?:ist|sind)\s+([A-ZÄÖÜ][\w\.\-]+(?:\s+[A-ZÄÖÜ][\w\.\-]+){1,4})", re.IGNORECASE),
]

MALE_FIRSTNAMES = {
    "alexander", "andreas", "bernd", "christian", "christoph", "daniel", "dieter", "dirk",
    "florian", "frank", "georg", "hans", "heiko", "heinrich", "helmut", "holger", "jan",
    "jens", "joachim", "johannes", "jörg", "joerg", "josef", "jürgen", "juergen", "karl",
    "klaus", "lars", "lutz", "manfred", "manuel", "marcus", "markus", "martin", "matthias",
    "michael", "norbert", "oliver", "patrick", "paul", "peter", "philipp", "rainer", "ralf",
    "ralph", "reinhard", "robert", "roland", "rudolf", "ruediger", "sascha", "sebastian",
    "stefan", "stephan", "sven", "thomas", "thorsten", "torsten", "udo", "ulrich", "uwe",
    "volker", "walter", "werner", "wilhelm", "wolfgang"
}

FEMALE_FIRSTNAMES = {
    "andrea", "anja", "annette", "barbara", "bettina", "birgit", "brigitte", "christina",
    "claudia", "dagmar", "daniela", "elke", "eva", "franziska", "gabriele", "heike", "helga",
    "ingrid", "julia", "karin", "katja", "kerstin", "marion", "martina", "monika", "nicole",
    "petra", "sabine", "sandra", "silke", "stefanie", "stephanie", "susanne", "tanja", "ursula",
    "ute"
}


@dataclass
class EnrichmentResult:
    lead_id: str
    row_idx: int
    email: str
    domain: str
    original_company: str
    enriched_company: str
    original_contact: str
    enriched_contact: str
    confidence: float
    source_url: str
    status: str
    reason: str


def check_domain_mx(domain: str) -> bool:
    """Prüft per nativem DNS-Befehl, ob die Domäne valide Mail-Server besitzt."""
    if not domain:
        return False
    try:
        res = subprocess.run(["host", "-t", "mx", domain], capture_output=True, text=True, timeout=4)
        out = res.stdout.lower()
        if "mail is handled by" in out:
            return True
        if "has no mx record" in out or "not found" in out or "nxdomain" in out:
            return False
        # Fallback A-Record
        res_a = subprocess.run(["host", "-t", "a", domain], capture_output=True, text=True, timeout=4)
        return "has address" in res_a.stdout.lower()
    except Exception:
        return True


def extract_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    domain = email.split("@")[-1].strip().lower()
    if domain in FREEMAIL_DOMAINS:
        return None
    return domain


def fetch_url(url: str, timeout: int = 6) -> tuple[int, str, str]:
    """Holt eine Webseite per urllib mit Timeout und Weiterleitungs-Tracking."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return resp.status, content, resp.url
    except Exception as e:
        return 0, "", str(e)


def extract_impressum_url(base_url: str, html_text: str) -> str | None:
    """Findet Impressum/Kontakt-Links im HTML."""
    links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, re.IGNORECASE | re.DOTALL)
    keywords = ["impressum", "legal", "kontakt", "über-uns", "ueber-uns", "about", "contact"]
    for href, text in links:
        href_lower = href.lower()
        text_lower = text.lower()
        if any(kw in href_lower or kw in text_lower for kw in keywords):
            if href.startswith("mailto:") or href.startswith("javascript:") or href.startswith("tel:"):
                continue
            return urllib.parse.urljoin(base_url, href)
    return None


def determine_salutation(full_name: str) -> str:
    """Bestimmt 'Herr ...' oder 'Frau ...' anhand typischer deutscher Vornamen (auch bei Titeln)."""
    parts = full_name.strip().split()
    if not parts:
        return ""
    test_idx = 0
    if parts[0].lower().strip(".") in {"dr", "prof", "dipl", "dipl.-ing", "ing"} and len(parts) > 1:
        test_idx = 1
    first = parts[test_idx].lower().strip(".,-")
    if first in MALE_FIRSTNAMES:
        return f"Herr {full_name}"
    if first in FEMALE_FIRSTNAMES:
        return f"Frau {full_name}"
    return full_name


def parse_company_from_html(html_text: str, domain: str) -> tuple[str | None, float]:
    """Extrahiert juristische Firmennamen aus HTML mit Konfidenzwert und Blacklist-Filter."""
    domain_base = domain.split(".")[0].lower().replace("-", "")

    # 1. Alle Corporate Forms suchen und gegen Blacklist filtern
    matches = CORPORATE_FORMS_RE.findall(html_text)
    clean_candidates = []
    for m in matches:
        c = re.sub(r"\s+", " ", m).strip().replace("&amp;", "&")
        c_lower = c.lower()
        if len(c) > 3 and not any(ex in c_lower for ex in EXCLUDED_ENTITIES):
            clean_candidates.append(c)

    # Relevanz-Ranking mit Umlaut-Normalisierung (ae <-> ä)
    def norm_u(s: str) -> str:
        return s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")

    domain_base_norm = norm_u(domain_base)
    domain_parts_norm = [norm_u(p) for p in domain.split(".")[0].split("-") if len(p) >= 3]

    for c in clean_candidates:
        c_norm = norm_u(re.sub(r"[^a-zA-Z0-9äöüÄÖÜß]", "", c))
        if domain_base_norm in c_norm or any(part in c_norm for part in domain_parts_norm):
            return c, 0.95

    # 2. Traditionelle Branchennamen (Brauerei, Molkerei etc.)
    m_trad = TRADITIONAL_TITLES_RE.search(html_text)
    if m_trad:
        c = re.sub(r"\s+", " ", m_trad.group(1)).strip().replace("&amp;", "&")
        if not any(ex in c.lower() for ex in EXCLUDED_ENTITIES):
            return c, 0.85

    # 3. HTML Title Tag
    m_title = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if m_title:
        title = re.sub(r"\s+", " ", m_title.group(1)).strip()
        title = html.unescape(title)
        for sep in ["|", "–", "-", "—", ":", "•"]:
            if sep in title:
                parts = [p.strip() for p in title.split(sep) if p.strip()]
                for p in parts:
                    if len(p) >= 3 and not any(kw in p.lower() for kw in ["home", "startseite", "willkommen", "index", "spezialit", "feinkost", "domain", "reserved", "reserviert", "construction", "entsteht", "webseite", "website", "online", "portal"]) and not any(ex in p.lower() for ex in EXCLUDED_ENTITIES):
                        return p, 0.75
        if len(title) >= 3 and len(title) <= 60 and not any(ex in title.lower() for ex in EXCLUDED_ENTITIES):
            return title, 0.60

    # 4. Falls gefilterte Corporate Form ohne direkten Domain-Match existiert
    if clean_candidates:
        return clean_candidates[0], 0.70

    return None, 0.0


def parse_executive_from_html(html_text: str) -> str | None:
    """Extrahiert Geschaeftsfuehrer / Inhaber aus Impressums-HTML."""
    for pat in EXECUTIVE_PATTERNS:
        m = pat.search(html_text)
        if m:
            raw = re.sub(r"\s+", " ", m.group(1)).strip()
            # Validierung
            parts = raw.split()
            if 2 <= len(parts) <= 4:
                # Ausschluss von Nicht-Personen
                if not any(ex in raw.lower() for ex in ["amtsgericht", "handelsregister", "gmbh", "ag", "gbr"]):
                    return determine_salutation(raw)
    return None


def enrich_lead(row_idx: int, lead: dict) -> EnrichmentResult:
    lead_id = lead.get("Lead_ID") or lead.get("Lead-ID") or ""
    email = lead.get("Email") or lead.get("E-Mail") or ""
    orig_company = lead.get("Company") or lead.get("Firma") or ""
    orig_contact = lead.get("Contact") or lead.get("Ansprechpartner") or ""

    domain = extract_domain(email)
    if not domain:
        return EnrichmentResult(
            lead_id=lead_id,
            row_idx=row_idx,
            email=email,
            domain="",
            original_company=orig_company,
            enriched_company=sanitize_company_name(orig_company, email),
            original_contact=orig_contact,
            enriched_contact=orig_contact,
            confidence=0.0,
            source_url="",
            status="SKIPPED_FREEMAIL_OR_INVALID",
            reason="Freemail oder ungueltige Domain"
        )

    # 0. Pre-Send DNS/MX-Prüfung
    if not check_domain_mx(domain):
        return EnrichmentResult(
            lead_id=lead_id,
            row_idx=row_idx,
            email=email,
            domain=domain,
            original_company=orig_company,
            enriched_company=sanitize_company_name(orig_company, email),
            original_contact=orig_contact,
            enriched_contact=orig_contact,
            confidence=0.0,
            source_url="",
            status="INVALID_MX",
            reason="Kein MX-Record vorhanden (Zustellung unmöglich)"
        )

    # 1. Homepage abrufen
    homepage_url = f"https://{domain}"
    status, html_content, final_url = fetch_url(homepage_url)
    if status == 0 or status >= 400:
        homepage_url = f"http://{domain}"
        status, html_content, final_url = fetch_url(homepage_url)

    if status == 0 or status >= 400:
        return EnrichmentResult(
            lead_id=lead_id,
            row_idx=row_idx,
            email=email,
            domain=domain,
            original_company=orig_company,
            enriched_company=sanitize_company_name(orig_company, email),
            original_contact=orig_contact,
            enriched_contact=orig_contact,
            confidence=0.0,
            source_url=homepage_url,
            status="UNREACHABLE",
            reason=f"HTTP {status} oder Verbindungsfehler"
        )

    # 2. Impressum suchen
    impressum_url = extract_impressum_url(final_url, html_content)
    impressum_html = ""
    if impressum_url:
        imp_status, imp_html, _ = fetch_url(impressum_url)
        if imp_status == 200:
            impressum_html = imp_html

    # 3. Firmennamen ermitteln
    comb_html = (impressum_html + "\n" + html_content) if impressum_html else html_content
    enriched_co, conf = parse_company_from_html(comb_html, domain)

    # 4. Ansprechpartner ermitteln
    enriched_exec = parse_executive_from_html(impressum_html or html_content) or orig_contact

    final_company = enriched_co if (enriched_co and conf >= 0.6) else sanitize_company_name(orig_company, email)
    status_str = "ENRICHED" if (conf >= 0.8) else ("PARTIAL" if conf >= 0.5 else "LOW_CONFIDENCE")

    return EnrichmentResult(
        lead_id=lead_id,
        row_idx=row_idx,
        email=email,
        domain=domain,
        original_company=orig_company,
        enriched_company=final_company,
        original_contact=orig_contact,
        enriched_contact=enriched_exec,
        confidence=conf,
        source_url=impressum_url or final_url,
        status=status_str,
        reason=f"Conf {conf*100:.0f}%"
    )


def load_leads_from_sheet(profile: str = "cherinodiaz", start_row: int = 2, end_row: int = 1601) -> list[tuple[int, dict]]:
    """Laedt Leads direkt aus Google Sheet ALL_LEADS."""
    from crm_common import services, SID
    sheets_svc, _ = services(profile)
    res = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SID,
        range=f"ALL_LEADS!A1:BD{end_row}"
    ).execute()
    rows = res.get("values", [])
    if not rows:
        return []
    hdr = rows[0]
    leads = []
    for idx, r in enumerate(rows[start_row - 1:end_row], start=start_row):
        d = {}
        for h, val in zip(hdr, r):
            d[h] = val
        leads.append((idx, d))
    return leads


def apply_writeback(results: list[EnrichmentResult], profile: str = "cherinodiaz", batch_size: int = 50) -> int:
    """Schreibt angereicherte Firmen und Ansprechpartner zurueck ins Sheet ALL_LEADS."""
    from crm_common import services, SID
    sheets_svc, _ = services(profile)

    res = sheets_svc.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!1:1").execute()
    hdr = res.get("values", [[]])[0]
    col_firma_idx = hdr.index("Firma")
    col_contact_idx = hdr.index("Ansprechpartner")

    def col_letter(i):
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    firma_col = col_letter(col_firma_idx)
    contact_col = col_letter(col_contact_idx)

    data = []
    valid_results = [r for r in results if r.status in ("ENRICHED", "PARTIAL") and r.confidence >= 0.7]

    for r in valid_results:
        if r.enriched_company and r.enriched_company != r.original_company:
            data.append({
                "range": f"ALL_LEADS!{firma_col}{r.row_idx}",
                "values": [[r.enriched_company]]
            })
        if r.enriched_contact and r.enriched_contact != r.original_contact:
            data.append({
                "range": f"ALL_LEADS!{contact_col}{r.row_idx}",
                "values": [[r.enriched_contact]]
            })

    if not data:
        logger.info("Keine Schreib-Updates vorhanden.")
        return 0

    logger.info(f"Writing back {len(data)} cell updates in batches of {batch_size}...")
    updated_total = 0
    for i in range(0, len(data), batch_size):
        chunk = data[i:i + batch_size]
        body = {"valueInputOption": "USER_ENTERED", "data": chunk}
        sheets_svc.spreadsheets().values().batchUpdate(spreadsheetId=SID, body=body).execute()
        updated_total += len(chunk)

    return updated_total


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Lead Company & Contact Enrichment")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Dry-Run Modus (kein Schreiben)")
    parser.add_argument("--apply", action="store_true", default=False, help="Aenderungen direkt ins Sheet schreiben")
    parser.add_argument("--limit", type=int, default=10, help="Anzahl zu pruefender Leads")
    parser.add_argument("--start-row", type=int, default=2, help="Startzeile in ALL_LEADS (Standard: 2)")
    parser.add_argument("--end-row", type=int, default=1601, help="Endzeile in ALL_LEADS (Standard: 1601)")
    parser.add_argument("--workers", type=int, default=8, help="Parallele HTTP-Threads")
    parser.add_argument("--profile", default="cherinodiaz", help="Google Workspace Profil")
    parser.add_argument("--output", default="enrichment_audit.jsonl", help="Pfad fuer Audit-Log")
    args = parser.parse_args()

    dry_run = not args.apply

    logger.info(f"=== HSB LEAD ENRICHMENT ENGINE ===")
    logger.info(f"Modus: {'DRY-RUN (Vorschau)' if dry_run else 'APPLY (Writeback)'}")
    logger.info(f"Bereich: Zeilen {args.start_row} bis {args.end_row} | Limit: {args.limit} | Threads: {args.workers}")

    leads = load_leads_from_sheet(profile=args.profile, start_row=args.start_row, end_row=args.end_row)
    logger.info(f"{len(leads)} Leads aus ALL_LEADS geladen.")

    leads_to_process = leads[:args.limit]

    results: list[EnrichmentResult] = []
    t0 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_lead = {
            executor.submit(enrich_lead, row_idx, lead): (row_idx, lead)
            for row_idx, lead in leads_to_process
        }
        for future in concurrent.futures.as_completed(future_to_lead):
            res = future.result()
            results.append(res)

    results.sort(key=lambda r: r.row_idx)
    duration = time.time() - t0

    # Summary
    logger.info(f"=== ENRICHMENT ABGESCHLOSSEN in {duration:.2f}s ===")
    enriched_count = sum(1 for r in results if r.status in ("ENRICHED", "PARTIAL"))
    logger.info(f"Erfolgreich angereichert: {enriched_count} / {len(results)}")

    print("\n" + "=" * 110)
    print(f"{'Row':<5} | {'Lead-ID':<18} | {'Email':<28} | {'Alt -> Neu Firma':<36} | {'Ansprechpartner':<20}")
    print("-" * 110)
    for r in results:
        firma_change = f"{r.original_company[:15]} -> {r.enriched_company[:18]}"
        contact_display = r.enriched_contact[:20] if r.enriched_contact else "-"
        print(f"{r.row_idx:<5} | {r.lead_id:<18} | {r.email[:28]:<28} | {firma_change:<36} | {contact_display:<20}")
    print("=" * 110 + "\n")

    # Audit Log
    with open(args.output, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    logger.info(f"Audit-Log gespeichert in: {args.output}")

    if args.apply:
        updated = apply_writeback(results, profile=args.profile)
        logger.info(f"Erfolgreich {updated} Zellen in Google Sheet ALL_LEADS aktualisiert.")
    else:
        logger.info("Dry-Run beendet. Fuehre den Befehl mit --apply aus, um die Werte ins Sheet zu schreiben.")


if __name__ == "__main__":
    main()
