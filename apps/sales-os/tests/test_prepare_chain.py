"""Lauf-Kette: Folgelauf nur bei erschöpftem Zeitbudget und echtem Fortschritt; PR-Tests warten nicht auf Live-Läufe."""
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = (REPO / '.github/workflows/sales-os-safety.yml').read_text(encoding='utf-8')

FAKE_CLI = """import json, os, sys
if 'upgrade-drafts' in sys.argv:
    owner = sys.argv[sys.argv.index('--owner') + 1]
    print(json.dumps(json.loads(os.environ['FAKE_TRANCHE'])[owner]))
else:
    print('{}')
"""
FAKE_AUDIT = """import json, pathlib, sys
out = pathlib.Path(sys.argv[sys.argv.index('--output') + 1]); out.mkdir(parents=True, exist_ok=True)
(out / 'summary.json').write_text(json.dumps({'ok': True})); print('{}')
"""
# Liefert START und die erste Budgetprüfung innerhalb des Budgets, danach eine Stunde später.
FAKE_DATE = """#!/bin/sh
case "$1" in
  +%s) n=$(cat "$DATE_COUNTER" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$DATE_COUNTER"
       if [ "$n" -le "$DATE_FRESH_CALLS" ]; then echo 1000; else echo 4600; fi;;
  *) echo 20261104-000000;;
esac
"""


def lauf(tmp_path, tranche, budget='0', fresh=2):
    base = tmp_path / 'repo'
    (base / 'apps/sales-os/bin').mkdir(parents=True)
    (base / 'apps/sales-os/engine').mkdir(parents=True)
    shutil.copy(REPO / 'apps/sales-os/bin/postfach-lauf.sh', base / 'apps/sales-os/bin/')
    (base / 'apps/sales-os/engine/hsb_cli.py').write_text(FAKE_CLI)
    (base / 'apps/sales-os/engine/sales_reconciliation.py').write_text(FAKE_AUDIT)
    shim = tmp_path / 'shim'
    shim.mkdir()
    (shim / 'date').write_text(FAKE_DATE)
    (shim / 'date').chmod(stat.S_IRWXU)
    output = tmp_path / 'github_output'
    output.write_text('')
    env = {'PATH': f'{shim}:{os.environ["PATH"]}', 'HOME': str(tmp_path), 'HSB_RUN_DIR': str(tmp_path),
           'HSB_MAILBOX_CONFIG_JSON': '{}', 'HSB_GOOGLE_AUTHORIZED_USER_JSON': '{}', 'HSB_RUN_BUDGET_MIN': budget,
           'FAKE_TRANCHE': json.dumps(tranche), 'GITHUB_OUTPUT': str(output),
           'DATE_COUNTER': str(tmp_path / 'counter'), 'DATE_FRESH_CALLS': str(fresh)}
    done = subprocess.run(['bash', str(base / 'apps/sales-os/bin/postfach-lauf.sh'), '--apply'], env=env,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout, output.read_text()


def test_budget_reached_with_progress_asks_for_next_run(tmp_path):
    out, github_output = lauf(tmp_path, {'JOEL': {'selected': 100, 'crm_updated': 100}, 'JORDI': {'selected': 100, 'crm_updated': 100}}, budget='1')
    assert 'more=yes' in github_output and 'Zeitbudget erreicht' in out


def test_everything_done_ends_the_chain(tmp_path):
    _, github_output = lauf(tmp_path, {'JOEL': {'selected': 0}, 'JORDI': {'selected': 0}})
    assert 'more=no' in github_output


def test_budget_reached_without_progress_stops_the_chain(tmp_path):
    # Stop-on-drift: Ein Lauf, der nichts erneuert hat, startet keinen Nachfolger.
    _, github_output = lauf(tmp_path, {'JOEL': {'selected': 0}, 'JORDI': {'selected': 0}}, budget='1', fresh=1)
    assert 'more=no' in github_output


def test_tranche_without_progress_ends_this_mailbox_but_not_the_other(tmp_path):
    out, github_output = lauf(tmp_path, {'JOEL': {'selected': 100, 'crm_updated': 0}, 'JORDI': {'selected': 0}})
    assert 'more=no' in github_output
    assert '[JOEL] Tranche 1: kein Fortschritt' in out and '[JORDI] Tranche 1: 0 erneuert' in out


def test_chain_is_bounded_and_can_only_prepare():
    assert 'inputs.chain < 8' in WORKFLOW
    assert WORKFLOW.count('gh workflow run') == 1
    for line in WORKFLOW.splitlines():
        if 'gh workflow run' in line:
            assert '-f mode=prepare-drafts ' in line and '--ref main' in line


def test_pr_tests_do_not_wait_behind_live_runs():
    assert '\nconcurrency:' not in WORKFLOW
    rest = WORKFLOW.split('\n  tests:\n')[1]
    tests_job = rest.split('\n  runtime-gate:\n')[0]
    assert 'concurrency' not in tests_job
    assert WORKFLOW.count('group: hsb-sales-os-runtime') == 5
    assert WORKFLOW.count('queue: max') == 5


def test_cron_cannot_replace_a_waiting_prepare_run():
    # Je Gruppe wartet nur ein Job; ein stündlicher Cron würde den wartenden Folgelauf abbrechen.
    assert "needs.runtime-gate.outputs.busy != 'yes'" in WORKFLOW
    assert '--event workflow_dispatch' in WORKFLOW


def test_postfach_lauf_runs_verifier_and_fills_missing_drafts(tmp_path):
    out, _ = lauf(tmp_path, {'JOEL': {'selected': 0}, 'JORDI': {'selected': 0}})
    assert out.index('verify-audit --audit-dir') < out.index('refresh-signature --audit-dir')
    assert out.index('upgrade-drafts --owner JORDI') < out.index('fill-missing-drafts --audit-dir')
    assert out.index('fill-missing-drafts --audit-dir') < out.rindex('verify-audit --audit-dir')

def test_fill_missing_cloud_repair_is_manual_serial_and_never_sends():
    job = WORKFLOW.split('\\n  fill-missing:\\n', 1)[1].split('\\n  # Entwürfe-Archiv-v1', 1)[0]
    assert "github.event_name == 'workflow_dispatch'" in job
    assert "github.ref == 'refs/heads/main'" in job
    assert 'needs: tests' in job
    assert "HSB_CUSTOMER_SEND_ENABLED: 'no'" in job
    assert "HSB_INTERNAL_TEST_SEND_ENABLED: 'no'" in job
    assert 'group: hsb-sales-os-runtime' in job
    assert 'queue: max' in job
    assert 'cancel-in-progress: false' in job
    assert "if [ \"$MODE\" = 'fill-missing' ]; then" in job
    assert 'fill-missing-drafts --audit-dir "$BEFORE" --apply' in job
    assert 'draft_verify.py --audit-dir "$AFTER"' in job
    assert "MAIN_ONLY_DRAFT_MUTATION" in job
