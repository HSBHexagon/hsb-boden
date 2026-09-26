from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from run_com_batch import run_com_batch_in_memory


def test_run_com_batch_dry_run_produces_draft_manifest():
    mock_leads = [
        {
            "row_idx": 10,
            "Lead_ID": "HSB-TEST-001",
            "Owner": "Joel Cherino",
            "Versandfreigabe": "yes",
            "Email": "info@test-bau.de",
            "Firmenname": "Test Bau GmbH",
            "Anrede": "Herr",
            "Nachname": "Mustermann"
        }
    ]
    res = run_com_batch_in_memory(mock_leads, owner="JOEL", limit=5, dry_run=True)
    assert res["status"] == "SUCCESS_DRY_RUN"
    assert res["selected_count"] == 1
    assert "HSB-HEXAGON-Industrieboeden-Flyer.pdf" in res["manifest"][0]["flyer_filename"]
    assert "j-cherino@hsb-boden.com" in res["manifest"][0]["sender"]
    assert res["manifest"][0]["status"] == "DRY_RUN"


def test_run_com_batch_no_eligible_leads():
    res = run_com_batch_in_memory([], owner="JOEL", limit=5, dry_run=True)
    assert res["status"] == "NO_ELIGIBLE_LEADS"
    assert res["selected_count"] == 0
