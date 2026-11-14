"""
Tests für die n8n-Orchestrierung der bestehenden HSB Sales-OS Versand-Engine
gemäß Betreiberauftrag vom 14.11.2026:
- Dry-Run mit 0 Kundenversand
- Idempotente Wiederholung über Job-Key
- Exklusives Lock (Fail-Closed bei parallelem Lauf)
- Opt-out-/Bounce-Fail-Close Gate
- Quoten-/Budget-Gate & Provider-Backoff
- Reconciliation & strukturierte Alerts im revisionssicheren Journal
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))


def test_dry_run_preflight_sends_zero_customer_emails(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=25,
        allow_live_send=False,
    )
    result = run_orchestrated_action(
        mode="preflight",
        count=5,
        job_key="preflight-test-001",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 0, "bounces_unsuppressed": 0, "crm_sent": 1886, "mailbox_sent": 1886},
        dry_run_executor=lambda count: {"selected": {"JOEL": count, "JORDI": count}, "customer_emails_sent": 0},
    )
    assert result["status"] == "DRY_RUN_COMPLETED"
    assert result["customer_emails_sent"] == 0
    assert result["gate_status"] == "GREEN"


def test_idempotent_job_key_prevents_duplicate_execution(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    calls = []
    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=25,
        allow_live_send=True,
    )
    metrics = {"optouts_unsuppressed": 0, "bounces_unsuppressed": 0, "crm_sent": 1886, "mailbox_sent": 1886}

    first = run_orchestrated_action(
        mode="preflight",
        count=5,
        job_key="idempotent-key-42",
        config=cfg,
        leitstand_metrics=metrics,
        dry_run_executor=lambda c: (calls.append(c) or {"customer_emails_sent": 0}),
    )
    second = run_orchestrated_action(
        mode="preflight",
        count=5,
        job_key="idempotent-key-42",
        config=cfg,
        leitstand_metrics=metrics,
        dry_run_executor=lambda c: (calls.append(c) or {"customer_emails_sent": 0}),
    )

    assert first["status"] == "DRY_RUN_COMPLETED"
    assert second["status"] == "DUPLICATE_JOB_KEY_SKIPPED"
    assert second["customer_emails_sent"] == 0
    assert len(calls) == 1


def test_optout_or_bounce_unsuppressed_triggers_fail_close_and_alert(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=25,
        allow_live_send=True,
    )
    # 1 ungesperrter Opt-out und 2 ungesperrte Bounces simulieren
    result = run_orchestrated_action(
        mode="send-gated",
        count=5,
        job_key="gate-block-optout-001",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 1, "bounces_unsuppressed": 2, "crm_sent": 1886, "mailbox_sent": 1886},
        live_executor=lambda c: pytest.fail("Live executor must NEVER be called when gate fails!"),
    )

    assert result["status"] == "GATE_BLOCKED_UNSUPPRESSED_RECORDS"
    assert result["gate_status"] == "RED"
    assert result["customer_emails_sent"] == 0

    alerts_file = tmp_path / "n8n_alerts.jsonl"
    assert alerts_file.exists()
    alerts = [json.loads(line) for line in alerts_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(a["alert_type"] == "UNSUPPRESSED_RECORDS_BLOCK" for a in alerts)


def test_quota_exceeded_triggers_fail_close_and_alert(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=20,
        allow_live_send=True,
    )
    result = run_orchestrated_action(
        mode="send-gated",
        count=50,  # Überschreitet max_budget_per_run=20
        job_key="quota-exceeded-001",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 0, "bounces_unsuppressed": 0, "crm_sent": 1886, "mailbox_sent": 1886},
        live_executor=lambda c: pytest.fail("Live executor must NEVER be called on quota violation!"),
    )

    assert result["status"] == "QUOTA_EXCEEDED"
    assert result["gate_status"] == "RED"
    assert result["customer_emails_sent"] == 0

    alerts_file = tmp_path / "n8n_alerts.jsonl"
    alerts = [json.loads(line) for line in alerts_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(a["alert_type"] == "QUOTA_EXCEEDED" for a in alerts)


def test_exclusive_lock_blocks_concurrent_execution(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    lock_file = tmp_path / "n8n_orchestrator.lock"
    lock_file.write_text(json.dumps({"pid": os.getpid(), "job_key": "running-job"}), encoding="utf-8")

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=20,
        allow_live_send=False,
    )
    result = run_orchestrated_action(
        mode="preflight",
        count=5,
        job_key="concurrent-job-002",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 0, "bounces_unsuppressed": 0, "crm_sent": 1886, "mailbox_sent": 1886},
    )

    assert result["status"] == "LOCKED_CONCURRENT_RUN"
    assert result["customer_emails_sent"] == 0


def test_reconciliation_mismatch_triggers_alert_and_blocks_send(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=20,
        allow_live_send=True,
        max_reconciliation_drift=0,
    )
    result = run_orchestrated_action(
        mode="send-gated",
        count=5,
        job_key="recon-drift-001",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 0, "bounces_unsuppressed": 0, "crm_sent": 1886, "mailbox_sent": 1895},
        live_executor=lambda c: pytest.fail("Live executor must NEVER be called on reconciliation drift!"),
    )

    assert result["status"] == "RECONCILIATION_DRIFT_BLOCKED"
    assert result["customer_emails_sent"] == 0

    alerts_file = tmp_path / "n8n_alerts.jsonl"
    alerts = [json.loads(line) for line in alerts_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(a["alert_type"] == "RECONCILIATION_DRIFT" for a in alerts)


def test_live_executor_gate_failure_emits_alert_and_fails_closed(tmp_path: Path):
    from n8n_orchestrator import OrchestratorConfig, run_orchestrated_action

    cfg = OrchestratorConfig(
        state_dir=tmp_path,
        max_budget_per_run=500,
        allow_live_send=True,
    )

    def _failing_engine(_count: int):
        raise RuntimeError("SEND_HEALTH_MISSING_OR_STALE")

    result = run_orchestrated_action(
        mode="send-gated",
        count=500,
        job_key="engine-health-block-001",
        config=cfg,
        leitstand_metrics={"optouts_unsuppressed": 0, "bounces_unsuppressed": 0},
        live_executor=_failing_engine,
    )

    assert result["status"] == "ENGINE_EXECUTION_BLOCKED"
    assert result["gate_status"] == "RED"
    assert result["customer_emails_sent"] == 0
    assert "SEND_HEALTH_MISSING_OR_STALE" in result["error"]

    alerts_file = tmp_path / "n8n_alerts.jsonl"
    alerts = [json.loads(line) for line in alerts_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(a["alert_type"] == "ENGINE_EXECUTION_BLOCKED" for a in alerts)

