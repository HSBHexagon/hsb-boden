from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from com_batch_selector import select_com_eligible_leads


def test_select_com_eligible_leads_filters_correctly():
    sample_leads = [
        {"Lead_ID": "L-1", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "a@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-2", "Owner": "Joel Cherino", "Versandfreigabe": "no", "Email": "b@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-3", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "c@test.de", "Drafted_At": "2026-09-20"},
        {"Lead_ID": "L-4", "Owner": "Jordie Post", "Versandfreigabe": "yes", "Email": "d@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-5", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "e@test.de", "Drafted_At": "", "Opt_Out": "yes"},
        {"Lead_ID": "L-6", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "a@test.de", "Drafted_At": ""}, # dupe
        {"Lead_ID": "L-7", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "invalid-no-at", "Drafted_At": ""},
    ]
    selected_joel = select_com_eligible_leads(sample_leads, owner="JOEL", limit=10)
    assert len(selected_joel) == 1
    assert selected_joel[0]["Lead_ID"] == "L-1"

    selected_jordi = select_com_eligible_leads(sample_leads, owner="JORDI", limit=10)
    assert len(selected_jordi) == 1
    assert selected_jordi[0]["Lead_ID"] == "L-4"
