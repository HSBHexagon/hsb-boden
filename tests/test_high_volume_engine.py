"""
Unit Tests fuer High-Volume Matrix Engine (UG-02).
Prueft:
1. Exakte 1.000er Lead-Partitionierung (500 Joel / 500 Jordie) ohne Crossover.
2. 2D-Matrix Formatierung (exakt 17 Spalten AN bis BD).
3. Paced Dispatcher Timing & Backoff.
"""
import time
import urllib.error
import pytest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from high_volume_matrix_engine import (
    partition_leads,
    build_2d_matrix,
    PacedDispatcher
)
from hsb_core import EMAIL_RE

def test_partition_1000_leads_integrity():
    joel_leads, jordi_leads = partition_leads(500, joel_start_row=152, jordi_start_row=3534, use_live_sheet=True)

    assert len(joel_leads) == 500, "Joel muss genau 500 Leads haben"
    assert len(jordi_leads) == 500, "Jordie muss genau 500 Leads haben"

    assert joel_leads[0]["_row"] == 152
    assert joel_leads[-1]["_row"] == 651

    assert jordi_leads[0]["_row"] == 3534
    assert jordi_leads[-1]["_row"] == 4033

    joel_ids = set(l["Lead_ID"] for l in joel_leads)
    jordi_ids = set(l["Lead_ID"] for l in jordi_leads)

    assert len(joel_ids) == 500, "Alle 500 Joel Lead-IDs muessen eindeutig sein"
    assert len(jordi_ids) == 500, "Alle 500 Jordie Lead-IDs muessen eindeutig sein"

    overlap = joel_ids.intersection(jordi_ids)
    assert len(overlap) == 0, f"Kein Crossover zulaessig: {overlap}"

    for l in joel_leads + jordi_leads:
        email = str(l.get("Email") or "").strip()
        assert EMAIL_RE.match(email), f"Ungueltige E-Mail: {email}"
        assert str(l.get("Send_Status") or "").lower() not in ["sent", "gesendet"]
        assert str(l.get("Reply_Status") or "").lower() not in ["bounced", "hard_bounce"]
        assert str(l.get("Opt_Out") or "").lower() not in ["yes", "ja", "opt_out"]
        assert str(l.get("Suppressed") or "").lower() not in ["yes", "ja", "true"]

def test_partition_offline_xlsx_fallback():
    joel_leads, jordi_leads = partition_leads(10, joel_start_row=152, jordi_start_row=3314, use_live_sheet=False)
    assert len(joel_leads) == 10
    assert len(jordi_leads) == 10
    overlap = set(l["Lead_ID"] for l in joel_leads).intersection(set(l["Lead_ID"] for l in jordi_leads))
    assert len(overlap) == 0

def test_build_2d_matrix_format():
    leads = [
        {"_row": 152, "Lead_ID": "TEST-01", "Legal_Basis": "OPT_IN", "Suppressed": "no"},
        {"_row": 153, "Lead_ID": "TEST-02", "Legal_Basis": "EXISTING_CUSTOMER_7_3", "Suppressed": "no"}
    ]
    results = [
        {"row": 152, "draft_id": "DRAFT-152", "internet_message_id": "<mid-152@hsb>", "conversation_id": "CONV-152"},
        {"row": 153, "draft_id": "DRAFT-153", "internet_message_id": "<mid-153@hsb>", "conversation_id": "CONV-153"}
    ]
    matrix = build_2d_matrix(leads, results, "BATCH-TEST")

    assert len(matrix) == 2
    for row in matrix:
        assert len(row) == 17, "Jede Matrix-Zeile muss genau 17 Spalten haben (AN bis BD)"
        assert row[0] == "BATCH-TEST"
        assert row[1] == "drafted"
        assert row[7] == "DRAFTED"

    assert matrix[0][9] == "DRAFT-152"
    assert matrix[0][13] == "<mid-152@hsb>"
    assert matrix[0][14] == "CONV-152"

def test_paced_dispatcher_timing():
    dispatcher = PacedDispatcher(min_interval_seconds=0.05)
    t0 = time.time()
    for _ in range(3):
        dispatcher.execute_with_retry(lambda: True, "test")
    dt = time.time() - t0
    assert dt >= 0.08, f"Pacing muss mindestens 2 Intervalle eingehalten haben: {dt}s"

def test_paced_dispatcher_backoff_on_429():
    attempts = 0
    def mock_flaky_call():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            headers = {"Retry-After": "0.05"}
            raise urllib.error.HTTPError("http://test", 429, "Too Many Requests", headers, None)
        return "SUCCESS"

    dispatcher = PacedDispatcher(min_interval_seconds=0.01, max_retries=2)
    result = dispatcher.execute_with_retry(mock_flaky_call, "flaky test")
    assert result == "SUCCESS"
    assert attempts == 2
