import sys
import pathlib
from types import SimpleNamespace
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


def _make_batched_uid_imap_mock(uid_to_email):
    imap_mock = MagicMock()
    imap_mock.select.return_value = ("OK", [str(len(uid_to_email)).encode()])
    uid_calls = []

    def mock_uid(op, *args):
        op_l = op.lower()
        uid_calls.append((op_l, args))
        if op_l == "search":
            return ("OK", [b" ".join(uid_to_email.keys())])
        if op_l == "fetch":
            uid_list = args[0].split(b",")
            resp = []
            for idx, uid in enumerate(uid_list, start=1):
                header = f"To: {uid_to_email[uid]}\r\n\r\n".encode()
                meta = f"{idx} (UID {uid.decode()} BODY[HEADER.FIELDS (TO)] {{{len(header)}}}".encode()
                resp.append((meta, header))
                resp.append(b")")
            return ("OK", resp)
        if op_l == "store":
            return ("OK", [b""])
        raise AssertionError(f"Unexpected imap.uid op: {op}")

    imap_mock.uid.side_effect = mock_uid
    return imap_mock, uid_calls


def test_cmd_purge_sent_drafts_batches_uid_fetch_and_store(monkeypatch):
    from hsb_cli import cmd_purge_sent_drafts

    mock_leads = [
        {"Lead-ID": "L1", "E-Mail": "sent1@test.com", "Send_Status": "sent"},
        {"Lead-ID": "L2", "E-Mail": "pending@test.com", "Send_Status": ""},
    ]
    monkeypatch.setattr("hsb_cli._load_all_leads", lambda svc: (["Lead-ID", "E-Mail", "Send_Status"], mock_leads))

    uid_to_email = {}
    for idx in range(450):
        uid = str(1000 + idx).encode()
        uid_to_email[uid] = "Sent1@TEST.com" if idx % 2 == 0 else "pending@test.com"

    imap_mock, uid_calls = _make_batched_uid_imap_mock(uid_to_email)

    mock_client = MagicMock()
    mock_client.cfg = {"drafts_folder": "INBOX.Drafts"}
    mock_client._get_imap.return_value.__enter__.return_value = imap_mock
    monkeypatch.setattr("com_mailbox_manager.ComMailboxClient", lambda o: mock_client)

    args = SimpleNamespace(owner="JOEL", apply=True)
    report = cmd_purge_sent_drafts(args, svc=MagicMock())

    assert report["total_sent_in_crm"] == 1
    assert report["JOEL"]["orphaned_sent_drafts"] == 225
    assert report["JOEL"]["applied"] is True

    fetch_calls = [c for c in uid_calls if c[0] == "fetch"]
    store_calls = [c for c in uid_calls if c[0] == "store"]
    assert 1 <= len(fetch_calls) <= 3
    assert 1 <= len(store_calls) <= 2
    assert all(c[1][1] == "+FLAGS" and c[1][2] == r"(\Deleted)" for c in store_calls)
    imap_mock.fetch.assert_not_called()
    imap_mock.store.assert_not_called()
    imap_mock.expunge.assert_called_once()


def test_cmd_purge_sent_drafts_dry_run_does_not_store_or_expunge(monkeypatch):
    from hsb_cli import cmd_purge_sent_drafts

    mock_leads = [{"Lead-ID": "L1", "E-Mail": "sent1@test.com", "Send_Status": "sent"}]
    monkeypatch.setattr("hsb_cli._load_all_leads", lambda svc: (["Lead-ID", "E-Mail", "Send_Status"], mock_leads))

    imap_mock, uid_calls = _make_batched_uid_imap_mock({b"10": "sent1@test.com", b"11": "keep@test.com"})
    mock_client = MagicMock()
    mock_client.cfg = {"drafts_folder": "INBOX.Drafts"}
    mock_client._get_imap.return_value.__enter__.return_value = imap_mock
    monkeypatch.setattr("com_mailbox_manager.ComMailboxClient", lambda o: mock_client)

    args = SimpleNamespace(owner="JOEL", apply=False)
    report = cmd_purge_sent_drafts(args, svc=MagicMock())

    assert report["JOEL"] == {"orphaned_sent_drafts": 1, "applied": False}
    assert not [c for c in uid_calls if c[0] == "store"]
    imap_mock.expunge.assert_not_called()


def test_cmd_purge_sent_drafts_handles_empty_folder_and_errors(monkeypatch):
    from hsb_cli import cmd_purge_sent_drafts

    mock_leads = [{"Lead-ID": "L1", "E-Mail": "sent1@test.com", "Send_Status": "sent"}]
    monkeypatch.setattr("hsb_cli._load_all_leads", lambda svc: (["Lead-ID", "E-Mail", "Send_Status"], mock_leads))

    empty_imap = MagicMock()
    empty_imap.select.return_value = ("OK", [b"0"])
    empty_imap.uid.return_value = ("OK", [b""])

    err_imap = MagicMock()
    err_imap.select.return_value = ("OK", [b"1"])
    err_imap.uid.side_effect = [("OK", [b"1"]), ("NO", [b"BAD FETCH"])]

    clients = {}
    for owner, imap_obj in [("JOEL", empty_imap), ("JORDI", err_imap)]:
        mc = MagicMock()
        mc.cfg = {"drafts_folder": "INBOX.Drafts"}
        mc._get_imap.return_value.__enter__.return_value = imap_obj
        clients[owner] = mc

    monkeypatch.setattr("com_mailbox_manager.ComMailboxClient", lambda o: clients[o])

    args = SimpleNamespace(owner=None, apply=True)
    report = cmd_purge_sent_drafts(args, svc=MagicMock())

    assert report["JOEL"] == {"orphaned_sent_drafts": 0, "applied": True}
    empty_imap.expunge.assert_not_called()
    assert "error" in report["JORDI"]
