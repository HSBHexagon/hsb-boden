import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

DUMMY_CFG = {
    "imap_server": "mail.example.com",
    "imap_port": 993,
    "smtp_server": "mail.example.com",
    "smtp_port": 465,
    "username": "user@example.com",
    "password": "secret_password",
    "email": "user@example.com",
    "drafts_folder": "Drafts",
    "sent_folder": "Sent Items",
    "inbox_folder": "INBOX"
}

class TestBounceMailboxFolder(unittest.TestCase):
    @patch("com_mailbox_manager.get_com_mailbox_config", return_value=DUMMY_CFG)
    def test_ensure_folder_creates_when_missing(self, mock_cfg):
        from com_mailbox_manager import ComMailboxClient
        client = ComMailboxClient("JOEL")
        mock_imap = MagicMock()
        mock_imap.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
        mock_imap.create.return_value = ("OK", [b'Success'])
        mock_imap.__enter__.return_value = mock_imap
        mock_imap.__exit__.return_value = None
        
        with patch.object(client, "_get_imap", return_value=mock_imap):
            res = client.ensure_folder("Unzustellbar")
            self.assertTrue(res)
            mock_imap.create.assert_called_once_with('"Unzustellbar"')

    @patch("com_mailbox_manager.get_com_mailbox_config", return_value=DUMMY_CFG)
    def test_ensure_folder_skips_when_exists(self, mock_cfg):
        from com_mailbox_manager import ComMailboxClient
        client = ComMailboxClient("JOEL")
        mock_imap = MagicMock()
        mock_imap.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "Unzustellbar"'])
        mock_imap.__enter__.return_value = mock_imap
        mock_imap.__exit__.return_value = None
        
        with patch.object(client, "_get_imap", return_value=mock_imap):
            res = client.ensure_folder("Unzustellbar")
            self.assertTrue(res)
            mock_imap.create.assert_not_called()

    @patch("com_mailbox_manager.get_com_mailbox_config", return_value=DUMMY_CFG)
    def test_move_message_by_uid(self, mock_cfg):
        from com_mailbox_manager import ComMailboxClient
        client = ComMailboxClient("JORDI")
        mock_imap = MagicMock()
        mock_imap.select.return_value = ("OK", [b'1'])
        mock_imap.uid.side_effect = [
            ("OK", [b'Copy OK']),   # COPY
            ("OK", [b'Flags OK']),  # STORE +FLAGS (\Deleted)
        ]
        mock_imap.__enter__.return_value = mock_imap
        mock_imap.__exit__.return_value = None
        
        with patch.object(client, "_get_imap", return_value=mock_imap), \
             patch.object(client, "ensure_folder", return_value=True):
            res = client.move_message_by_uid("12345", source_folder="INBOX", target_folder="Unzustellbar")
            self.assertTrue(res)
            mock_imap.uid.assert_any_call("COPY", "12345", '"Unzustellbar"')
            mock_imap.uid.assert_any_call("STORE", "12345", "+FLAGS", r"(\Deleted)")
            mock_imap.expunge.assert_called_once()

if __name__ == "__main__":
    unittest.main()
