"""
Unit Tests fuer Postfach- & Sende-Abgleich (reconcile_mailbox.py).
Prueft:
1. Status-Abfrage aus Google Sheet ALL_LEADS (get_leads_status & print_status).
2. Zeilen-Markierung als versendet (mark_rows_sent).
3. CLI Argumente & Steuerungslogik (main).
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

import reconcile_mailbox as rm


def test_get_leads_status_normal_and_mismatched_rows():
    mock_service = MagicMock()
    mock_batch_get = MagicMock()
    mock_service.spreadsheets().values().batchGet.return_value = mock_batch_get

    # 3 leads in col_a, 2 in col_i, 3 in col_aa, 2 in col_ao, 1 in col_ap, 3 in col_ar, 2 in col_au
    mock_batch_get.execute.return_value = {
        "valueRanges": [
            {"values": [["HSB-001"], ["HSB-002"], ["HSB-003"]]},
            {"values": [["info@firma-a.de"], ["kontakt@firma-b.de"]]},
            {"values": [["Joel Cherino"], ["Jordie Post"], ["Unbekannt"]]},
            {"values": [["drafted"], ["sent"]]},
            {"values": [["2026-09-18 10:00:00"]]},
            {"values": [["none"], ["reply"], ["positive_reply"]]},
            {"values": [["DRAFTED"], ["SENT"]]},
        ]
    }

    with patch.object(rm, "get_sheets_service", return_value=mock_service):
        leads = rm.get_leads_status()

    assert len(leads) == 3

    assert leads[0] == {
        "row": 2,
        "lead_id": "HSB-001",
        "email": "info@firma-a.de",
        "owner": "JOEL",
        "owner_raw": "Joel Cherino",
        "send_status": "drafted",
        "send_datum": "2026-09-18 10:00:00",
        "reply_status": "none",
        "batch_status": "DRAFTED",
    }

    assert leads[1] == {
        "row": 3,
        "lead_id": "HSB-002",
        "email": "kontakt@firma-b.de",
        "owner": "JORDI",
        "owner_raw": "Jordie Post",
        "send_status": "sent",
        "send_datum": "",
        "reply_status": "reply",
        "batch_status": "SENT",
    }

    assert leads[2] == {
        "row": 4,
        "lead_id": "HSB-003",
        "email": "",
        "owner": "UNBEKANNT",
        "owner_raw": "Unbekannt",
        "send_status": "",
        "send_datum": "",
        "reply_status": "positive_reply",
        "batch_status": "",
    }


def test_get_leads_status_empty_response():
    mock_service = MagicMock()
    mock_service.spreadsheets().values().batchGet().execute.return_value = {
        "valueRanges": [{}, {}, {}, {}, {}, {}, {}]
    }

    with patch.object(rm, "get_sheets_service", return_value=mock_service):
        leads = rm.get_leads_status()

    assert leads == []


def test_print_status_metrics_output(capsys):
    mock_leads = [
        # Joel: 1 drafted by send_status, 1 drafted by batch_status, 1 sent, 1 replied (positive_reply)
        {
            "row": 2,
            "owner": "JOEL",
            "send_status": "drafted",
            "batch_status": "",
            "reply_status": "none",
        },
        {
            "row": 3,
            "owner": "JOEL",
            "send_status": "",
            "batch_status": "DRAFTED",
            "reply_status": "auto_reply_ooo",
        },
        {
            "row": 4,
            "owner": "JOEL",
            "send_status": "sent",
            "batch_status": "SENT",
            "reply_status": "positive_reply",
        },
        # Jordi: 1 sent, 1 replied (reply)
        {
            "row": 5,
            "owner": "JORDI",
            "send_status": "sent",
            "batch_status": "",
            "reply_status": "reply",
        },
    ]

    with patch.object(rm, "get_leads_status", return_value=mock_leads):
        rm.print_status()

    captured = capsys.readouterr().out
    assert "HSB SALES OS — CRM STATUS & SENDE-MONITOR" in captured
    assert "Kontakte in Datenbank" in captured
    assert "4" in captured
    assert "3" in captured
    assert "1" in captured


def test_mark_rows_sent_custom_timestamp():
    mock_service = MagicMock()
    mock_batch_update = MagicMock()
    mock_service.spreadsheets().values().batchUpdate.return_value = mock_batch_update

    with patch.object(rm, "get_sheets_service", return_value=mock_service):
        rm.mark_rows_sent(10, 12, send_timestamp="2026-09-19 12:34:56")

    mock_service.spreadsheets().values().batchUpdate.assert_called_once_with(
        spreadsheetId=rm.SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": "ALL_LEADS!AO10:AP12",
                    "values": [
                        ["sent", "2026-09-19 12:34:56"],
                        ["sent", "2026-09-19 12:34:56"],
                        ["sent", "2026-09-19 12:34:56"],
                    ],
                },
                {
                    "range": "ALL_LEADS!AU10:AU12",
                    "values": [["SENT"], ["SENT"], ["SENT"]],
                },
                {
                    "range": "ALL_LEADS!BD10:BD12",
                    "values": [[""], [""], [""]],
                },
            ],
        },
    )
    mock_batch_update.execute.assert_called_once()


def test_mark_rows_sent_default_timestamp():
    mock_service = MagicMock()

    with patch.object(rm, "get_sheets_service", return_value=mock_service):
        rm.mark_rows_sent(5, 5)

    call_args = mock_service.spreadsheets().values().batchUpdate.call_args[1]
    data = call_args["body"]["data"]
    timestamp = data[0]["values"][0][1]
    assert len(timestamp) == 19  # YYYY-MM-DD HH:MM:SS
    assert data[0]["range"] == "ALL_LEADS!AO5:AP5"


def test_main_cli_status_flag():
    with patch.object(rm, "print_status") as mock_print_status, patch.object(
        sys, "argv", ["reconcile_mailbox.py", "--status"]
    ):
        rm.main()
        mock_print_status.assert_called_once()


def test_main_cli_mark_sent_flag():
    with patch.object(rm, "mark_rows_sent") as mock_mark_rows_sent, patch.object(
        rm, "print_status"
    ) as mock_print_status, patch.object(
        sys, "argv", ["reconcile_mailbox.py", "--mark-sent", "10", "15"]
    ):
        rm.main()
        mock_mark_rows_sent.assert_called_once_with(10, 15)
        mock_print_status.assert_called_once()


def test_main_cli_mark_sent_owner_with_drafts():
    mock_leads = [
        {"row": 10, "owner": "JOEL", "send_status": "drafted"},
        {"row": 12, "owner": "JOEL", "send_status": "drafted"},
        {"row": 15, "owner": "JOEL", "send_status": "drafted"},
        {"row": 20, "owner": "JORDI", "send_status": "drafted"},
    ]

    with patch.object(
        rm, "get_leads_status", return_value=mock_leads
    ), patch.object(rm, "mark_rows_sent") as mock_mark_rows_sent, patch.object(
        rm, "print_status"
    ) as mock_print_status, patch.object(
        sys,
        "argv",
        ["reconcile_mailbox.py", "--mark-sent-owner", "JOEL", "--count", "2"],
    ):
        rm.main()
        mock_mark_rows_sent.assert_called_once_with(10, 12)
        mock_print_status.assert_called_once()


def test_main_cli_mark_sent_owner_no_drafts(capsys):
    mock_leads = [
        {"row": 10, "owner": "JOEL", "send_status": "sent"},
    ]

    with patch.object(
        rm, "get_leads_status", return_value=mock_leads
    ), patch.object(rm, "mark_rows_sent") as mock_mark_rows_sent, patch.object(
        sys, "argv", ["reconcile_mailbox.py", "--mark-sent-owner", "JORDI"]
    ):
        rm.main()
        mock_mark_rows_sent.assert_not_called()
        captured = capsys.readouterr().out
        assert "Keine offenen Entwürfe für JORDI" in captured


def test_main_cli_sync_cloud():
    mock_run_cloud_sync = MagicMock()

    with patch.dict("sys.modules", {"reconcile_cloud_mailbox": MagicMock(run_cloud_sync=mock_run_cloud_sync)}), patch.object(
        rm, "print_status"
    ) as mock_print_status, patch.object(
        sys, "argv", ["reconcile_mailbox.py", "--sync-cloud", "--owner", "JORDI"]
    ):
        rm.main()
        mock_run_cloud_sync.assert_called_once_with(target_owner="JORDI")
        mock_print_status.assert_called_once()


def test_main_cli_sync_apple_mail_deprecated(capsys):
    mock_run_cloud_sync = MagicMock()

    with patch.dict("sys.modules", {"reconcile_cloud_mailbox": MagicMock(run_cloud_sync=mock_run_cloud_sync)}), patch.object(
        rm, "print_status"
    ) as mock_print_status, patch.object(
        sys, "argv", ["reconcile_mailbox.py", "--sync-apple-mail"]
    ):
        rm.main()
        captured = capsys.readouterr().out
        assert "Apple Mail ist abgeloest durch Cloud-Native Sync" in captured
        mock_run_cloud_sync.assert_called_once_with(target_owner=None)
        mock_print_status.assert_called_once()


def test_main_cli_default_no_args():
    with patch.object(rm, "print_status") as mock_print_status, patch.object(
        sys, "argv", ["reconcile_mailbox.py"]
    ):
        rm.main()
        mock_print_status.assert_called_once()
