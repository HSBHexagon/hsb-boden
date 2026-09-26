from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from hsb_config import get_com_mailbox_config
from com_mailbox_manager import ComMailboxClient


def test_com_mailbox_config_joel_and_jordi():
    cfg_joel = get_com_mailbox_config("JOEL")
    assert cfg_joel["email"] == "j-cherino@hsb-boden.com"
    assert cfg_joel["username"] == "m0821e5d"
    assert cfg_joel["imap_server"] == "w0221a9f.kasserver.com"
    assert cfg_joel["imap_port"] == 993
    assert cfg_joel["smtp_port"] == 465

    cfg_jordi = get_com_mailbox_config("JORDI")
    assert cfg_jordi["email"] == "j-post@hsb-boden.com"
    assert cfg_jordi["username"] == "m0821e5b"
    assert cfg_jordi["imap_server"] == "w0221a9f.kasserver.com"


def test_com_mailbox_config_invalid_owner():
    with pytest.raises(ValueError, match="Unbekannter Owner"):
        get_com_mailbox_config("UNKNOWN_USER")


def test_com_mailbox_client_fail_closed_on_invalid_recipient():
    client = ComMailboxClient("JOEL")
    with pytest.raises(ValueError, match="Ungueltige Empfaengeradresse"):
        client.create_draft(to_email="invalid-no-at", subject="Test", body_html="<p>Test</p>")

    with pytest.raises(ValueError, match="Ungueltige Empfaengeradresse"):
        client.create_draft(to_email="", subject="Test", body_html="<p>Test</p>")


def test_com_mailbox_live_connection_and_counts():
    for owner in ["JOEL", "JORDI"]:
        client = ComMailboxClient(owner)
        conn = client.test_connection()
        assert conn["imap"] is True
        assert conn["smtp"] is True
        assert "INBOX" in conn["folders"]
        counts = client.get_counts()
        assert isinstance(counts["drafts"], int)
        assert isinstance(counts["sent"], int)
        assert isinstance(counts["inbox"], int)
