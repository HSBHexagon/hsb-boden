import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from graph_batch_worker import process_batch_chunk


def test_process_batch_chunk_mocked():
    mock_engine = MagicMock()
    mock_engine.execute_batch.return_value = {
        "1": {"id": "1", "status": 201, "body": {"id": "MOCK-DRAFT-1"}},
        "2": {"id": "2", "status": 201, "body": {"id": "MOCK-DRAFT-2"}},
    }
    mock_store = MagicMock()

    leads = [
        {"Lead_ID": "L-1", "Firmenname": "Firma A", "Email": "a@firma.de"},
        {"Lead_ID": "L-2", "Firmenname": "Firma B", "Email": "b@firma.de"},
    ]

    stats = process_batch_chunk(
        leads,
        owner="JOEL",
        batch_engine=mock_engine,
        shadow_store=mock_store,
        batch_id="B-TEST",
    )
    assert stats["success_count"] == 2
    assert stats["failed_count"] == 0
    assert len(stats["draft_ids"]) == 2
    assert mock_store.record_draft_event.call_count == 2
