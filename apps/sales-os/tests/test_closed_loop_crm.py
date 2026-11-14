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


def test_sync_inbounds_bounce_automatic_rescue(monkeypatch):
    from types import SimpleNamespace
    from closed_loop_crm import sync_inbounds
    from bounce_rescue_agent import RescueResult

    lead = ["L10", "bad@firma.de", "no", "", "", "", "", "Neu", ""]
    headers = ["Lead-ID", "E-Mail", "Versandfreigabe", "Suppressed", "Bounce_Status", "Reply_Status", "Last_Error", "Pipeline", "Notizen"]
    writes = []
    inbox = SimpleNamespace(
        message_id="<bounce10@firma.de>", source="COM_IMAP", owner="JOEL", date="2026-11-06T15:00:00+00:00",
        sender="mailer-daemon@firma.de", subject="Undeliverable: User Unknown",
        body="Final-Recipient: rfc822; bad@firma.de\nAction: failed\nStatus: 5.1.1\nDiagnostic-Code: smtp; 550 User unknown\n",
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

    # Mock BounceRescueAgent.rescue_lead to return a successful rescue
    dummy_rescue = RescueResult(
        status="SUCCESS",
        failed_email="bad@firma.de",
        rescued_email="info@firma.de",
        source_url="https://firma.de/impressum",
        confidence=0.95,
        notes="Alternative E-Mail gefunden"
    )
    monkeypatch.setattr('bounce_rescue_agent.BounceRescueAgent.rescue_lead', lambda self, lead, failed_email=None: dummy_rescue)

    result = sync_inbounds(apply=True, include_de=False)

    assert result['categories'] == {'BOUNCE': 1}
    assert len(writes) == 1
    assert writes[0]['E-Mail'] == 'info@firma.de'
    assert writes[0]['Bounce_Status'] == 'rescued'
    assert writes[0]['Suppressed'] == 'no'
    assert writes[0]['Versandfreigabe'] == 'yes'
    assert writes[0]['Reply_Status'] == 'bounce_rescued'
    assert writes[0]['Pipeline'] == 'Freigegeben'
    assert 'Bounce gerettet' in writes[0]['Notizen']

    # In INBOUND_EVENTS, blocked should be 'no' and reason has [RESCUED -> ...]
    assert values.event[0][8] == 'no'
    assert '[RESCUED -> info@firma.de]' in values.event[0][10]


def test_rescue_crm_bounces(monkeypatch):
    from types import SimpleNamespace
    from closed_loop_crm import rescue_crm_bounces
    from bounce_rescue_agent import RescueResult

    headers = ["Lead-ID", "E-Mail", "Versandfreigabe", "Suppressed", "Bounce_Status", "Reply_Status", "Pipeline", "Notizen"]
    row1 = ["L1", "bad1@firma1.de", "no", "yes", "hard_bounce", "bounced", "Bounce", ""]
    row2 = ["L2", "bad2@firma2.de", "no", "yes", "hard_bounce", "bounced", "Bounce", ""]
    row3 = ["L3", "ok@firma3.de", "yes", "no", "", "", "Freigegeben", ""]
    rows = [headers, row1, row2, row3]

    batch_updates = []

    class Values:
        def get(self, *, range, **_):
            return SimpleNamespace(execute=lambda: {'values': rows})

        def batchUpdate(self, *, body, **_):
            batch_updates.append(body)
            # update rows in place for readback
            for item in body['data']:
                row_idx = int(item['range'].split('!')[1][1:]) - 1
                col_idx = 1 if 'B' in item['range'] else (2 if 'C' in item['range'] else 0)
            return SimpleNamespace(execute=lambda: {})

    service = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: Values()))

    def mock_rescue(self, lead, failed_email=None):
        if failed_email == "bad1@firma1.de":
            return RescueResult(status="SUCCESS", failed_email=failed_email, rescued_email="info@firma1.de", source_url="https://firma1.de", confidence=0.95)
        return RescueResult(status="NO_CANDIDATE", failed_email=failed_email, notes="Keine Adresse gefunden")

    monkeypatch.setattr('bounce_rescue_agent.BounceRescueAgent.rescue_lead', mock_rescue)

    res = rescue_crm_bounces(apply=False, svc=service)
    assert res['scanned_bounces'] == 2
    assert res['rescued_count'] == 1
    assert res['failed_count'] == 1
    assert res['rescued'][0]['to'] == 'info@firma1.de'
    assert len(batch_updates) == 0


def test_approve_verified_drafts(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    from closed_loop_crm import approve_verified_drafts

    headers = ["Lead-ID", "E-Mail", "Verantwortlicher", "Versandfreigabe", "Suppressed", "Opt-out-Status", "Send_Status", "Pipeline"]
    row1 = ["L1", "lead1@example.com", "Joel", "no", "no", "no", "", "Neu"]
    row2 = ["L2", "lead2@example.com", "Joel", "no", "yes", "no", "", "Neu"]  # suppressed -> skip
    row3 = ["L3", "lead3@example.com", "Jordi", "yes", "no", "no", "", "Freigegeben"]  # already approved -> skip
    rows = [headers, row1, row2, row3]

    # Create dummy audit dir
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    drafts = [
        {"technical_ready": True, "internal_test": False, "recipients": ["lead1@example.com"]},
        {"technical_ready": True, "internal_test": False, "recipients": ["lead2@example.com"]},
        {"technical_ready": True, "internal_test": False, "recipients": ["lead3@example.com"]},
    ]
    (audit_dir / "drafts.json").write_text(json.dumps(drafts))

    batch_updates = []

    class Values:
        def get(self, *, range, **_):
            return SimpleNamespace(execute=lambda: {'values': rows})

        def batchUpdate(self, *, body, **_):
            batch_updates.append(body)
            return SimpleNamespace(execute=lambda: {})

    service = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: Values()))

    res = approve_verified_drafts(apply=False, audit_dir=audit_dir, svc=service)
    assert res['drafts_scanned'] == 3
    assert res['eligible_leads'] == 1
    assert res['sample'][0]['lead_id'] == 'L1'
    assert res['sample'][0]['email'] == 'lead1@example.com'

