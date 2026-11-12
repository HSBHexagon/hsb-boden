"""
Unit-Tests für die Multi-Inbox Pool-Rotations-Engine (High-Volume Outreach 1.000 - 10.000 Mails/Tag).
"""
import pytest
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from inbox_rotation_pool import InboxRotationPool, MailboxNode, PoolExhaustedError


def test_round_robin_distribution_across_mailboxes():
    pool = InboxRotationPool()
    pool.register_mailbox("sender1@hsb-boden.com", daily_cap=100)
    pool.register_mailbox("sender2@hsb-boden.com", daily_cap=100)
    pool.register_mailbox("sender3@hsb-boden.com", daily_cap=100)

    # 6 Zuweisungen im gleichmäßigen Umlauf
    assigned = [pool.get_next_mailbox() for _ in range(6)]
    assert assigned == [
        "sender1@hsb-boden.com",
        "sender2@hsb-boden.com",
        "sender3@hsb-boden.com",
        "sender1@hsb-boden.com",
        "sender2@hsb-boden.com",
        "sender3@hsb-boden.com",
    ]


def test_failover_when_individual_mailbox_cap_is_exhausted():
    pool = InboxRotationPool()
    pool.register_mailbox("sender1@hsb-boden.com", daily_cap=2)
    pool.register_mailbox("sender2@hsb-boden.com", daily_cap=5)

    # Erste 4 Mails: sender1 (1), sender2 (1), sender1 (2 - voll), sender2 (2)
    for _ in range(4):
        pool.get_next_mailbox()

    # Nächster Abruf: sender1 ist erschöpft, pool rotiert automatisch ausschließlich zu sender2
    next_sender = pool.get_next_mailbox()
    assert next_sender == "sender2@hsb-boden.com"
    assert pool.get_sent_count("sender1@hsb-boden.com") == 2
    assert pool.get_remaining_capacity("sender1@hsb-boden.com") == 0


def test_high_volume_10000_mails_across_pool():
    pool = InboxRotationPool()
    # 10 Absender à 1.000 Mails Kapazität = 10.000 Mails Tagesvolumen
    for i in range(10):
        pool.register_mailbox(f"box{i}@hsb-boden.com", daily_cap=1000)

    assert pool.total_pool_capacity() == 10000

    # Versende 10.000 Mails simuliert
    for _ in range(10000):
        box = pool.get_next_mailbox()
        assert box is not None

    # Alle Postfächer müssen exakt bei 1.000 stehen und der Pool jetzt erschöpft sein
    for i in range(10):
        assert pool.get_sent_count(f"box{i}@hsb-boden.com") == 1000

    with pytest.raises(PoolExhaustedError):
        pool.get_next_mailbox()


def test_deferral_pause_temporarily_skips_mailbox():
    pool = InboxRotationPool()
    pool.register_mailbox("primary@hsb-boden.com", daily_cap=100)
    pool.register_mailbox("secondary@hsb-boden.com", daily_cap=100)

    # Pausiere primary temporär wegen Deferral
    pool.mark_deferred("primary@hsb-boden.com", defer_seconds=300)

    # Muss sofort secondary wählen
    assert pool.get_next_mailbox() == "secondary@hsb-boden.com"
