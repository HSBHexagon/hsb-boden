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


def _archive_job():
    start = WORKFLOW.index('\n  archive-purge:\n')
    end = WORKFLOW.find('\n  # ', start + 1)
    return WORKFLOW[start:end if end != -1 else None]


def test_archive_purge_applies_only_on_main_with_typed_confirmation():
    job = _archive_job()
    assert 'github.event_name == \'workflow_dispatch\' && startsWith(inputs.mode, \'archive-purge\')' in job
    assert 'group: hsb-sales-os-runtime' in job
    assert '[ "$CONFIRM" != "ARCHIV-LEEREN" ]' in job and '[ "$GITHUB_REF" != "refs/heads/main" ]' in job
    assert job.count('archive-purge --apply') == 1
    assert job.index('release-stale-lock --apply') < job.index('archive-purge --apply')
    assert "HSB_CUSTOMER_SEND_ENABLED: 'no'" in job


def test_archive_modes_do_not_trigger_other_live_jobs():
    start = WORKFLOW.index('\n  live-readonly-and-inbound:\n')
    assert "!startsWith(inputs.mode, 'archive-purge')" in WORKFLOW[start:WORKFLOW.index('needs:', start)]
