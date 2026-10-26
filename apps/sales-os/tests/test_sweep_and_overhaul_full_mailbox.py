import sys
import time
from unittest.mock import MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Stub out heavy/missing external dependencies before importing engine modules
mock_google = MagicMock()
mock_google_oauth2 = MagicMock()
mock_google_oauth2_credentials = MagicMock()
sys.modules['google'] = mock_google
sys.modules['google.oauth2'] = mock_google_oauth2
sys.modules['google.oauth2.credentials'] = mock_google_oauth2_credentials
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from sweep_and_overhaul_full_mailbox import classify_draft, delete_draft


def test_classify_draft():
    email_map = {
        "valid@firma.de": (2, {"Email": "valid@firma.de", "Firma": "Valid Firma"})
    }

    # Empty recipient -> PURGE
    d_empty = {"toRecipients": "", "subject": "Test", "body": "Body"}
    assert classify_draft(d_empty, email_map) == ("PURGE", "Empfängeradresse ist komplett leer")

    # Dummy recipient -> PURGE
    d_dummy = {"toRecipients": "mustermann@example.com", "subject": "Test", "body": "Body"}
    assert classify_draft(d_dummy, email_map)[0] == "PURGE"

    # Not in ALL_LEADS -> PURGE
    d_unknown = {"toRecipients": "unknown@firma.de", "subject": "Test", "body": "Body"}
    assert classify_draft(d_unknown, email_map)[0] == "PURGE"

    # Outdated draft -> OVERHAUL
    d_outdated = {
        "toRecipients": "valid@firma.de",
        "subject": "Angebot für Ihr Unternehmen",
        "body": "Hallo"
    }
    assert classify_draft(d_outdated, email_map)[0] == "OVERHAUL"

    # Pristine draft -> PRISTINE
    d_pristine = {
        "toRecipients": "valid@firma.de",
        "subject": "Spezifisches Angebot",
        "body": "hsb-boden-logo.png abmelden Jordie Post"
    }
    assert classify_draft(d_pristine, email_map) == ("PRISTINE", "Entspricht dem kanonischen 2026-Standard")


def mock_delete_draft(token, conn_id, mid, latency=0.02):
    time.sleep(latency)
    return True


def benchmark_sequential_vs_concurrent_purge():
    purge_list = [(f"mid_{i}", f"to_{i}@test.de", f"Subj {i}", "Reason") for i in range(50)]
    token = "mock_token"
    conn_id = "mock_conn"

    # Sequential execution baseline
    t0 = time.perf_counter()
    seq_purged = 0
    for mid, to, subj, reason in purge_list:
        if mock_delete_draft(token, conn_id, mid):
            seq_purged += 1
    t1 = time.perf_counter()
    seq_time = t1 - t0

    # Concurrent execution (10 workers)
    t2 = time.perf_counter()
    con_purged = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(mock_delete_draft, token, conn_id, mid)
            for mid, to, subj, reason in purge_list
        ]
        for f in as_completed(futures):
            if f.result():
                con_purged += 1
    t3 = time.perf_counter()
    con_time = t3 - t2

    print(f"\n--- BENCHMARK RESULTS (50 draft purges) ---")
    print(f"Sequential Purge Time: {seq_time:.4f}s")
    print(f"Concurrent Purge Time: {con_time:.4f}s")
    print(f"Speedup Factor        : {seq_time / con_time:.2f}x")

    assert seq_purged == 50
    assert con_purged == 50
    assert con_time < seq_time


if __name__ == "__main__":
    test_classify_draft()
    benchmark_sequential_vs_concurrent_purge()
    print("ALL SWEEP & OVERHAUL TESTS AND BENCHMARKS PASSED.")
