"""Tests fuer DSN-Klassifikation, Zustellbarkeits-Flags und bounce-report (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import hsb_cli
import lead_quality
from hsb_core import check_eligibility
from lead_quality import classify_dsn, delivery_bounce_status, deliverability_flags, summarize_bounces


def test_delivery_outcome_uses_action_and_the_matching_recipient():
    report = (
        'Final-Recipient: rfc822; first@example.test\nAction: failed\nStatus: 5.1.1\n\n'
        'Final-Recipient: rfc822; second@example.test\nAction: delayed\nStatus: 4.2.0\n'
    )
    assert delivery_bounce_status(report, 'first@example.test') == 'hard_bounce'
    assert delivery_bounce_status(report, 'second@example.test') == 'deferred'
    assert delivery_bounce_status(report.replace('Action: delayed', 'Action: failed'), 'second@example.test') == 'failed_temporary'
    assert delivery_bounce_status(report, 'other@example.test') == 'bounce_review'
    assert delivery_bounce_status('Action: failed\nStatus: 5.7.51') == 'policy_block'
    assert delivery_bounce_status('Action: failed\nStatus: 5.0.0') == 'bounce_review'


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


def test_classify_dsn_ignores_ip_and_received_headers():
    body = ("Received: from mx.example.org (10.4.2.3) by 5.9.1.2 with ESMTP\n"
            "Final-Recipient: rfc822; a@firma-a.de\nStatus: 5.1.1\n"
            "Diagnostic-Code: smtp; 550 5.1.1 User unknown")
    assert classify_dsn(body) == "hard"
    soft = "Received: from 5.9.1.2 by 10.5.7.3\nStatus: 4.2.2\nDiagnostic-Code: smtp; 452 4.2.2 Mailbox full"
    assert classify_dsn(soft) == "soft"


def test_classify_dsn_boilerplate_does_not_override_code():
    body = ("This is the mail system. Our spam policy blocked nothing here.\n"
            "550 5.1.1 <a@firma-a.de> User unknown\n"
            "See our anti-spam policy at https://example.org/policy")
    assert classify_dsn(body) == "hard"


def test_classify_dsn_diagnostic_code_policy():
    body = "Final-Recipient: rfc822; a@firma-a.de\nDiagnostic-Code: smtp; 554 5.7.1 message rejected as spam"
    assert classify_dsn(body) == "policy"


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
    flags = deliverability_flags(_lead(), {"firma-a.de": True}, {"Firma-A.de"})
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
    assert summary["hard_by_domain"] == {"firma-a.de": 1}
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


def test_dns_failure_is_not_a_deliverability_pass(monkeypatch):
    from enrich_company_names import check_domain_mx
    def unavailable(*a,**k): raise TimeoutError('dns unavailable')
    monkeypatch.setattr('enrich_company_names.subprocess.run',unavailable)
    assert check_domain_mx('firma.invalid') is False


def test_null_mx_rejects_email(monkeypatch):
    from types import SimpleNamespace
    from enrich_company_names import check_domain_mx
    monkeypatch.setattr('enrich_company_names.subprocess.run',lambda *a,**k:SimpleNamespace(stdout='firma.invalid mail is handled by 0 .\n'))
    assert check_domain_mx('firma.invalid') is False


def test_recipient_specific_remote_relay_denial_is_hard_bounce_not_sender_policy():
    dsn = (
        "Reporting-MTA: dns; dd43534.kasserver.com\n\n"
        "Final-Recipient: rfc822; rejected@example.test\n"
        "Action: failed\n"
        "Status: 5.7.1\n"
        "Remote-MTA: dns; mx1.agenturserver.de\n"
        "Diagnostic-Code: smtp; 554 5.7.1 <rejected@example.test>: Relay access denied\n"
    )
    assert delivery_bounce_status(dsn, "rejected@example.test") == "hard_bounce"
    assert delivery_bounce_status(dsn, "different@example.test") == "bounce_review"
    assert delivery_bounce_status(
        dsn.replace("Relay access denied", "rejected as spam"),
        "rejected@example.test"
    ) == "policy_block"
    assert delivery_bounce_status(
        dsn.replace("Remote-MTA: dns; mx1.agenturserver.de\n", ""),
        "rejected@example.test"
    ) == "policy_block"


def test_previously_reported_as_unknown_is_hard_bounce():
    dsn = (
        "Reporting-MTA: dns; dd43534.kasserver.com\n\n"
        "Original-Recipient: rfc822; unknown@example.test\n\n"
        "Final-Recipient: rfc822; unknown@example.test\n"
        "Action: failed\n"
        "Status: 5.7.1\n"
        "Diagnostic-Code: smtp; 554 5.7.1 Message cannot be sent. One or more recipients were previously reported as unknown.\n"
    )
    assert delivery_bounce_status(dsn, "unknown@example.test") == "hard_bounce"
    assert delivery_bounce_status(dsn, None) == "hard_bounce"


def test_german_isp_explicit_nonexistent_mailbox_and_domain_dsns_are_hard_bounce():
    ionos_dsn = (
        "Final-Recipient: rfc822; contact@loma-online.com\n"
        "Action: failed\n"
        "Status: 5.0.0\n"
        "Remote-MTA: dns; mx01.ionos.de\n"
        "Diagnostic-Code: smtp; 550-Requested action not taken: mailbox unavailable 550\n"
        "    For explanation visit https://postmaster.1und1.de/en/case?c=r1601\n"
    )
    strato_dsn = (
        "Final-Recipient: rfc822; info@team.example\n"
        "Action: failed\n"
        "Status: 5.1.2\n"
        "Diagnostic-Code: smtp; 550 5.1.2 No such mailbox [MSG0031]\n"
    )
    exchange_not_found = (
        "Final-Recipient: rfc822; anfrage@m-s-arch.example\n"
        "Action: failed\n"
        "Status: 5.1.10\n"
        "Diagnostic-Code: smtp;550 5.1.10 RESOLVER.ADR.RecipientNotFound; Recipient anfrage@m-s-arch.example not found\n"
    )
    exo_dbeb = (
        "Final-Recipient: rfc822; info@refresco.example\n"
        "Action: failed\n"
        "Status: 5.4.1\n"
        "Diagnostic-Code: smtp; 550 5.4.1 Recipient address rejected: Access denied. For more information see https://aka.ms/EXOSmtpErrors\n"
    )
    hosteurope_invalid = (
        "Final-Recipient: rfc822; info@shop.example\n"
        "Action: failed\n"
        "Status: 5.0.0\n"
        "Diagnostic-Code: smtp; 550 Address invalid (ID:550:1:1 (mi002.mc1.hosteurope.de))\n"
    )
    dead_domain = (
        "Final-Recipient: rfc822; office@plan80.example\n"
        "Action: failed\n"
        "Status: 5.4.4\n"
        "Diagnostic-Code: X-Postfix; Host or domain name not found. Name service error\n"
    )
    null_mx = (
        "Final-Recipient: rfc822; info@lead-it.example\n"
        "Action: failed\n"
        "Status: 5.1.0\n"
        "Diagnostic-Code: X-Postfix; Domain lead-it.example does not accept mail (nullMX)\n"
    )

    assert delivery_bounce_status(ionos_dsn, "contact@loma-online.com") == "hard_bounce"
    assert delivery_bounce_status(strato_dsn, "info@team.example") == "hard_bounce"
    assert delivery_bounce_status(exchange_not_found, "anfrage@m-s-arch.example") == "hard_bounce"
    assert delivery_bounce_status(exo_dbeb, "info@refresco.example") == "hard_bounce"
    assert delivery_bounce_status(hosteurope_invalid, "info@shop.example") == "hard_bounce"
    assert delivery_bounce_status(dead_domain, "office@plan80.example") == "hard_bounce"
    assert delivery_bounce_status(null_mx, "info@lead-it.example") == "hard_bounce"

    # Negative guards: ambiguous 5.0.0, relaying denied without EXOSmtpErrors, and policy blocks stay protected
    assert delivery_bounce_status("Action: failed\nStatus: 5.0.0") == "bounce_review"
    assert delivery_bounce_status(
        "Final-Recipient: rfc822; a@example.com\nAction: failed\nStatus: 5.0.0\nDiagnostic-Code: smtp; 550 relaying denied",
        "a@example.com",
    ) == "bounce_review"
    assert delivery_bounce_status(
        "Final-Recipient: rfc822; a@example.com\nAction: failed\nStatus: 5.4.1\nDiagnostic-Code: smtp; 550 5.4.1 Access denied",
        "a@example.com",
    ) == "bounce_review"
    assert delivery_bounce_status(
        "Final-Recipient: rfc822; a@example.com\nAction: failed\nStatus: 5.7.1\nDiagnostic-Code: smtp; 550 5.7.1 rejected as spam",
        "a@example.com",
    ) == "policy_block"
