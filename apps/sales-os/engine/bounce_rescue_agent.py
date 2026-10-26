#!/usr/bin/env python3
"""
HSB Sales OS - Autonomous Bounce Rescue Agent.
Analysiert unzustellbare Leads (Hard Bounces / 550 User Unknown), durchsucht die
Unternehmens-Website (Impressum, Kontakt, Homepage) nach alternativen, funktionierenden
E-Mail-Adressen (z.B. info@, kontakt@, zentrale@), validiert MX-Records und legt gerettete
Kontakte zur Freigabe im SSOT vor.

Sicherheits-Invariante: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Reine Recherche & CRM-Update).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
import html
import json
import logging
import re
import socket
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from enrich_company_names import check_domain_mx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("bounce_rescue_agent")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0

EMAIL_EXTRACT_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
GENERIC_IGNORE_DOMAINS = {"wix.com", "jimdo.com", "wordpress.com", "squarespace.com", "cloudflare.com", "google.com", "schema.org"}
GENERIC_IGNORE_PREFIXES = {"webmaster", "postmaster", "hostmaster", "noreply", "no-reply", "datenschutz", "privacy", "dsgvo"}


@dataclass
class RescueResult:
    status: str  # SUCCESS, NO_CANDIDATE, MX_FAILED, ERROR
    failed_email: str
    rescued_email: Optional[str] = None
    company_name: str = ""
    domain: str = ""
    source_url: Optional[str] = None
    confidence: float = 0.0
    notes: str = ""


class BounceRescueAgent:
    """Intelligenter Agent zur Rettung gebouncter Leads via Web & Impressum Scraping."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
        }

    def _fetch_url_content(self, url: str) -> Optional[str]:
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    return None
                raw = resp.read()
                return raw.decode("utf-8", errors="ignore")
        except Exception:
            return None

    def _derive_domain(self, website: str, email: str) -> str:
        if website and "." in website:
            clean = re.sub(r"^https?://", "", website.strip(), flags=re.IGNORECASE)
            clean = clean.split("/")[0].split("?")[0].strip()
            if clean.startswith("www."):
                clean = clean[4:]
            if clean:
                return clean.lower()
        if email and "@" in email:
            dom = email.split("@")[-1].strip().lower()
            return dom
        return ""

    def search_alternative_emails(self, domain: str) -> List[Tuple[str, str, float]]:
        """
        Sucht auf der Domain (Homepage, /impressum, /kontakt) nach alternativen E-Mails.
        Gibt eine Liste von (email, quelle_url, confidence) sortiert nach Score zurück.
        """
        if not domain or any(d in domain for d in ["gmail.com", "gmx.de", "web.de", "t-online.de", "outlook.com"]):
            return []

        base_urls = [
            f"https://www.{domain}",
            f"https://{domain}",
            f"http://www.{domain}",
            f"http://{domain}",
        ]
        subpaths = ["/impressum", "/kontakt", "/de/impressum", "/de/kontakt", ""]
        visited = set()
        candidates: Dict[str, Tuple[str, float]] = {}

        for base in base_urls[:2]:
            for path in subpaths:
                target = f"{base}{path}"
                if target in visited:
                    continue
                visited.add(target)
                html_text = self._fetch_url_content(target)
                if not html_text:
                    continue

                # Extrahiere mailto: Links und Plain-Text Mails
                matches = EMAIL_EXTRACT_RE.findall(html_text)
                for raw_em in matches:
                    em = raw_em.strip().lower()
                    if not em or "@" not in em:
                        continue
                    prefix, em_dom = em.split("@", 1)
                    if em_dom in GENERIC_IGNORE_DOMAINS or any(p in prefix for p in GENERIC_IGNORE_PREFIXES):
                        continue

                    # Prioritäts-Scoring
                    score = 0.50
                    if em_dom == domain or em_dom.endswith("." + domain):
                        score += 0.20
                        if prefix in ("info", "kontakt", "contact", "zentrale", "empfang"):
                            score += 0.25
                        elif prefix in ("geschaeftsfuehrung", "leitung", "management", "vertrieb", "sales", "einkauf"):
                            score += 0.20
                        else:
                            score += 0.10
                    elif "impressum" in target or "kontakt" in target:
                        score += 0.15

                    if em not in candidates or score > candidates[em][1]:
                        candidates[em] = (target, round(min(score, 0.98), 2))

                # Wenn hochqualitative info@ oder kontakt@ gefunden, Abbruch
                if any(candidates.get(f"{p}@{domain}") for p in ["info", "kontakt"]):
                    break
            if candidates:
                break

        sorted_cands = sorted([(em, src, score) for em, (src, score) in candidates.items()], key=lambda x: x[2], reverse=True)
        return sorted_cands

    def rescue_lead(self, lead: Dict[str, Any], failed_email: Optional[str] = None) -> RescueResult:
        """Führt den vollen Rettungs-Workflow für einen Lead durch."""
        raw_em = (failed_email or lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
        company = str(lead.get("Firma") or lead.get("Company") or "").strip()
        website = str(lead.get("Website") or lead.get("Web") or "").strip()

        domain = self._derive_domain(website, raw_em)
        if not domain:
            return RescueResult(
                status="NO_CANDIDATE",
                failed_email=raw_em,
                company_name=company,
                notes="Keine Domain ermittelbar"
            )

        cands = self.search_alternative_emails(domain)
        # Filtere die fehlgeschlagene E-Mail strikt heraus
        viable = [c for c in cands if c[0] != raw_em]

        if not viable:
            return RescueResult(
                status="NO_CANDIDATE",
                failed_email=raw_em,
                company_name=company,
                domain=domain,
                notes="Keine alternative E-Mail im Impressum/Web gefunden"
            )

        # Prüfe MX-Record des besten Kandidaten
        for cand_em, src, score in viable:
            mx_domain = cand_em.split("@")[-1]
            if check_domain_mx(mx_domain):
                return RescueResult(
                    status="SUCCESS",
                    failed_email=raw_em,
                    rescued_email=cand_em,
                    company_name=company,
                    domain=domain,
                    source_url=src,
                    confidence=score,
                    notes=f"Alternative E-Mail auf {src} gefunden und MX verifiziert."
                )

        return RescueResult(
            status="MX_FAILED",
            failed_email=raw_em,
            company_name=company,
            domain=domain,
            notes="Alternative Adressen gefunden, aber MX-Prüfung fehlgeschlagen."
        )


def main():
    agent = BounceRescueAgent()
    test_lead = {
        "Firma": "HSB Hexagon Test",
        "Website": "https://www.hsb-boden.de",
        "E-Mail": "ungueltig-12345@hsb-boden.de"
    }
    logger.info("Teste Bounce Rescue Agent...")
    res = agent.rescue_lead(test_lead, failed_email="ungueltig-12345@hsb-boden.de")
    logger.info(f"Ergebnis: Status={res.status} | Gerettet: {res.rescued_email} | Quelle: {res.source_url} | Score={res.confidence}")


if __name__ == "__main__":
    main()
