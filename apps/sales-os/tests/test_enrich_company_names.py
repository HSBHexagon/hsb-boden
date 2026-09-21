#!/usr/bin/env python3
"""
Unit tests for the Lead Company and Contact Enrichment Engine.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from enrich_company_names import (
    extract_domain,
    determine_salutation,
    parse_company_from_html,
    parse_executive_from_html,
    enrich_lead,
)


def test_extract_domain_valid():
    assert extract_domain("info@brauerei-paeffgen.de") == "brauerei-paeffgen.de"
    assert extract_domain("kontakt@bodensee-kaese.ch") == "bodensee-kaese.ch"


def test_extract_domain_freemail_returns_none():
    assert extract_domain("r.paeffgen@t-online.de") is None
    assert extract_domain("max.mustermann@gmx.de") is None
    assert extract_domain("chef@web.de") is None
    assert extract_domain("contact@gmail.com") is None


def test_determine_salutation():
    assert determine_salutation("Jürgen Müller") == "Herr Jürgen Müller"
    assert determine_salutation("Klaus Dieter") == "Herr Klaus Dieter"
    assert determine_salutation("Monika Schmidt") == "Frau Monika Schmidt"
    assert determine_salutation("Silke Maier") == "Frau Silke Maier"
    assert determine_salutation("Robin Schneider") == "Robin Schneider"


def test_parse_company_legal_forms():
    html_sample = "<div>Impressum: Bodensee Käse AG, Hauptstr. 12, 9000 St. Gallen</div>"
    company, conf = parse_company_from_html(html_sample, "bodensee-kaese.ch")
    assert company == "Bodensee Käse AG"
    assert conf >= 0.9

    html_gmbh_co_kg = "<div>Angaben gemäß § 5 TMG: Brauerei Päffgen GmbH & Co. KG, Köln</div>"
    company2, conf2 = parse_company_from_html(html_gmbh_co_kg, "paeffgen.de")
    assert "Brauerei Päffgen GmbH & Co. KG" in company2
    assert conf2 >= 0.9


def test_parse_executive():
    html_sample = "<p>Geschäftsführer: Dr. Markus Weber</p>"
    exec_name = parse_executive_from_html(html_sample)
    assert exec_name == "Herr Dr. Markus Weber" or "Markus Weber" in exec_name

    html_inhaber = "<p>Inhaber: Monika Schneider</p>"
    exec_name2 = parse_executive_from_html(html_inhaber)
    assert exec_name2 == "Frau Monika Schneider"


def test_enrich_lead_freemail_skipped():
    lead = {
        "Lead_ID": "TEST-01",
        "Email": "test@t-online.de",
        "Company": "T-Online",
        "Contact": ""
    }
    res = enrich_lead(17, lead)
    assert res.status == "SKIPPED_FREEMAIL_OR_INVALID"
    assert res.enriched_company == "Ihr Unternehmen"
