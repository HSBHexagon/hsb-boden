import os
import sys
from pathlib import Path
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from sqlite_shadow_store import SQLiteShadowStore


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_shadow.db"
    store = SQLiteShadowStore(str(db_file))
    yield store
    store.close()


def test_init_and_upsert_lead(test_db):
    lead = {
        "Lead_ID": "L-100",
        "Row_Number": 10,
        "Firmenname": "Brauerei Test AG",
        "Email": "kontakt@brauerei-test.de",
        "Status": "not_sent",
    }
    test_db.upsert_lead(lead)
    retrieved = test_db.get_lead("L-100")
    assert retrieved is not None
    assert retrieved["Firmenname"] == "Brauerei Test AG"
    assert retrieved["Status"] == "not_sent"


def test_record_draft_event_and_pending_sync(test_db):
    lead = {
        "Lead_ID": "L-200",
        "Row_Number": 20,
        "Firmenname": "Käse GmbH",
        "Email": "kaese@gmbh.de",
    }
    test_db.upsert_lead(lead)
    test_db.record_draft_event(
        lead_id="L-200", draft_id="MSG-XYZ-999", owner="JOEL", batch_id="B-2026-09"
    )

    lead_after = test_db.get_lead("L-200")
    assert lead_after["Status"] == "drafted"
    assert lead_after["Draft_ID"] == "MSG-XYZ-999"

    pending = test_db.get_pending_sync_events()
    assert len(pending) == 1
    assert pending[0]["lead_id"] == "L-200"

    test_db.mark_synced([pending[0]["id"]])
    assert len(test_db.get_pending_sync_events()) == 0
