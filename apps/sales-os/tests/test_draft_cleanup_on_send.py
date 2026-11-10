import sys
import pathlib
from unittest.mock import MagicMock

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from outbound_safety import cleanup_sent_draft
from com_mailbox_manager import ComMailboxClient


def test_cleanup_sent_draft_calls_manager_delete():
    client = MagicMock()
    cleanup_sent_draft(client, "INBOX.Drafts", "12345")
    client.delete_draft_by_uid.assert_called_once_with("12345", "INBOX.Drafts")


def test_cleanup_sent_draft_falls_back_to_imap():
    client = MagicMock(spec=["_get_imap"])
    imap_mock = MagicMock()
    imap_mock.select.return_value = ("OK", [b"1"])
    client._get_imap.return_value.__enter__.return_value = imap_mock

    cleanup_sent_draft(client, "Entw&APw-rfe", "999")

    imap_mock.select.assert_called_once_with("Entw&APw-rfe")
    imap_mock.uid.assert_called_once_with("store", "999", "+FLAGS", r"(\Deleted)")
    imap_mock.expunge.assert_called_once()


def test_cleanup_sent_draft_handles_exceptions_gracefully():
    client = MagicMock()
    client.delete_draft_by_uid.side_effect = RuntimeError("IMAP timeout")

    # Must not raise
    cleanup_sent_draft(client, "INBOX.Drafts", "12345")


def test_cleanup_sent_draft_noop_on_missing_args():
    # Must not raise and do nothing
    cleanup_sent_draft(None, None, None)
    cleanup_sent_draft(MagicMock(), "", None)


def test_com_mailbox_client_delete_draft_by_uid(monkeypatch):
    mgr = ComMailboxClient("JOEL")
    imap_mock = MagicMock()
    imap_mock.select.return_value = ("OK", [b"1"])
    monkeypatch.setattr(mgr, "_get_imap", lambda: MagicMock(__enter__=lambda s: imap_mock, __exit__=lambda *a: None))

    ok = mgr.delete_draft_by_uid("555", "INBOX.Drafts")
    assert ok is True
    imap_mock.select.assert_called_once_with("INBOX.Drafts")
    imap_mock.uid.assert_called_once_with("store", "555", "+FLAGS", r"(\Deleted)")
    imap_mock.expunge.assert_called_once()


def test_cmd_purge_sent_drafts(monkeypatch):
    from hsb_cli import cmd_purge_sent_drafts
    from types import SimpleNamespace

    mock_leads = [
        {"Lead-ID": "L1", "E-Mail": "sent1@test.com", "Send_Status": "sent"},
        {"Lead-ID": "L2", "E-Mail": "pending@test.com", "Send_Status": ""},
    ]
    monkeypatch.setattr("hsb_cli._load_all_leads", lambda svc: (["Lead-ID", "E-Mail", "Send_Status"], mock_leads))

    imap_mock = MagicMock()
    imap_mock.select.return_value = ("OK", [b"1"])
    imap_mock.search.return_value = ("OK", [b"1 2"])

    msg_sent = b"To: sent1@test.com\r\nSubject: Test\r\n\r\nBody"
    msg_pending = b"To: pending@test.com\r\nSubject: Test 2\r\n\r\nBody"

    def mock_fetch(num, spec):
        if num == b"1":
            return ("OK", [(b"1", msg_sent)])
        return ("OK", [(b"2", msg_pending)])

    imap_mock.fetch.side_effect = mock_fetch

    mock_client = MagicMock()
    mock_client.cfg = {"drafts_folder": "INBOX.Drafts"}
    mock_client._get_imap.return_value.__enter__.return_value = imap_mock

    monkeypatch.setattr("com_mailbox_manager.ComMailboxClient", lambda o: mock_client)

    args = SimpleNamespace(owner="JOEL", apply=True)
    report = cmd_purge_sent_drafts(args, svc=MagicMock())

    assert report["total_sent_in_crm"] == 1
    assert report["JOEL"]["orphaned_sent_drafts"] == 1
    assert report["JOEL"]["applied"] is True
    imap_mock.store.assert_called_once_with(b"1", "+FLAGS", r"\Deleted")
    imap_mock.expunge.assert_called_once()

