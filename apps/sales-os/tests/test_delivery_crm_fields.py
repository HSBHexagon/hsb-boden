import sys
import pathlib
import sqlite3
from email.message import EmailMessage
from types import SimpleNamespace

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from outbound_safety import complete_delivery, SendJournal
from sequence import SEQUENCE_SCHEMA


class FakeClient:
    def __init__(self, email="j-cherino@hsb-boden.com"):
        self.cfg = {"email": email, "sent_folder": "Sent"}
        self.delivered = []

    def deliver_verified_bytes(self, raw, recipient, journal=None):
        self.delivered.append((raw, recipient))


class FakeSheetsService:
    def __init__(self):
        self.written = {}
        self.call_history = []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def batchUpdate(self, spreadsheetId, body):
        self.call_history.append(body)
        for update in body.get("data", []):
            self.written[update["range"]] = update["values"]
        return self

    def batchGet(self, spreadsheetId, ranges):
        value_ranges = []
        for r in ranges:
            value_ranges.append({"range": r, "values": self.written.get(r, [[""]])})
        return SimpleNamespace(execute=lambda: {"valueRanges": value_ranges})

    def execute(self):
        return {}


def test_complete_delivery_writes_template_and_segment(tmp_path, monkeypatch):
    """v2-Entwurf mit Header schreibt nach Versand Email_Template_ID und Segment ins CRM."""
    db_path = tmp_path / "journal.sqlite"
    journal = SendJournal(str(db_path))

    client = FakeClient()
    monkeypatch.setattr("outbound_safety.sent_copy_readback", lambda *a: "123")

    svc = FakeSheetsService()
    headers = [
        "Lead-ID",
        "Send_Status",
        "Last_Send_Attempt_At",
        "Outbound_ID",
        "Sender_Account",
        "Send_Datum",
        "Batch_Status",
        "Internet_Message_ID",
        "Email_Template_ID",
        "Segment",
    ]

    msg = EmailMessage()
    msg["To"] = "klaus@brauerei.invalid"
    msg["From"] = "j-cherino@hsb-boden.com"
    msg["Subject"] = "Industrieboden Brauerei"
    msg["Message-ID"] = "<test-v2-mid@hsb-boden.com>"
    msg["X-HSB-Template-ID"] = "v2-produktion-s1"
    msg.set_content("Guten Tag, ...")
    raw = msg.as_bytes()

    item = {
        "owner": "JOEL",
        "lead_id": "HSB-TEST-001",
        "email": "klaus@brauerei.invalid",
    }

    complete_delivery(
        client=client,
        journal=journal,
        svc=svc,
        spreadsheet_id="fake_sheet",
        headers=headers,
        row=2,
        item=item,
        raw=raw,
        mid="<test-v2-mid@hsb-boden.com>",
        cap=10,
    )

    # Prüfe den zweiten crm_write_readback Aufruf (finaler Versandzustand)
    assert len(svc.call_history) == 2
    final_payload = svc.call_history[1]["data"]
    written_map = {item["range"]: item["values"][0][0] for item in final_payload}

    # Spaltenindizes:
    # headers.index('Email_Template_ID') + 1 = 9 -> Spalte I
    # headers.index('Segment') + 1 = 10 -> Spalte J
    assert written_map.get("ALL_LEADS!I2") == "v2-produktion-s1"
    assert written_map.get("ALL_LEADS!J2") == "produktion"
    assert written_map["ALL_LEADS!B2"] == "sent"


def test_v1_message_without_header_leaves_fields_untouched(tmp_path, monkeypatch):
    """v1-Mail ohne Template-Header lässt Email_Template_ID und Segment unangetastet."""
    db_path = tmp_path / "journal.sqlite"
    journal = SendJournal(str(db_path))

    client = FakeClient()
    monkeypatch.setattr("outbound_safety.sent_copy_readback", lambda *a: "123")

    svc = FakeSheetsService()
    headers = [
        "Lead-ID",
        "Send_Status",
        "Last_Send_Attempt_At",
        "Outbound_ID",
        "Sender_Account",
        "Send_Datum",
        "Batch_Status",
        "Internet_Message_ID",
        "Email_Template_ID",
        "Segment",
    ]

    msg = EmailMessage()
    msg["To"] = "klaus@brauerei.invalid"
    msg["From"] = "j-cherino@hsb-boden.com"
    msg["Subject"] = "Industrieboden"
    msg["Message-ID"] = "<test-v1-mid@hsb-boden.com>"
    # Kein X-HSB-Template-ID Header!
    msg.set_content("Alter Text...")
    raw = msg.as_bytes()

    item = {
        "owner": "JOEL",
        "lead_id": "HSB-TEST-002",
        "email": "klaus@brauerei.invalid",
    }

    complete_delivery(
        client=client,
        journal=journal,
        svc=svc,
        spreadsheet_id="fake_sheet",
        headers=headers,
        row=3,
        item=item,
        raw=raw,
        mid="<test-v1-mid@hsb-boden.com>",
        cap=10,
    )

    assert len(svc.call_history) == 2
    final_payload = svc.call_history[1]["data"]
    written_map = {item["range"]: item["values"][0][0] for item in final_payload}

    # Nur die Standard-Felder dürfen geschrieben werden
    assert "ALL_LEADS!I3" not in written_map  # Email_Template_ID
    assert "ALL_LEADS!J3" not in written_map  # Segment
    assert written_map["ALL_LEADS!B3"] == "sent"
