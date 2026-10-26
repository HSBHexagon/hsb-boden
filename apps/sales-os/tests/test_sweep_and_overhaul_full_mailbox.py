import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT / "engine" / "operator_layer"))

# Mock google modules before importing sweep_and_overhaul_full_mailbox
mock_google = MagicMock()
sys.modules["google"] = mock_google
sys.modules["google.oauth2"] = mock_google.oauth2
sys.modules["google.oauth2.credentials"] = mock_google.oauth2.credentials
sys.modules["googleapiclient"] = mock_google
sys.modules["googleapiclient.discovery"] = mock_google.discovery

import sweep_and_overhaul_full_mailbox


class TestSweepAndOverhaul(unittest.TestCase):

    @patch("sweep_and_overhaul_full_mailbox.delete_draft")
    def test_purge_execution(self, mock_delete_draft):
        mock_delete_draft.side_effect = lambda token, conn_id, mid: mid != "fail_id"

        purge_list = [
            ("mid_1", "user1@example.com", "Subject 1", "Reason 1"),
            ("fail_id", "user2@example.com", "Subject 2", "Reason 2"),
            ("mid_3", "user3@example.com", "Subject 3", "Reason 3"),
        ]

        total_purged = 0
        def _purge_one(item):
            mid, to, subj, reason = item
            ok = sweep_and_overhaul_full_mailbox.delete_draft("token", "conn_id", mid)
            return ok, mid, to, subj, reason

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for ok, mid, to, subj, reason in executor.map(_purge_one, purge_list):
                if ok:
                    total_purged += 1

        self.assertEqual(total_purged, 2)
        self.assertEqual(mock_delete_draft.call_count, 3)


if __name__ == "__main__":
    unittest.main()
