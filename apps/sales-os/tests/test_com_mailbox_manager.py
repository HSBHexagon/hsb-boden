from pathlib import Path
import sys
import pytest
import os

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
    assert cfg_joel["reply_to"] == ""

    cfg_jordi = get_com_mailbox_config("JORDI")
    assert cfg_jordi["email"] == "j-post@hsb-boden.com"
    assert cfg_jordi["username"] == "m0821e5b"
    assert cfg_jordi["imap_server"] == "w0221a9f.kasserver.com"
    assert cfg_jordi["reply_to"] == ""


def test_com_mailbox_config_invalid_owner():
    with pytest.raises(ValueError, match="Unbekannter Owner"):
        get_com_mailbox_config("UNKNOWN_USER")


def test_com_mailbox_client_fail_closed_on_invalid_recipient():
    client = ComMailboxClient("JOEL")
    with pytest.raises(ValueError, match="Ungueltige Empfaengeradresse"):
        client.create_draft(to_email="invalid-no-at", subject="Test", body_html="<p>Test</p>")

    with pytest.raises(ValueError, match="Ungueltige Empfaengeradresse"):
        client.create_draft(to_email="", subject="Test", body_html="<p>Test</p>")


@pytest.mark.skipif(os.environ.get("HSB_LIVE_READONLY_TESTS") != "yes", reason="Separate explicit live audit verifies authentication")
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


def test_com_mailbox_create_draft_sets_reply_to_header(monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    client = ComMailboxClient("JOEL")
    captured = {}
    class FakeImap:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def append(self, folder, flags, date_time, raw_bytes):
            import email
            captured["msg"] = email.message_from_bytes(raw_bytes)
            return "OK", [b"Success"]
    monkeypatch.setattr(client, "_get_imap", lambda: FakeImap())
    monkeypatch.setattr(client, "_assert_draft_capacity", lambda *_: None)
    ok, mid = client.create_draft("cherinodiaz@outlook.com", "Test Betreff", "<p>Hallo</p>")
    assert ok is True
    msg = captured["msg"]
    assert "j-cherino@hsb-boden.com" in msg["From"]
    assert msg["Reply-To"] is None
    assert msg["To"] == "cherinodiaz@outlook.com"
    assert msg["X-Unsent"] == "1"


def test_com_mailbox_send_message_executes_smtp_and_appends_to_sent(monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    client = ComMailboxClient("JOEL")
    captured = {}
    class FakeImap:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def append(self, folder, flags, date_time, raw_bytes):
            captured["imap_folder"] = folder
            return "OK", [b"Success"]

    class FakeSMTP:
        def __init__(self, host, port, context=None, timeout=None):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def login(self, u, p):
            pass
        def send_message(self, msg):
            captured["smtp_msg"] = msg

    monkeypatch.setattr(client, "_get_imap", lambda: FakeImap())
    monkeypatch.setattr(client, "_assert_draft_capacity", lambda *_: None)
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    ok, mid = client.send_message("cherinodiaz@outlook.com", "Live Send Test", "<p>Hallo</p><SCRIPT>hidden_script_payload</SCRIPT   bar>")
    assert ok is True
    assert captured["imap_folder"] == '"Gesendet"'
    msg = captured["smtp_msg"]
    plain = next(p for p in msg.walk() if p.get_content_type() == "text/plain").get_payload(decode=True).decode()
    assert "hidden_script_payload" not in plain
    assert "j-cherino@hsb-boden.com" in msg["From"]
    assert msg["Reply-To"] is None
    assert msg["To"] == "cherinodiaz@outlook.com"


def test_com_mailbox_send_message_with_bcc(monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    client = ComMailboxClient("JOEL")
    captured = {}
    class FakeImap:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def append(self, folder, flags, date_time, raw_bytes):
            return "OK", [b"Success"]

    class FakeSMTP:
        def __init__(self, host, port, context=None, timeout=None):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def login(self, u, p):
            pass
        def send_message(self, msg, *args, **kwargs):
            captured["smtp_msg"] = msg
            captured["to_addrs"] = kwargs.get("to_addrs")

    monkeypatch.setattr(client, "_get_imap", lambda: FakeImap())
    monkeypatch.setattr(client, "_assert_draft_capacity", lambda *_: None)
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    ok, mid = client.send_message(
        to_email="cherinodiaz@outlook.com",
        subject="Test mit BCC",
        body_html="<p>Hallo</p>",
        bcc_email="Joel Cherino Diaz <j-cherino@hsb-boden.de>"
    )
    assert ok is True
    assert captured["to_addrs"] == ["cherinodiaz@outlook.com", "j-cherino@hsb-boden.de"]
    assert captured["smtp_msg"]["To"] == "cherinodiaz@outlook.com"
    assert "Bcc" not in captured["smtp_msg"]


def test_inbound_read_failure_never_looks_like_empty_inbox():
    import pytest
    from contextlib import contextmanager
    for failure in ('select','search','fetch'):
        class IMAP:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def select(self,*a,**k):return ('NO',[]) if failure=='select' else ('OK',[])
            def uid(self,verb,*a):
                if verb==failure:return 'NO',[]
                if verb=='search':return 'OK',[b'1']
                return 'OK',[(b'header',b'Subject: Test\r\n\r\ntext')]
        c=object.__new__(ComMailboxClient);c.owner='JOEL';c.cfg={'inbox_folder':'INBOX'};c._get_imap=lambda:IMAP()
        with pytest.raises(RuntimeError,match='INBOX_'):
            c.fetch_inbound_messages(limit=0)
