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

    monkeypatch.setattr(audit, "ComMailboxClient", Client)
    monkeypatch.setattr(audit, "extracted_records", lambda *args, **kw: iter(()))
    report = audit.check_snapshot()
    assert report["seen_inbound_ids"] == ["<incoming@example.test>"]
