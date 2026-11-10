"""Regression checks for actual imaplib FETCH reply shapes."""
from contextlib import contextmanager
from pathlib import Path
import sys

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))
from capture_com_health import extracted_records


class FakeImap:
    def __init__(self, entries):
        self.entries = entries
        self.readonly = None

    def select(self, folder, readonly):
        self.readonly = readonly
        return "OK", [b"1"]

    def uid(self, action, *arguments):
        if action == "search":
            return "OK", [b"12"]
        if action == "fetch":
            return "OK", self.entries
        raise AssertionError(action)


class FakeClient:
    def __init__(self, entries):
        self.imap = FakeImap(entries)

    @contextmanager
    def _get_imap(self):
        yield self.imap


HEADER = b'From: sender@example.test\r\nSubject: test\r\n\r\n'
META = b'1 (UID 12 INTERNALDATE "09-Nov-2026 18:22:00 +0100" BODY[HEADER.FIELDS (DATE FROM TO SUBJECT MESSAGE-ID)] {50}'


def test_fetch_ignores_imap_closing_literal_and_preserves_readonly():
    client = FakeClient([(META, HEADER), b")"])
    records = list(extracted_records(client, "INBOX"))
    assert len(records) == 1
    assert records[0][0].isoformat() == "2026-11-09T17:22:00+00:00"
    assert records[0][1]["Subject"] == "test"
    assert client.imap.readonly is True


def test_fetch_fails_closed_when_literal_missing():
    client = FakeClient([b")"])
    with pytest.raises(RuntimeError, match="MAILBOX_UID_FETCH_INCOMPLETE"):
        list(extracted_records(client, "INBOX"))


def test_fetch_fails_closed_when_internaldate_missing():
    client = FakeClient([(b"1 (UID 12)", HEADER), b")"])
    with pytest.raises(RuntimeError, match="MAILBOX_INTERNALDATE_MISSING"):
        list(extracted_records(client, "INBOX"))

def test_cursor_prefers_public_message_id_as_reconciliation_does(monkeypatch):
    import capture_com_health as audit

    class Client:
        def __init__(self, owner):
            self.cfg = {"inbox_folder": "INBOX", "sent_folder": "Sent"}

        def fetch_inbound_messages(self, limit=0):
            return [{"id": "COM_IMAP:JOEL:SHA256:abcdef", "internet_message_id": "<incoming@example.test>"}]

        def fetch_sent_messages(self, limit=0):
            return [{"to": "outside@example.test", "date_str": "Mon, 09 Nov 2026 10:00:00 +0000"}]

    import datetime as dt
    from email import message_from_string

    monkeypatch.setattr(audit, "ComMailboxClient", Client)
    from send_governance import MailboxHealthStore
    monkeypatch.setattr(MailboxHealthStore, "read", lambda self: {'state':'paused','reason':'POLICY_BOUNCE','ack_id':'test-only'})
    historical = message_from_string("To: outside@example.test\nDate: invalid\n\n")
    def read_records(_client, _folder, **kwargs):
        if kwargs.get("history"):
            return iter([(audit.NOW - dt.timedelta(days=25), historical)])
        return iter(())
    monkeypatch.setattr(audit, "extracted_records", read_records)
    report = audit.check_snapshot()
    assert report["seen_inbound_ids"] == ["<incoming@example.test>"]


def test_policy_bounce_diagnostic_reports_structured_smtp_codes_without_address():
    from email import policy
    from email.parser import BytesParser
    from datetime import datetime, timezone
    import capture_com_health as audit
    raw = (
        b'MIME-Version: 1.0\r\n'
        b'Content-Type: multipart/report; report-type=delivery-status; boundary="boundary"\r\n'
        b'\r\n--boundary\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'Rejected: address test-recipient@customer.example\r\n'
        b'--boundary\r\n'
        b'Content-Type: message/delivery-status\r\n\r\n'
        b'Final-Recipient: rfc822; test-recipient@customer.example\r\n'
        b'Action: failed\r\n'
        b'Status: 5.7.1\r\n'
        b'Diagnostic-Code: smtp; 550 5.7.1 recipient policy rejected test-recipient@customer.example\r\n'
        b'Remote-MTA: dns; mx.customer.example\r\n\r\n'
        b'--boundary--\r\n'
    )
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    result = audit.policy_bounce_diagnostic(
        msg, audit.msg_body(msg), 'JOEL',
        datetime(2026, 11, 9, 19, 6, tzinfo=timezone.utc), 'policy_block'
    )
    assert result['classification'] == 'policy_block'
    assert result['dsn_blocks']
    assert any(block.get('status') == '5.7.1' for block in result['dsn_blocks'])
    assert '550' in repr(result['dsn_blocks'])
    assert 'test-recipient@customer.example' not in repr(result)
    assert '[EMAIL]' in repr(result)
