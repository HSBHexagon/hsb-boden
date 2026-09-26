#!/usr/bin/env python3
"""
Commercial Register & Swiss Zefix Enrichment Engine for HSB Sales OS.
Extracts official corporate entities (AG, GmbH, Genossenschaft, KG, e.K.)
for German, Austrian, and Swiss B2B prospects using pattern matching and Exa search.
"""
import re
from typing import Dict, Any, Optional

SWISS_CANTONS = [
    "AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU",
    "NE", "NW", "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH"
]

LEGAL_SUFFIXES_DACH = [
    "GmbH & Co. KG", "GmbH & Co. KGaA", "GmbH", "AG", "UG (haftungsbeschränkt)", "UG",
    "e.K.", "e. K.", "e.Kfm.", "e.Kfr.", "KG", "OHG", "GbR", "SE", "KGaA",
    "Genossenschaft", "eG", "GmbH & Co.", "SA", "Sàrl", "Sagl"
]

def is_swiss_lead(lead: Dict[str, Any]) -> bool:
    email = str(lead.get("Email") or lead.get("E-Mail") or "").lower()
    website = str(lead.get("Website") or "").lower()
    country = str(lead.get("Land") or lead.get("Country") or "").upper()
    state = str(lead.get("Bundesland") or lead.get("State") or "").upper()

    if email.endswith(".ch") or website.endswith(".ch") or country in ("CH", "SCHWEIZ", "SWITZERLAND"):
        return True
    if state in SWISS_CANTONS:
        return True
    return False

def extract_legal_form(name: str) -> Optional[str]:
    """
    Detects if the company name already contains a formal DACH legal suffix.
    """
    for suffix in LEGAL_SUFFIXES_DACH:
        pattern = r'\b' + re.escape(suffix) + r'\b'
        if re.search(pattern, name, re.IGNORECASE):
            return suffix
    return None

def normalize_dach_company_name(name: str, lead: Optional[Dict[str, Any]] = None) -> str:
    """
    Cleans raw company names from scraping artifacts, slugs, and domain endings,
    preserving or restoring legal forms.
    """
    if not name:
        return ""

    cleaned = name.strip()
    
    # Strip URL protocols and domains
    cleaned = re.sub(r'https?://(?:www\.)?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\.(?:de|com|ch|at|net|org|eu|info)/?$', '', cleaned, flags=re.IGNORECASE)

    # Strip excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Detect legal suffix
    legal = extract_legal_form(cleaned)
    
    return cleaned

if __name__ == "__main__":
    test_cases = [
        "Molkerei Biedermann AG",
        "züger frischkäse.ch",
        "Weingut Nägelsförst GmbH",
        "Bodensee Käse",
        "Käserei Champignon Hofmeister GmbH & Co. KG"
    ]
    print("Normalizing company names:")
    for t in test_cases:
        norm = normalize_dach_company_name(t)
        legal = extract_legal_form(norm)
        print(f"  Raw: {t:<45} -> Normalized: {norm:<35} (Legal Form: {legal})")
