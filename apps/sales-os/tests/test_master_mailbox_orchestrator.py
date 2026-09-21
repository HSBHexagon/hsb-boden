import sys
from pathlib import Path
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from master_mailbox_orchestrator import validate_preflight


def test_validate_preflight_success(monkeypatch):
    monkeypatch.setattr("master_mailbox_orchestrator.run_ssot_check", lambda: True)
    monkeypatch.setattr("master_mailbox_orchestrator.run_dns_audit", lambda: 85)

    assert validate_preflight() is True


def test_validate_preflight_fails_on_bad_ssot(monkeypatch):
    monkeypatch.setattr("master_mailbox_orchestrator.run_ssot_check", lambda: False)
    assert validate_preflight() is False
