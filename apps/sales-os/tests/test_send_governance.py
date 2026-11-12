"""
Testet Send-Governance, Jitter-Verzoegerung (45-180s) und konfigurierbares Tages-Cap (Obergrenze 250 Mails/Tag) (Goal G11).
"""
import datetime
from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from send_governance import (
    SendGovernanceQueue,
    DailyCapReachedError,
    MIN_JITTER_SECONDS,
    MAX_JITTER_SECONDS,
    DAILY_CAP_PER_MAILBOX,
    REAL_EXTERNAL_PROSPECT_SEND_COUNT
)


def test_jitter_corridor_is_strictly_between_45_and_180_seconds():
    queue = SendGovernanceQueue()
    delays = [queue.get_jitter_delay() for _ in range(200)]

    for d in delays:
        assert MIN_JITTER_SECONDS <= d <= MAX_JITTER_SECONDS, f"Jitter {d} liegt ausserhalb [{MIN_JITTER_SECONDS}, {MAX_JITTER_SECONDS}]"

    # Pruefe stochastische Streuung
    assert min(delays) < 70, f"Min delay zu hoch: {min(delays)}"
    assert max(delays) > 150, f"Max delay zu niedrig: {max(delays)}"


def test_strict_daily_cap_enforcement_at_configured_limit():
    queue = SendGovernanceQueue()
    mailbox = "j-post@hsb-boden.de"
    today = datetime.date(2026, 9, 18)

    # Bis zum konfigurierten Limit muessen alle Nachrichten erlaubt sein
    for i in range(1, DAILY_CAP_PER_MAILBOX + 1):
        item = queue.queue_send(mailbox, f"prospect-{i}@kunde.de", target_date=today)
        assert item["status"] == "QUEUED"
        assert item["day_sequence_number"] == i
        assert MIN_JITTER_SECONDS <= item["jitter_delay_seconds"] <= MAX_JITTER_SECONDS

    # Die erste Nachricht ueber dem Limit muss blockiert werden
    with pytest.raises(DailyCapReachedError) as exc_info:
        queue.queue_send(mailbox, f"prospect-{DAILY_CAP_PER_MAILBOX + 1}@kunde.de", target_date=today)

    assert f"{DAILY_CAP_PER_MAILBOX}/{DAILY_CAP_PER_MAILBOX} versendet" in str(exc_info.value)
    print(f"Cap-Erreichung auf #{DAILY_CAP_PER_MAILBOX + 1} erfolgreich abgewehrt.")


def test_independent_mailbox_quotas():
    queue = SendGovernanceQueue()
    today = datetime.date(2026, 9, 18)

    # Erschoepfe Jordis Kontingent
    for i in range(DAILY_CAP_PER_MAILBOX):
        queue.queue_send("j-post@hsb-boden.de", f"p-jordi-{i}@kunde.de", target_date=today)

    # Joels Kontingent muss weiterhin voll verfuegbar sein
    can_send_joel, count, remaining = queue.can_send("j-cherino@hsb-boden.de", target_date=today)
    assert can_send_joel is True
    assert count == 0
    assert remaining == DAILY_CAP_PER_MAILBOX

    item_joel = queue.queue_send("j-cherino@hsb-boden.de", "p-joel@kunde.de", target_date=today)
    assert item_joel["status"] == "QUEUED"
    assert item_joel["day_sequence_number"] == 1


def test_real_external_send_count_guardrail():
    assert REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0, "REAL_EXTERNAL_PROSPECT_SEND_COUNT muss strikt 0 sein!"


if __name__ == "__main__":
    test_jitter_corridor_is_strictly_between_45_and_180_seconds()
    test_strict_daily_cap_enforcement_at_configured_limit()
    test_independent_mailbox_quotas()
    test_real_external_send_count_guardrail()
    print("ALL G11 SEND GOVERNANCE TESTS PASSED SUCCESSFULLY.")
