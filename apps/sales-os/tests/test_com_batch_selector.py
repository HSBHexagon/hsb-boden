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
    for row in sample_leads:
        row.update({"Legal_Basis": "OPT_IN", "Legal_Evidence": "Consent record TEST-2026", "Legal_Evidence_At": "2026-09-01T10:00:00Z"})
    selected_joel = select_com_eligible_leads(sample_leads, owner="JOEL", limit=10)
    assert len(selected_joel) == 1
    assert selected_joel[0]["Lead_ID"] == "L-1"

    selected_jordi = select_com_eligible_leads(sample_leads, owner="JORDI", limit=10)
    assert len(selected_jordi) == 1
    assert selected_jordi[0]["Lead_ID"] == "L-4"


def test_select_com_eligible_leads_contract_approved():
    """SSOT: CONTRACT_APPROVED and OWNER_APPROVED leads with Versandfreigabe=yes are eligible without individual Legal_Evidence."""
    sample = [
        {"Lead_ID": "C-1", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "contract1@test.de", "Legal_Basis": "CONTRACT_APPROVED"},
        {"Lead_ID": "C-2", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "contract2@test.de", "Legal_Basis": "OWNER_APPROVED"},
        {"Lead_ID": "C-3", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "contract3@test.de", "Legal_Basis": ""}, # defaults to contract approval
        {"Lead_ID": "C-4", "Owner": "Joel Cherino", "Versandfreigabe": "no", "Email": "contract4@test.de", "Legal_Basis": "CONTRACT_APPROVED"}, # unapproved
        {"Lead_ID": "C-5", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "contract5@test.de", "Legal_Basis": "CONTRACT_APPROVED", "Opt_Out": "yes"}, # opt-out
    ]
    selected = select_com_eligible_leads(sample, owner="JOEL", limit=10)
    selected_ids = [s["Lead_ID"] for s in selected]
    assert "C-1" in selected_ids
    assert "C-2" in selected_ids
    assert "C-3" in selected_ids
    assert "C-4" not in selected_ids
    assert "C-5" not in selected_ids

def test_select_com_eligible_leads_domain_and_company_suppression_magnus():
    """Verify that suppression on one lead (e.g. Magnus) shields all other contacts of the same company/domain."""
    sample = [
        # Lead 1: Magnus registered customer, explicitly suppressed
        {
            "Lead_ID": "HSB-20260708-00226", "Owner": "Joel Cherino", "Versandfreigabe": "no",
            "Firma": "Magnus Mineralbrunnen GmbH", "Email": "info@magnus.de",
            "Suppressed": "yes", "Legal_Basis": "CONTRACT_APPROVED"
        },
        # Lead 2: Same company, different project email, unsuppressed row
        {
            "Lead_ID": "HSB-20260708-09999", "Owner": "Joel Cherino", "Versandfreigabe": "yes",
            "Firma": "Magnus Mineralbrunnen", "Email": "projekt@magnus.de",
            "Suppressed": "no", "Legal_Basis": "CONTRACT_APPROVED"
        },
        # Lead 3: Unrelated legitimate prospect
        {
            "Lead_ID": "HSB-20260708-05555", "Owner": "Joel Cherino", "Versandfreigabe": "yes",
            "Firma": "Brauerei Mueller GmbH", "Email": "kontakt@brauerei-mueller.de",
            "Suppressed": "no", "Legal_Basis": "CONTRACT_APPROVED"
        }
    ]
    selected = select_com_eligible_leads(sample, owner="JOEL", limit=10)
    selected_ids = [s["Lead_ID"] for s in selected]

    # Both Lead 1 and Lead 2 must be blocked!
    assert "HSB-20260708-00226" not in selected_ids
    assert "HSB-20260708-09999" not in selected_ids

    # Unrelated lead must pass
    assert "HSB-20260708-05555" in selected_ids
