import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from ingest_bounces import scan_com_mailbox_for_bounces

class TestIngestBouncesMove(unittest.TestCase):
    def test_scan_com_mailbox_moves_bounces(self):
        mock_client = MagicMock()
        mock_client.fetch_inbound_messages.return_value = [{
            "id": "999",
            "subject": "Undelivered Mail Returned to Sender",
            "body": "Diagnostic-Code: smtp; 550 5.1.1 User unknown <alt@firma.de>",
            "from": "mailer-daemon@kasserver.com",
            "date_str": "Sun, 08 Nov 2026 06:00:00 +0100"
        }]
        with patch("ingest_bounces.ComMailboxClient", return_value=mock_client):
            bounces = scan_com_mailbox_for_bounces("JOEL", limit=10, move_bounces=True)
            self.assertEqual(len(bounces), 1)
            mock_client.move_message_by_uid.assert_called_once_with("999", source_folder="INBOX", target_folder="Unzustellbar")

    def test_scan_com_mailbox_uses_uid_key_if_present(self):
        mock_client = MagicMock()
        mock_client.fetch_inbound_messages.return_value = [{
            "uid": "42",
            "id": "COM_IMAP:JOEL:HASH-999",
            "subject": "Undelivered Mail Returned to Sender",
            "body": "Diagnostic-Code: smtp; 550 5.1.1 User unknown <alt@firma.de>",
            "from": "mailer-daemon@kasserver.com",
            "date_str": "Sun, 08 Nov 2026 06:00:00 +0100"
        }]
        with patch("ingest_bounces.ComMailboxClient", return_value=mock_client):
            bounces = scan_com_mailbox_for_bounces("JOEL", limit=10, move_bounces=True)
            self.assertEqual(len(bounces), 1)
            mock_client.move_message_by_uid.assert_called_once_with("42", source_folder="INBOX", target_folder="Unzustellbar")

    def test_scan_com_mailbox_does_not_move_in_preview(self):
        mock_client = MagicMock()
        mock_client.fetch_inbound_messages.return_value = [{
            "uid": "42",
            "id": "999",
            "subject": "Undelivered Mail Returned to Sender",
            "body": "Diagnostic-Code: smtp; 550 5.1.1 User unknown <alt@firma.de>",
            "from": "mailer-daemon@kasserver.com",
            "date_str": "Sun, 08 Nov 2026 06:00:00 +0100"
        }]
        with patch("ingest_bounces.ComMailboxClient", return_value=mock_client):
            bounces = scan_com_mailbox_for_bounces("JOEL", limit=10, move_bounces=False)
            self.assertEqual(len(bounces), 1)
            mock_client.move_message_by_uid.assert_not_called()

if __name__ == "__main__":
    unittest.main()
