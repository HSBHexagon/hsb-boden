import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from async_sheet_sync_daemon import flush_pending_to_sheets


def test_flush_pending_to_sheets():
    mock_store = MagicMock()
    mock_store.get_pending_sync_events.return_value = [
        {
            "id": 1,
            "lead_id": "L-1",
            "payload": '{"draft_id": "D-1", "owner": "JOEL", "batch_id": "B-1", "drafted_at": "2026-09-21 12:00:00"}',
        },
        {
            "id": 2,
            "lead_id": "L-2",
            "payload": '{"draft_id": "D-2", "owner": "JORDI", "batch_id": "B-1", "drafted_at": "2026-09-21 12:00:00"}',
        },
    ]
    mock_store.get_lead.side_effect = lambda lid: {
        "row_number": 10 if lid == "L-1" else 11
    }

    mock_sheets = MagicMock()
    mock_sheets.batch_update_cells.return_value = True

    synced_count = flush_pending_to_sheets(mock_store, mock_sheets, batch_size=50)
    assert synced_count == 2
    assert mock_sheets.batch_update_cells.called
    assert mock_store.mark_synced.called
