from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from closed_loop_crm import compute_lead_update
from inbound_classifier import InboundClassificationResult

def test_compute_lead_update_bounce():
    cls_res = InboundClassificationResult(category="BOUNCE", confidence=0.95, reason="User unknown")
    upd = compute_lead_update(row_idx=15, lead_id="LEAD-101", cls_res=cls_res)
    assert upd["optout_val"] is None
    assert upd["reply_status"] == "bounced"
    assert upd["pipeline_val"] == "Zustellmeldung / Prüfung"

def test_compute_lead_update_ooo_with_date():
    cls_res = InboundClassificationResult(category="OOO_URLAUB", confidence=0.92, recontact_date="2026-11-05")
    upd = compute_lead_update(row_idx=20, lead_id="LEAD-202", cls_res=cls_res)
    assert upd["optout_val"] is None
    assert upd["reply_status"] == "auto_reply_ooo"
    assert "Wiedervorlage 2026-11-05" in upd["pipeline_val"]

def test_compute_lead_update_hot_lead():
    cls_res = InboundClassificationResult(category="HOT_LEAD", confidence=0.88, reason="Besichtigung gewünscht")
    upd = compute_lead_update(row_idx=35, lead_id="LEAD-303", cls_res=cls_res)
    assert upd["reply_status"] == "replied_interested"
    assert "HOT LEAD" in upd["pipeline_val"]

def test_compute_lead_update_optout():
    cls_res = InboundClassificationResult(category="OPTOUT", confidence=0.90, reason="Widerspruch")
    upd = compute_lead_update(row_idx=42, lead_id="LEAD-404", cls_res=cls_res)
    assert upd["optout_val"] == "YES"
    assert upd["reply_status"] == "opt_out"
    assert upd["pipeline_val"] == "Abgemeldet / Widerspruch"


def test_policy_report_holds_address_without_recording_a_hard_bounce(monkeypatch):
    from types import SimpleNamespace

    from closed_loop_crm import sync_inbounds

    lead = ["L1", "person@example.test", "yes", "", "", "", ""]
    headers = ["Lead-ID", "E-Mail", "Versandfreigabe", "Suppressed", "Bounce_Status", "Reply_Status", "Last_Error"]
    writes = []
    inbox = SimpleNamespace(
        message_id="<dsn@example.test>", source="COM_IMAP", owner="JOEL", date="2026-11-06T15:00:00+00:00",
        sender="mailer-daemon@example.test", subject="Undeliverable",
        body="Final-Recipient: rfc822; person@example.test\nAction: failed\nStatus: 5.7.51\n",
    )

    class Values:
        event = []

        def get(self, *, range, **_):
            rows = [headers, lead] if range.startswith('ALL_LEADS') else self.event
            return SimpleNamespace(execute=lambda: {'values': rows})

        def append(self, *, body, **_):
            self.event = body['values']
            return SimpleNamespace(execute=lambda: {'updates': {'updatedRange': 'INBOUND_EVENTS!A2:M2'}})

    values = Values()
    service = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values))
    monkeypatch.setattr('sync_to_google_sheet.get_sheets_service', lambda: service)
    monkeypatch.setattr('dual_domain_collector.collect_all_inbounds', lambda **_: [inbox])
    monkeypatch.setattr('outbound_safety.crm_write_readback', lambda *args: writes.append(args[-1]))

    result = sync_inbounds(apply=True, include_de=False)

    assert result['categories'] == {'BOUNCE': 1}
    assert writes[0]['Versandfreigabe'] == 'no'
    assert writes[0]['Bounce_Status'] == 'bounce_review'
    assert writes[0]['Last_Error'] == 'policy_block'
    assert 'Suppressed' not in writes[0]
    assert 'Last_Reply_At' not in writes[0]
