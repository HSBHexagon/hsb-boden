"""Ausgehende Kopie trägt genau einen kanonischen List-Unsubscribe-Header, ohne Identität der Nachricht zu verändern."""
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import sys

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

from inbound_classifier import classify_inbound_message  # noqa: E402
from outbound_safety import UNSUBSCRIBE_TOKEN_RE, add_list_unsubscribe  # noqa: E402
from sales_reconciliation import has_unreviewed_legacy_variant  # noqa: E402


def _draft():
    msg = EmailMessage()
    msg["From"] = "Jordie Post <j-post@hsb-boden.com>"
    msg["To"] = "info@beispiel-industrie.invalid"
    msg["Subject"] = "Industrieböden für Beispiel GmbH"
    msg["Message-ID"] = "<abc123@hsb-boden.com>"
    msg.set_content("Hallo")
    return msg


def _mailto(msg):
    value = msg["List-Unsubscribe"]
    assert value.startswith("<") and value.endswith(">")
    return urlsplit(value[1:-1])


def test_header_points_to_sending_com_mailbox_with_lead_token():
    msg = add_list_unsubscribe(_draft(), "JORDI", "HSB-2026-0042")
    link = _mailto(msg)
    assert link.scheme == "mailto" and link.path == "j-post@hsb-boden.com"
    query = parse_qs(link.query)
    assert query["subject"] == ["Abmelden"]
    assert UNSUBSCRIBE_TOKEN_RE.findall(unquote(query["body"][0])) == ["HSB-2026-0042"]
    assert "List-Unsubscribe-Post" not in msg


def test_identity_headers_unchanged_after_serialization():
    msg = add_list_unsubscribe(_draft(), "JOEL", "HSB-1")
    parsed = BytesParser(policy=policy.default).parsebytes(msg.as_bytes(policy=policy.SMTP))
    assert parsed["Message-ID"] == "<abc123@hsb-boden.com>"
    assert parsed["To"] == "info@beispiel-industrie.invalid"
    assert len(parsed.get_all("List-Unsubscribe")) == 1


def test_foreign_or_duplicate_headers_are_replaced_by_one_canonical_header():
    msg = _draft()
    msg["List-Unsubscribe"] = "<mailto:retired@example.net?subject=cancel>"
    msg["List-Unsubscribe"] = "<https://example.net/unsub>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    add_list_unsubscribe(msg, "JOEL", "HSB-7")
    values = msg.get_all("List-Unsubscribe")
    assert len(values) == 1 and values[0].startswith("<mailto:j-cherino@hsb-boden.com?")
    assert "List-Unsubscribe-Post" not in msg


def test_mailto_unsubscribe_reply_is_classified_as_optout():
    # Ein Klick auf 'Abmelden' im Mailprogramm erzeugt eine Mail mit diesem Betreff und dem Token im Text.
    result = classify_inbound_message(
        "kollege@beispiel-industrie.invalid", "Abmelden", "Bitte keine weiteren E-Mails. HSB-ABMELDUNG: HSB-7"
    )
    assert result.category == "OPTOUT"


def test_second_reply_to_header_is_held_for_review():
    raw = (b"From: j-post@hsb-boden.com\r\nTo: info@beispiel-industrie.invalid\r\n"
           b"Reply-To: j-post@hsb-boden.com\r\nReply-To: external@example.net\r\n"
           b"Subject: x\r\nMessage-ID: <x@hsb-boden.com>\r\n\r\nHallo\r\n")
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    assert has_unreviewed_legacy_variant(msg, "JORDI") is True


def test_single_same_mailbox_reply_to_is_accepted():
    msg = _draft()
    msg["Reply-To"] = "j-post@hsb-boden.com"
    assert has_unreviewed_legacy_variant(msg, "JORDI") is False


def test_smtp_bytes_carry_a_plain_mailto_url_for_both_senders():
    from outbound_safety import SMTP_POLICY
    for owner, sender in (("JOEL", b"j-cherino@hsb-boden.com"), ("JORDI", b"j-post@hsb-boden.com")):
        msg = add_list_unsubscribe(_draft(), owner, "HSB-2026-0042")
        raw = msg.as_bytes(policy=SMTP_POLICY)
        line = next(l for l in raw.split(b"\r\n") if l.startswith(b"List-Unsubscribe:"))
        assert line == b"List-Unsubscribe: <mailto:" + sender + b"?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-2026-0042>"
        assert b"=?utf-8?" not in line
