"""
Unit Tests fuer Cloud-Native Mailbox Reconciliation Engine (UG-03).
Prueft:
1. Dynamischen RFC 3464 DSN Bounce Parser (Statuscodes 550, 5.4.1, 5.1.0 etc.).
2. Dynamischen RFC 3834 Auto-Reply / OOO Parser.
3. Struktur & Integritaet der Cloud-Verbindungsdaten.
"""
import sys
from unittest.mock import MagicMock

# Mock google modules if not installed in current environment
for mod in [
    'google',
    'google.oauth2',
    'google.oauth2.credentials',
    'googleapiclient',
    'googleapiclient.discovery',
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from reconcile_cloud_mailbox import (
    parse_rfc3464_dsn,
    parse_rfc3834_autoreply,
    CONNECTIONS,
    BOUNCE_SUBJ_RE,
    AUTO_REPLY_SUBJ_RE
)


# --- RFC 3464 DSN Bounce Parser Tests ---

def test_rfc3464_bounce_parsing_hard_bounces():
    subj = "Unzustellbar: Industrieböden & Säurebau – HSB Hexagon"
    body = """
    Ihre Nachricht konnte nicht zugestellt werden.
    Fehler beim Übermitteln der Nachricht: 550 5.4.1 Mailbox nicht gefunden: info@milchhuus.ch
    Diagnostic-Code: smtp; 550 5.4.1 [info@milchhuus.ch]: Recipient address rejected
    """
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is True
    assert "550 5.4.1" in reason
    assert "info@milchhuus.ch" in recips


def test_rfc3464_bounce_various_status_codes():
    cases = [
        ("Undeliverable: Offer", "Remote server returned: 550 5.1.0 Mailbox rejected target@firma.de", "550 5.1.0", "target@firma.de"),
        ("Delivery Status Notification (Failure)", "Diagnostic-Code: smtp; 550 5.7.3 Access denied for test@kunde.com", "550 5.7.3", "test@kunde.com"),
        ("Fehler bei der Zustellung: failed", "Status: 5.4.3 System unavailable bad@domain.de", "5.4.3", "bad@domain.de"),
        ("Mail delivery failed", "Action: failed\nStatus: 4.2.2 Mailbox full user@fullbox.org", "4.2.2", "user@fullbox.org"),
    ]
    for subj, body, expected_code, expected_email in cases:
        is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
        assert is_bounce is True, f"Sollte als Bounce erkannt werden: {subj}"
        assert expected_code in reason, f"Erwarteter Code {expected_code} in {reason}"
        assert expected_email in recips, f"Erwartete E-Mail {expected_email} in {recips}"


def test_rfc3464_bounce_subject_keywords():
    bounce_subjects = [
        "Unzustellbar: Angebot",
        "Undeliverable: Re: Meeting",
        "Delivery Status Notification (Failure)",
        "Mail Delivery System - FAILURE",
        "Zustellung FAILED: info@example.com",
    ]
    body = "Diagnostic-Code: 550 5.1.1 user@external-domain.com"
    for subj in bounce_subjects:
        is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
        assert is_bounce is True, f"Subject should trigger bounce detection: '{subj}'"
        assert recips == ["user@external-domain.com"]


def test_rfc3464_bounce_fallback_status_code_when_missing_in_body():
    subj = "Unzustellbar: Ihre Anfrage"
    body = "Die Nachricht konnte nicht an den Empfänger info@partner.de zugestellt werden."
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is True
    assert "550 (Generisch)" in reason
    assert recips == ["info@partner.de"]


def test_rfc3464_bounce_internal_domain_filtering():
    subj = "Undeliverable: Project Status"
    body = """
    From: postmaster@hsb-boden.de
    To: mailer-daemon@outlook.com
    Via: server.microsoft.com
    Failed recipient: client@external-client.de
    """
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is True
    assert "client@external-client.de" in recips
    # Ensure internal domains like hsb-boden.de, microsoft.com, outlook.com, postmaster, mailer-daemon are filtered out
    for internal in ["postmaster@hsb-boden.de", "mailer-daemon@outlook.com", "server.microsoft.com"]:
        assert internal not in recips


def test_rfc3464_bounce_recipient_deduplication_and_limit():
    subj = "Undeliverable: Mass outreach"
    body = """
    Failed to deliver to:
    a@external1.com
    b@external2.com
    c@external3.com
    d@external4.com
    e@external5.com
    """
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is True
    # Deduplicated and limited to top 3
    assert len(recips) == 3
    assert recips == ["a@external1.com", "b@external2.com", "c@external3.com"]


def test_rfc3464_non_bounces():
    subj = "Re: Industrieböden für Ihr Unternehmen"
    body = "Vielen Dank für das Angebot. Wir prüfen das intern."
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is False
    assert reason is None
    assert recips == []


def test_rfc3464_edge_cases_empty_or_malformed():
    # Empty subject and body
    assert parse_rfc3464_dsn("", "") == (False, None, [])

    # Bounce subject, but body has no emails
    is_bounce, reason, recips = parse_rfc3464_dsn("Undeliverable notice", "An error occurred with no email address.")
    assert is_bounce is True
    assert "550 (Generisch)" in reason
    assert recips == []

    # Case insensitive matching in subject
    is_bounce, reason, recips = parse_rfc3464_dsn("UNZUSTELLBAR: TEST", "Status: 5.2.2 user@test.de")
    assert is_bounce is True
    assert "5.2.2" in reason
    assert recips == ["user@test.de"]


# --- RFC 3834 Auto-Reply Parser Tests ---

def test_rfc3834_autoreply_detection():
    # Fall 1: Absender mit no-reply
    is_ar, cls = parse_rfc3834_autoreply("no-reply@darboven.com", "[Wichtig] Ihre Anfrage", "Vielen Dank")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 2: Case Number im Betreff
    is_ar, cls = parse_rfc3834_autoreply("support@becks.de", "::No Reply:: Case Number: 00531307", "Ticket erfasst")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 3: Abwesenheitsnotiz
    is_ar, cls = parse_rfc3834_autoreply("gf@kunde.de", "Automatische Antwort: Bis 20.09 außer Haus", "Ich bin im Urlaub")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 4: Echte Antwort
    is_ar, cls = parse_rfc3834_autoreply("gf@kunde.de", "Re: Industrieböden", "Rufen Sie mich gerne morgen an.")
    assert is_ar is False
    assert cls == ""


# --- Integration & Structure Tests ---

def test_cloud_connections_structure():
    assert "JOEL" in CONNECTIONS
    assert "JORDI" in CONNECTIONS

    assert CONNECTIONS["JOEL"]["account"] == "j-cherino@hsb-boden.de"
    assert CONNECTIONS["JOEL"]["connection_id"] == "shared-office365-819bd473"

    assert CONNECTIONS["JORDI"]["account"] == "j-post@hsb-boden.de"
    assert CONNECTIONS["JORDI"]["connection_id"] == "3d152ea7ddb24e9286fe006cb9f5069b"


def test_inbound_event_row_has_message_id_in_column_f():
    import reconcile_cloud_mailbox as m
    row = m.build_inbound_event_row(
        event_id="X", msg_date="2026-09-17T00:00:00Z", mailbox="j-cherino@hsb-boden.de",
        sender="a@b.de", subject="AW", message_id="<1@b>", lead_id="HSB-1",
        classification="REPLY", stop="no", processed="PROCESSED", notes="n")
    assert row[5] == "<1@b>" and row[11] == "" and len(row) == 12
    assert row[:5] == ["X", "2026-09-17T00:00:00Z", "j-cherino@hsb-boden.de", "a@b.de", "AW"]
    assert row[6:11] == ["HSB-1", "REPLY", "no", "PROCESSED", "n"]
