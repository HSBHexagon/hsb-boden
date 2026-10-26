"""Ausgehende Kopie trägt einen List-Unsubscribe-Header, ohne Identität der Nachricht zu verändern."""
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

from inbound_classifier import classify_inbound_message  # noqa: E402
from outbound_safety import add_list_unsubscribe  # noqa: E402


def _draft():
    msg = EmailMessage()
    msg["From"] = "Jordie Post <j-post@hsb-boden.com>"
    msg["To"] = "info@beispiel-industrie.invalid"
    msg["Subject"] = "Industrieböden für Beispiel GmbH"
    msg["Message-ID"] = "<abc123@hsb-boden.com>"
    msg.set_content("Hallo")
    return msg


def test_header_points_to_sending_com_mailbox():
    msg = add_list_unsubscribe(_draft(), "JORDI")
    assert msg["List-Unsubscribe"] == "<mailto:j-post@hsb-boden.com?subject=Abmelden>"
    assert "List-Unsubscribe-Post" not in msg


def test_identity_headers_unchanged_after_serialization():
    msg = add_list_unsubscribe(_draft(), "JOEL")
    parsed = BytesParser(policy=policy.default).parsebytes(msg.as_bytes(policy=policy.SMTP))
    assert parsed["Message-ID"] == "<abc123@hsb-boden.com>"
    assert parsed["To"] == "info@beispiel-industrie.invalid"
    assert parsed["List-Unsubscribe"] == "<mailto:j-cherino@hsb-boden.com?subject=Abmelden>"


def test_existing_header_is_not_duplicated():
    msg = _draft()
    msg["List-Unsubscribe"] = "<mailto:x@hsb-boden.com>"
    add_list_unsubscribe(msg, "JOEL")
    assert msg.get_all("List-Unsubscribe") == ["<mailto:x@hsb-boden.com>"]


def test_mailto_unsubscribe_reply_is_classified_as_optout():
    # Ein Klick auf 'Abmelden' im Mailprogramm erzeugt eine leere Mail mit diesem Betreff.
    result = classify_inbound_message("info@beispiel-industrie.invalid", "Abmelden", "")
    assert result.category == "OPTOUT"
