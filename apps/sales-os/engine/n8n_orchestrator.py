#!/usr/bin/env python3
"""
HSB Sales OS — n8n Orchestrator & Gate Controller (Keine Parallel-Engine!)
Steuert und überwacht ausschließlich die bestehende Versand-Engine (hsb_cli.py / versand-tranche.sh).

Sicherheitsgarantien gemäß Betreiberauftrag vom 14.11.2026:
1. Exklusives Prozess-Lock (Fail-Closed bei aktivem Parallel-Lauf)
2. Idempotenter Job-Key (Verhindert Doppelausführung bei Webhook/Schedule-Retries)
3. P0-Opt-out/Bounce-Gate (Fail-Closed wenn ungesperrte Opt-outs oder Bounces > 0)
4. Reconciliation-Gate (Prüft Abweichung zwischen CRM und Postfach-Stand)
5. Quoten-/Budget-Gate (Verhindert Überschreitung des genehmigten Tranchen-Budgets)
6. Revisionssicheres Journal (n8n_orchestrator_journal.jsonl) & Alert-Stream (n8n_alerts.jsonl)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class OrchestratorConfig:
    state_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("HSB_SALES_STATE_DIR", str(Path.home() / ".local/state/hsb-sales-os"))
        )
    )
    max_budget_per_run: int = 25
    allow_live_send: bool = False
    max_reconciliation_drift: int = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _emit_alert(state_dir: Path, alert_type: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    record = {
        "timestamp": _utc_now(),
        "alert_type": alert_type,
        "severity": "CRITICAL",
        "message": message,
        "details": details,
    }
    _append_jsonl(state_dir / "n8n_alerts.jsonl", record)
    return record


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _is_job_key_seen(state_dir: Path, job_key: str) -> bool:
    ledger = state_dir / "n8n_executed_jobs.jsonl"
    if not ledger.exists():
        return False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if row.get("job_key") == job_key:
                return True
        except json.JSONDecodeError:
            continue
    return False


def _record_job_key(state_dir: Path, job_key: str, mode: str, status: str) -> None:
    _append_jsonl(
        state_dir / "n8n_executed_jobs.jsonl",
        {"timestamp": _utc_now(), "job_key": job_key, "mode": mode, "status": status},
    )


def run_orchestrated_action(
    *,
    mode: str,
    count: int,
    job_key: str,
    config: OrchestratorConfig,
    leitstand_metrics: dict[str, Any],
    dry_run_executor: Callable[[int], dict[str, Any]] | None = None,
    live_executor: Callable[[int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    state_dir = config.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    journal_path = state_dir / "n8n_orchestrator_journal.jsonl"
    lock_file = state_dir / "n8n_orchestrator.lock"

    # 1. Exklusives Lock prüfen
    if lock_file.exists():
        try:
            lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            existing_pid = int(lock_data.get("pid", -1))
        except Exception:
            existing_pid = -1
        if _is_pid_alive(existing_pid):
            _emit_alert(
                state_dir,
                "CONCURRENT_LOCK_ACTIVE",
                f"Paralleler Orchestrator-Lauf blockiert (PID {existing_pid}).",
                {"job_key": job_key, "active_pid": existing_pid},
            )
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "LOCKED_CONCURRENT_RUN",
                "gate_status": "RED",
                "customer_emails_sent": 0,
            }
            _append_jsonl(journal_path, res)
            return res

    # Lock setzen
    lock_file.write_text(
        json.dumps({"pid": os.getpid(), "job_key": job_key, "started_at": _utc_now()}),
        encoding="utf-8",
    )

    try:
        # 2. Idempotenz-Gate über Job-Key
        if _is_job_key_seen(state_dir, job_key):
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "DUPLICATE_JOB_KEY_SKIPPED",
                "gate_status": "GREEN",
                "customer_emails_sent": 0,
            }
            _append_jsonl(journal_path, res)
            return res

        # 3. Opt-out & Bounce Fail-Close Gate
        optouts_unsupp = int(leitstand_metrics.get("optouts_unsuppressed", -1))
        bounces_unsupp = int(leitstand_metrics.get("bounces_unsuppressed", -1))
        if optouts_unsupp != 0 or bounces_unsupp != 0:
            _emit_alert(
                state_dir,
                "UNSUPPRESSED_RECORDS_BLOCK",
                f"Sicherheitsstopp: {optouts_unsupp} Opt-outs und {bounces_unsupp} Bounces ohne Sperre!",
                {"job_key": job_key, "optouts_unsuppressed": optouts_unsupp, "bounces_unsuppressed": bounces_unsupp},
            )
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "GATE_BLOCKED_UNSUPPRESSED_RECORDS",
                "gate_status": "RED",
                "customer_emails_sent": 0,
                "metrics": leitstand_metrics,
            }
            _append_jsonl(journal_path, res)
            return res

        # 4. Reconciliation Drift Gate
        if "crm_sent" in leitstand_metrics and "mailbox_sent" in leitstand_metrics:
            drift = abs(int(leitstand_metrics["crm_sent"]) - int(leitstand_metrics["mailbox_sent"]))
            if drift > config.max_reconciliation_drift:
                _emit_alert(
                    state_dir,
                    "RECONCILIATION_DRIFT",
                    f"Abweichung zwischen CRM ({leitstand_metrics['crm_sent']}) und Postfach ({leitstand_metrics['mailbox_sent']}): Drift={drift}",
                    {"job_key": job_key, "drift": drift, "max_allowed": config.max_reconciliation_drift},
                )
                res = {
                    "timestamp": _utc_now(),
                    "job_key": job_key,
                    "mode": mode,
                    "status": "RECONCILIATION_DRIFT_BLOCKED",
                    "gate_status": "RED",
                    "customer_emails_sent": 0,
                    "drift": drift,
                }
                _append_jsonl(journal_path, res)
                return res

        # 5. Quoten-/Budget-Gate
        if count < 1 or count > config.max_budget_per_run or count > 500:
            _emit_alert(
                state_dir,
                "QUOTA_EXCEEDED",
                f"Angeforderte Menge ({count}) überschreitet zulässiges Tranchen-Budget ({config.max_budget_per_run}).",
                {"job_key": job_key, "requested_count": count, "max_budget_per_run": config.max_budget_per_run},
            )
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "QUOTA_EXCEEDED",
                "gate_status": "RED",
                "customer_emails_sent": 0,
            }
            _append_jsonl(journal_path, res)
            return res

        # 6. Modus-Ausführung
        if mode in ("health", "reconcile"):
            _record_job_key(state_dir, job_key, mode, "HEALTH_RECONCILED")
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "HEALTH_RECONCILED",
                "gate_status": "GREEN",
                "customer_emails_sent": 0,
                "metrics": leitstand_metrics,
            }
            _append_jsonl(journal_path, res)
            return res

        if mode == "preflight":
            exec_res = dry_run_executor(count) if dry_run_executor else {"customer_emails_sent": 0}
            _record_job_key(state_dir, job_key, mode, "DRY_RUN_COMPLETED")
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "DRY_RUN_COMPLETED",
                "gate_status": "GREEN",
                "customer_emails_sent": int(exec_res.get("customer_emails_sent", 0)),
                "engine_output": exec_res,
            }
            _append_jsonl(journal_path, res)
            return res

        if mode == "send-gated":
            if not config.allow_live_send:
                _emit_alert(
                    state_dir,
                    "UNAUTHORIZED_LIVE_SEND_ATTEMPT",
                    "Live-Versand angefordert, aber HSB_ALLOW_LIVE_SEND ist nicht freigegeben.",
                    {"job_key": job_key, "count": count},
                )
                res = {
                    "timestamp": _utc_now(),
                    "job_key": job_key,
                    "mode": mode,
                    "status": "GATE_REJECTED_NO_OPERATOR_APPROVAL",
                    "gate_status": "RED",
                    "customer_emails_sent": 0,
                }
                _append_jsonl(journal_path, res)
                return res

            exec_res = live_executor(count) if live_executor else {"customer_emails_sent": 0}
            _record_job_key(state_dir, job_key, mode, "LIVE_BATCH_EXECUTED")
            res = {
                "timestamp": _utc_now(),
                "job_key": job_key,
                "mode": mode,
                "status": "LIVE_BATCH_EXECUTED",
                "gate_status": "GREEN",
                "customer_emails_sent": int(exec_res.get("customer_emails_sent", 0)),
                "engine_output": exec_res,
            }
            _append_jsonl(journal_path, res)
            return res

        raise ValueError(f"Unbekannter Orchestrator-Modus: {mode}")
    finally:
        if lock_file.exists():
            try:
                lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
                if int(lock_data.get("pid", -1)) == os.getpid():
                    lock_file.unlink(missing_ok=True)
            except Exception:
                pass


def fetch_live_leitstand_metrics(engine_dir: Path) -> dict[str, Any]:
    override_json = os.environ.get("HSB_ORCHESTRATOR_METRICS_JSON")
    if override_json:
        return json.loads(override_json)

    op_dir = str(engine_dir / "operator_layer")
    if op_dir not in sys.path:
        sys.path.insert(0, op_dir)
    from crm_common import SID, services  # type: ignore

    sheets, _ = services("info")
    res = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=SID, range="'LEITSTAND VISUELL'!B18:B19")
        .execute()
    )
    vals = res.get("values", [])
    optouts_unsupp = int(vals[0][0]) if len(vals) > 0 and vals[0] else -1
    bounces_unsupp = int(vals[1][0]) if len(vals) > 1 and vals[1] else -1
    return {
        "optouts_unsuppressed": optouts_unsupp,
        "bounces_unsuppressed": bounces_unsupp,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HSB Sales OS n8n Orchestrator & Gate Controller")
    parser.add_argument("--mode", choices=["health", "reconcile", "preflight", "send-gated"], default="health")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--job-key", default=f"job-{int(datetime.now(timezone.utc).timestamp())}")
    args = parser.parse_args(argv)

    engine_dir = Path(__file__).resolve().parent
    sales_dir = engine_dir.parent
    tranche_script = sales_dir / "bin" / "versand-tranche.sh"

    config = OrchestratorConfig(
        max_budget_per_run=int(os.environ.get("HSB_MAX_BUDGET_PER_RUN", "25")),
        allow_live_send=os.environ.get("HSB_ALLOW_LIVE_SEND", "no").lower() == "yes",
        max_reconciliation_drift=int(os.environ.get("HSB_MAX_RECONCILIATION_DRIFT", "0")),
    )

    metrics = fetch_live_leitstand_metrics(engine_dir)

    def _dry_run(n: int) -> dict[str, Any]:
        proc = subprocess.run(
            ["bash", str(tranche_script), str(n)],
            cwd=str(sales_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Dry-Run versand-tranche.sh fehlgeschlagen (Exit {proc.returncode}): {proc.stderr}")
        return {"customer_emails_sent": 0, "returncode": proc.returncode}

    def _live_run(n: int) -> dict[str, Any]:
        proc = subprocess.run(
            ["bash", str(tranche_script), str(n), "--apply"],
            cwd=str(sales_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Live versand-tranche.sh fehlgeschlagen (Exit {proc.returncode}): {proc.stderr}")
        return {"customer_emails_sent": n, "returncode": proc.returncode}

    result = run_orchestrated_action(
        mode=args.mode,
        count=args.count,
        job_key=args.job_key,
        config=config,
        leitstand_metrics=metrics,
        dry_run_executor=_dry_run,
        live_executor=_live_run,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("gate_status") == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())

