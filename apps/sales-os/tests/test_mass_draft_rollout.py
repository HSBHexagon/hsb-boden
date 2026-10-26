import pytest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from run_mass_draft_rollout import build_draft_payload, select_untouched_candidates, REAL_EXTERNAL_PROSPECT_SEND_COUNT

def test_zero_send_invariant():
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0

def test_build_draft_payload():
    lead = {
        "Lead_ID": "HSB-TEST-001",
        "E-Mail": "kontakt@brauerei-test.de",
        "Firma": "Brauerei Test GmbH",
        "Ansprechpartner": "Herr Müller",
        "_row": 15
    }
    payload = build_draft_payload("JOEL", lead)
    assert payload["owner"] == "JOEL"
    assert payload["lead_id"] == "HSB-TEST-001"
    assert payload["to_email"] == "kontakt@brauerei-test.de"
    assert "Brauerei Test" in payload["subject"]
    assert "www.hsb-boden.de/flyer" in payload["body_html"]
    assert "Hier abmelden" in payload["body_html"]
    assert payload["flyer_path"] is None

def test_select_untouched_candidates_filtering():
    leads = [
        {"Email": "sent@test.de", "Send_Status": "sent", "_row": 10},
        {"Email": "optout@test.de", "Opt_Out": "yes", "_row": 11},
        {"Email": "forensic@test.de", "_row": 12},
        {"Email": "existing_draft@test.de", "_row": 13},
        {"Email": "fresh_joel@test.de", "_row": 14},
        {"Email": "fresh_jordi@test.de", "_row": 3300},
    ]
    forensic = {"forensic@test.de"}
    existing = {"JOEL": {"existing_draft@test.de"}, "JORDI": set()}

    cand = select_untouched_candidates(leads, forensic, existing)
    assert len(cand["JOEL"]) == 1
    assert cand["JOEL"][0]["Email"] == "fresh_joel@test.de"
    assert len(cand["JORDI"]) == 1
    assert cand["JORDI"][0]["Email"] == "fresh_jordi@test.de"
