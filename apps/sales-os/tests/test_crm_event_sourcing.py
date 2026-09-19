"""
Testet deterministische SHA-256 Idempotency-Keys & Append-Only Event-Sourcing im CRM (Goal G10).

Akzeptanzkriterium:
50 parallele Aufrufe erzeugen 0 Duplikate und 0 Zellueberschreibungen.
Schreibschutz fuer den Campari-Datensatz (1 Antwort erhalten) und 167 versendete Datensaetze.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from crm_event_sourcing import CrmEventStore, generate_idempotency_key


def test_50_concurrent_calls_produce_zero_duplicates_and_zero_cell_overwrites():
    store = CrmEventStore()

    # 50 parallele Aufrufe mit identischen und disjunkten Events
    # Davon 25 eindeutige Leads und 25 Wiederholungen/Replays derselben Leads
    # Plus Angriffsversuche auf die geschuetzte Campari-Zelle
    calls = []
    for i in range(25):
        calls.append({
            "lead_id": f"LEAD-CORP-{i:03d}",
            "recipient": f"kontakt@corp-{i}.de",
            "campaign_id": "HSB-2026-Q3",
            "step": "1",
            "action": "log_outreach_step",
            "status": "DRAFT_PREPARED"
        })
        # Exakter Replay des gleichen Leads & Steps
        calls.append({
            "lead_id": f"LEAD-CORP-{i:03d}",
            "recipient": f"kontakt@corp-{i}.de",
            "campaign_id": "HSB-2026-Q3",
            "step": "1",
            "action": "log_outreach_step",
            "status": "DRAFT_PREPARED"
        })

    # Fuege Mutations-Versuche auf Campari ein
    calls.append({
        "lead_id": "CAMPARI-01",
        "action": "overwrite",
        "new_value": "reset_to_unanswered"
    })
    calls.append({
        "lead_id": "CAMPARI-01",
        "action": "update_reply",
        "new_value": "tampered"
    })

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(store.append_event, call) for call in calls]
        for f in futures:
            results.append(f.result())

    # Auswertung
    committed = [r for r in results if r[0] is True]
    duplicates = [r for r in results if r[1] == "duplicate_idempotency_key"]
    overwrites_rejected = [r for r in results if r[1] == "protected_cell_mutation_rejected"]

    print(f"Total concurrent calls executed: {len(calls)}")
    print(f"Committed unique events: {len(committed)}")
    print(f"Duplicates intercepted: {len(duplicates)}")
    print(f"Overwrites blocked on protected cells: {len(overwrites_rejected)}")

    # Pruefungen
    assert len(committed) == 25, f"Erwartet genau 25 eindeutige Events, erhalten: {len(committed)}"
    assert len(duplicates) == 25, f"Erwartet genau 25 abgefangene Duplikate, erhalten: {len(duplicates)}"
    assert len(overwrites_rejected) == 2, f"Erwartet 2 blockierte Zellueberschreibungen auf Campari, erhalten: {len(overwrites_rejected)}"
    assert store.event_count == 25, "Event store enthaelt genau 25 Eintraege (0 Duplikate)"
    assert store.duplicate_count == 25, "0 Duplikate durften persistiert werden"
    assert store.overwrite_attempts == 2, "Zellueberschreibungen wurden registriert und abgewehrt"


def test_sha256_idempotency_key_determinism():
    k1 = generate_idempotency_key("prospect@firma.de", "CAMP-01", 1)
    k2 = generate_idempotency_key("prospect@firma.de ", "CAMP-01", "1")
    k3 = generate_idempotency_key("PROSPECT@FIRMA.DE", "CAMP-01", 1)

    assert k1 == k2 == k3, "Idempotency key muss Gross/Kleinschreibung und Whitespace deterministisch normalisieren"
    assert len(k1) == 64, "SHA-256 Hash muss exakt 64 Hex-Zeichen haben"


if __name__ == "__main__":
    test_sha256_idempotency_key_determinism()
    test_50_concurrent_calls_produce_zero_duplicates_and_zero_cell_overwrites()
    print("ALL G10 IDEMPOTENCY TESTS PASSED SUCCESSFULLY.")
