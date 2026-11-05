"""Workflow-Vertrag: Modus audit endet nur nach bestandener Tiefenprüfung grün."""
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[3] / '.github/workflows/sales-os-safety.yml').read_text(encoding='utf-8')


def test_audit_mode_runs_verifier():
    audit = WORKFLOW.index('sales_reconciliation.py --output "$RUNNER_TEMP/hsb-reconciliation"')
    verify = WORKFLOW.index('draft_verify.py --audit-dir "$RUNNER_TEMP/hsb-reconciliation"')
    assert audit < verify
    step = WORKFLOW[WORKFLOW.rindex('- name:', 0, verify):verify]
    assert "if: inputs.mode == 'audit'" in step


def test_chain_start_removed():
    assert '55 1 5 11 *' not in WORKFLOW
    assert 'chain-start' not in WORKFLOW
