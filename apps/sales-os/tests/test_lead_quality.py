"""Tests fuer DSN-Klassifikation, Zustellbarkeits-Flags und bounce-report (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import hsb_cli
import lead_quality
from hsb_core import check_eligibility
from lead_quality import classify_dsn, deliverability_flags, summarize_bounces


def _lead(email="info@firma-a.de", **extra):
    lead = {"Email": email}
    lead.update(extra)
    return lead


def test_classify_dsn_hard_soft_policy():
    assert classify_dsn("550 5.1.1 User unknown") == "hard"
    assert classify_dsn("452 4.2.2 Mailbox full") == "soft"
    assert classify_dsn("554 5.7.1 rejected as spam") == "policy"
    assert classify_dsn("hallo welt") == "unknown"
    assert classify_dsn("") == "unknown"


def test_no_mx_blocks():
    flags = deliverability_flags(_lead(), {}, set(), mx_check=lambda d: False)
    assert "NO_MX" in flags


def test_syntax_invalid_blocks_without_mx_lookup():
    calls = []
    flags = deliverability_flags(_lead("kein-at-zeichen"), {}, set(), mx_check=lambda d: calls.append(d) or True)
    assert flags == ["SYNTAX_INVALID"]
    assert calls == []


def test_previous_hard_bounce_blocks():
    flags = deliverability_flags(_lead(Bounce_Status="hard_bounce"), {"firma-a.de": True}, set())
    assert "PREVIOUS_HARD_BOUNCE" in flags
    result = check_eligibility(_lead(Deliverability_Flags=flags))
    assert any("PREVIOUS_HARD_BOUNCE" in r for r in result.reasons)
    assert not result.eligible


def test_noreply_blocks():
    flags = deliverability_flags(_lead("no-reply@firma-a.de"), {"firma-a.de": True}, set())
    assert "ROLE_NOREPLY" in flags
    result = check_eligibility(_lead("no-reply@firma-a.de", Deliverability_Flags=flags))
    assert any("ROLE_NOREPLY" in r for r in result.reasons)


def test_domain_bounced_before_warns_only():
    flags = deliverability_flags(_lead(), {"firma-a.de": True}, {"firma-a.de"})
    assert flags == ["DOMAIN_BOUNCED_BEFORE"]
    base = check_eligibility(_lead()).reasons
    warned = check_eligibility(_lead(Deliverability_Flags=flags)).reasons
    assert warned == base  # Warnung veraendert die Gruende nicht
    blocked = check_eligibility(_lead(Deliverability_Flags="NO_MX,DOMAIN_BOUNCED_BEFORE")).reasons
    assert any("NO_MX" in r for r in blocked)
    assert not any("DOMAIN_BOUNCED_BEFORE" in r for r in blocked)


def test_mx_checked_once_per_domain():
    calls = []

    def fake(domain):
        calls.append(domain)
        return True

    cache: dict[str, bool] = {}
    for mail in ("a@firma-a.de", "b@firma-a.de", "c@firma-b.de"):
        deliverability_flags(_lead(mail), cache, set(), mx_check=fake)
    assert calls == ["firma-a.de", "firma-b.de"]
    assert cache == {"firma-a.de": True, "firma-b.de": True}


def test_summarize_bounces_counts_only():
    class Msg:
        def __init__(self, sender, subject, body):
            self.sender, self.subject, self.body = sender, subject, body

    msgs = [
        Msg("MAILER-DAEMON@x", "Undelivered Mail", "Final-Recipient: rfc822; a@firma-a.de\n550 5.1.1 User unknown"),
        Msg("MAILER-DAEMON@x", "Undelivered Mail", "Final-Recipient: rfc822; b@firma-a.de\n452 4.2.2 Mailbox full"),
        Msg("kunde@firma-c.de", "Re: Anfrage", "Danke, gerne Termin."),
    ]
    summary = summarize_bounces(msgs)
    assert summary["by_class"] == {"hard": 1, "soft": 1}
    assert summary["by_domain"] == {"firma-a.de": 2}
    assert summary["total"] == 2
    assert "a@firma-a.de" not in str(summary)


def test_cmd_bounce_report_uses_injected_collector(capsys):
    class Msg:
        sender = "MAILER-DAEMON@x"
        subject = "Undelivered Mail"
        body = "Final-Recipient: rfc822; a@firma-a.de\n554 5.7.1 rejected as spam"

    class Args:
        limit = 50
        com_only = True

    hsb_cli.cmd_bounce_report(Args(), collector=lambda **kw: [Msg()])
    out = capsys.readouterr().out
    assert "policy" in out and "firma-a.de" in out
    assert "a@firma-a.de" not in out
