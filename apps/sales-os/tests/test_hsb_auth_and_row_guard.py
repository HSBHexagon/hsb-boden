import pytest

import sync_to_google_sheet as sg
from outbound_safety import assert_row_lead
from operator_layer import crm_dashboard as cd


class _About:
    def __init__(self, email): self.email = email
    def about(self): return self
    def get(self, fields): return self
    def execute(self): return {'user': {'emailAddress': self.email}}


def test_private_account_is_refused(monkeypatch):
    sg._VERIFIED_PRINCIPALS.clear()
    monkeypatch.setattr(sg, 'build', lambda *a, **k: _About('privat@outlook.com'))
    with pytest.raises(RuntimeError, match='CRM_AUTH_NOT_HSB'):
        sg.assert_hsb_principal(object(), 'test-privat')


def test_hsb_account_is_accepted(monkeypatch):
    sg._VERIFIED_PRINCIPALS.clear()
    monkeypatch.setattr(sg, 'build', lambda *a, **k: _About('info@hsb-boden.de'))
    assert sg.assert_hsb_principal(object(), 'test-hsb') == 'info@hsb-boden.de'


def test_default_profile_is_hsb_not_private(monkeypatch):
    seen = {}
    monkeypatch.delenv('HSB_GOOGLE_AUTHORIZED_USER_JSON', raising=False)
    monkeypatch.delenv('HSB_GOOGLE_PROFILE', raising=False)
    monkeypatch.setattr(sg, '_profile_credentials', lambda p: seen.setdefault('profile', p))
    monkeypatch.setattr(sg, 'assert_hsb_principal', lambda c, k: 'info@hsb-boden.de')
    monkeypatch.setattr(sg, 'build', lambda *a, **k: 'svc')
    assert sg.get_sheets_service() == 'svc' and seen['profile'] == 'hsb-boden'


class _Sheet:
    def __init__(self, value): self.value = value
    def spreadsheets(self): return self
    def values(self): return self
    def get(self, spreadsheetId, range): return self
    def execute(self): return {'values': [[self.value]]}


def test_row_guard_blocks_moved_row():
    assert_row_lead(_Sheet('HSB-20260708-00001'), 'x', 5, 'HSB-20260708-00001')
    with pytest.raises(RuntimeError, match='CRM_ROW_MOVED'):
        assert_row_lead(_Sheet('HSB-20260708-00002'), 'x', 5, 'HSB-20260708-00001')


def test_cockpit_formatting_keeps_font_fields_in_text_format():
    for req in cd.formatting_requests(123):
        fmt = req.get('repeatCell', {}).get('cell', {}).get('userEnteredFormat', {})
        assert 'fontSize' not in fmt and 'foregroundColor' not in fmt


def test_reply_formulas_include_apps_script_statuses():
    f = cd.reply_count_formula()
    for status in ('replied', 'replied_interested', 'received', 'reply', 'positive_reply', 'negative_reply'):
        assert f'"{status}"' in f
    for status in ('opt_out', 'bounced', 'auto_reply_ooo'):
        assert f'"{status}"' not in f


@pytest.mark.row_guard
def test_complete_delivery_stops_before_any_write_when_row_moved():
    import outbound_safety

    class Journal:
        def __init__(self): self.events = []
        def reserve(self, *a): self.events.append('reserve')
        def transition(self, *a): self.events.append('transition')

    class Client:
        cfg = {'email': 'j-cherino@hsb-boden.com'}
        def deliver_verified_bytes(self, *a, **k): raise AssertionError('darf nicht senden')

    j = Journal()
    with pytest.raises(RuntimeError, match='CRM_ROW_MOVED'):
        outbound_safety.complete_delivery(Client(), j, _Sheet('HSB-20260708-00999'), 'x', ['Lead-ID'], 5,
                                          {'email': 'a@b.de', 'owner': 'JOEL', 'lead_id': 'HSB-20260708-00001'},
                                          b'raw', '<m@x>', 10)
    assert j.events == []
