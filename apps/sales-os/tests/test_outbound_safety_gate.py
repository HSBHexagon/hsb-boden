"""Regression: CRM-Zustimmung ist kein Nebeneffekt einer Draft-Erstellung."""
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

from hsb_core import check_eligibility
from run_dual_outreach_batch import select_send_candidates


def _crm_lead(**overrides):
    data = {
        "Lead-ID": "TEST-2026-01",
        "Verantwortlicher": "Jordie Post",
        "E-Mail": "probe@beispiel-industrie.invalid",
        "Firma": "Beispiel Industrie GmbH",
        "Legal_Basis": "OPT_IN",
        "Legal_Evidence": "consent-fixture-123",
        "Legal_Evidence_At": "2026-10-20T10:00:00Z",
        "Versandfreigabe": "yes",
        "Suppressed": "no",
        "Opt-out-Status": "no",
        "Send_Status": "drafted",
        "Batch_Status": "DRAFTED_COM_2026",
    }
    data.update(overrides)
    return data


def test_live_crm_column_names_are_supported():
    assert check_eligibility(_crm_lead()).eligible


def test_optout_and_missing_approval_block():
    assert not check_eligibility(_crm_lead(**{"Opt-out-Status": "yes"})).eligible
    assert not check_eligibility(_crm_lead(Versandfreigabe="no")).eligible


def test_rollout_created_contract_approved_is_not_implicit_legal_authorization():
    assert not check_eligibility(_crm_lead(Legal_Basis="CONTRACT_APPROVED")).eligible


def test_dual_dispatch_filters_bad_permissions_and_duplicate_emails(monkeypatch):
    monkeypatch.setattr("run_dual_outreach_batch.check_domain_mx", lambda _: True)
    leads = [
        _crm_lead(),
        _crm_lead(**{"Lead-ID": "TEST-2026-02"}),
        _crm_lead(**{"Lead-ID": "TEST-2026-03", "E-Mail": "other@beispiel.invalid", "Legal_Basis": "BLOCKED"}),
        _crm_lead(**{"Lead-ID": "TEST-2026-04", "E-Mail": "optout@beispiel.invalid", "Opt-out-Status": "yes"}),
    ]
    actual = select_send_candidates(leads, "JORDI", 10, set())
    assert len(actual) == 1
    assert actual[0]["Lead-ID"] == "TEST-2026-01"


def test_mass_draft_rollout_never_sets_legal_approval():
    for name in ("run_mass_draft_rollout.py", "run_rollout_500_com.py"):
        code = (ENGINE / name).read_text()
        assert '"Z": "yes"' not in code
        assert '"AS": "CONTRACT_APPROVED"' not in code
