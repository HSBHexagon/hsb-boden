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


def test_smtp_554_unknown_recipient_handled_as_hard_bounce(tmp_path, monkeypatch):
    import smtplib
    monkeypatch.setenv("HSB_CRM_BINDINGS_VERIFIED", "yes")

    journal_path = tmp_path / "journal.db"
    journal = SendJournal(str(journal_path))

    headers = [
        "Lead-ID",
        "Send_Status",
        "Bounce_Status",
        "Suppressed",
        "Suppression_Reason",
        "Versandfreigabe",
        "Last_Send_Attempt_At",
        "Outbound_ID",
        "Sender_Account",
    ]
    svc = FakeSheetsService()
    svc.written["ALL_LEADS!A3:A3"] = [["HSB-TEST-003"]]

    class RejectingClient:
        cfg = {"email": "j-cherino@hsb-boden.com"}
        def deliver_verified_bytes(self, raw, recipient, journal=None):
            raise smtplib.SMTPDataError(554, b"5.7.1 Message cannot be sent. One or more recipients were previously reported as unknown.")

    msg = EmailMessage()
    msg["Message-ID"] = "<test-mid-554@hsb-boden.com>"
    msg.set_content("Text...")
    raw = msg.as_bytes()

    item = {
        "owner": "JOEL",
        "lead_id": "HSB-TEST-003",
        "email": "unknown@mbg-online.net",
    }

    res = complete_delivery(
        client=RejectingClient(),
        journal=journal,
        svc=svc,
        spreadsheet_id="fake_sheet",
        headers=headers,
        row=3,
        item=item,
        raw=raw,
        mid="<test-mid-554@hsb-boden.com>",
        cap=10,
    )

    assert res is False
    # Check that it did not leave unresolved attempt in journal
    assert journal.db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 0
    final_payload = svc.call_history[-1]["data"]
    written_map = {item["range"]: item["values"][0][0] for item in final_payload}
    assert written_map["ALL_LEADS!B3"] == "failed"
    assert written_map["ALL_LEADS!C3"] == "hard_bounce"
    assert written_map["ALL_LEADS!D3"] == "yes"
    assert written_map["ALL_LEADS!E3"] == "PROVIDER_KNOWN_UNKNOWN"
    assert written_map["ALL_LEADS!F3"] == "no"


def test_complete_delivery_broken_pipe_retried(tmp_path, monkeypatch):
    """Prüft, dass BrokenPipeError (z. B. bei OAuth-Token-Refresh) abgefangen und mit frischem Service wiederholt wird."""
    monkeypatch.setenv("HSB_CRM_BINDINGS_VERIFIED", "yes")
    monkeypatch.setattr("outbound_safety.sent_copy_readback", lambda *a: "123")

    db_path = tmp_path / "journal.sqlite"
    journal = SendJournal(str(db_path))

    client = FakeClient()
    svc_healthy = FakeSheetsService()
    svc_healthy.written["ALL_LEADS!A4:A4"] = [["HSB-TEST-RETRY"]]

    class FlakySheetsService:
        attempts = 0
        def spreadsheets(self):
            self.attempts += 1
            if self.attempts == 1:
                raise BrokenPipeError(32, "Broken pipe")
            return svc_healthy.spreadsheets()

    monkeypatch.setattr("sync_to_google_sheet.get_sheets_service", lambda: svc_healthy)

    headers = [
        "Lead-ID",
        "Send_Status",
        "Last_Send_Attempt_At",
        "Outbound_ID",
        "Sender_Account",
        "Send_Datum",
        "Batch_Status",
        "Internet_Message_ID",
    ]
    msg = EmailMessage()
    msg["To"] = "test@retry.invalid"
    msg["From"] = "j-cherino@hsb-boden.com"
    msg["Message-ID"] = "<test-retry@hsb-boden.com>"
    msg.set_content("Text...")
    raw = msg.as_bytes()

    item = {"owner": "JOEL", "lead_id": "HSB-TEST-RETRY", "email": "test@retry.invalid"}

    flaky_svc = FlakySheetsService()
    complete_delivery(
        client=client,
        journal=journal,
        svc=flaky_svc,
        spreadsheet_id="fake_sheet",
        headers=headers,
        row=4,
        item=item,
        raw=raw,
        mid="<test-retry@hsb-boden.com>",
        cap=10,
    )
    assert flaky_svc.attempts >= 1
    assert journal.db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 1
