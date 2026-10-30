import sys
from pathlib import Path

# Sicherstellen, dass engine/ und operator_layer/ immer im Suchpfad liegen
_ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
_OPERATOR_DIR = _ENGINE_DIR / "operator_layer"
for _d in (str(_ENGINE_DIR), str(_OPERATOR_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import pytest
"""Unit tests never depend on production mailbox credentials."""
import os
os.environ.setdefault('HSB_COM_JOEL_USER','m0821e5d')
os.environ.setdefault('HSB_COM_JORDI_USER','m0821e5b')
os.environ.setdefault('HSB_COM_JOEL_PASS','unit-test-password')
os.environ.setdefault('HSB_COM_JORDI_PASS','unit-test-password')


@pytest.fixture(autouse=True)
def _row_guard_off_for_simple_sheet_fakes(request, monkeypatch):
    """Die meisten Versandtests nutzen Sheet-Attrappen ohne Einzelzellen-Lesen; die Zeilenprüfung
    hat eigene Tests (test_hsb_auth_and_row_guard.py). Mit @pytest.mark.row_guard bleibt sie aktiv."""
    if request.node.get_closest_marker('row_guard'):
        return
    import outbound_safety
    monkeypatch.setattr(outbound_safety, 'assert_row_lead', lambda *a, **k: None)
    # Einfache Attrappen kennen keine Developer-Metadaten: Versand-Writes dort zeilenbasiert simulieren.
    monkeypatch.setattr(outbound_safety, '_send_write',
                        lambda svc, sid, headers, row, lead_id, fields: outbound_safety.crm_write_readback(svc, sid, headers, row, fields))
    monkeypatch.setattr(outbound_safety, 'prepare_lead_binding', lambda *a, **k: None)
    monkeypatch.setattr(outbound_safety, '_release_binding', lambda *a, **k: None)
    monkeypatch.setenv('HSB_CRM_BINDINGS_VERIFIED', 'yes')


def pytest_configure(config):
    config.addinivalue_line('markers', 'row_guard: Zeilenprüfung assert_row_lead im Test aktiv lassen')
