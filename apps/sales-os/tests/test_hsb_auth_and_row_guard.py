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
    class C:
        refresh_token = 'rt'
    monkeypatch.setattr(sg, '_profile_credentials', lambda p: (seen.setdefault('profile', p), C())[1])
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
def test_complete_delivery_stops_before_any_write_when_row_moved(monkeypatch):
    monkeypatch.setenv('HSB_CRM_BINDINGS_VERIFIED', 'yes')
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



@pytest.mark.row_guard
def test_send_write_uses_lead_binding_not_row_number(monkeypatch):
    """Die Bindung entsteht einmal vor reserve(); Versand-Writes schreiben nur noch über sie."""
    import outbound_safety, crm_bindings
    calls = []
    monkeypatch.setattr(crm_bindings, 'ensure_bindings', lambda svc, sid, **k: calls.append(('bind', k['only'], k['apply'])))
    monkeypatch.setattr(outbound_safety, 'crm_write_lead_readback', lambda svc, sid, lead, fields: calls.append(('write', lead, fields)))
    outbound_safety._send_write('svc', 'sid', ['Lead-ID'], 999, 'HSB-20260708-00001', {'Send_Status': 'sent'})
    assert calls == [('write', 'HSB-20260708-00001', {'Send_Status': 'sent'})]


@pytest.mark.row_guard
def test_binding_is_prepared_once_before_reservation(monkeypatch):
    import outbound_safety
    monkeypatch.setenv('HSB_CRM_BINDINGS_VERIFIED', 'yes')
    events = []
    monkeypatch.setattr(outbound_safety, 'prepare_lead_binding', lambda svc, sid, lead: events.append('bind'))
    monkeypatch.setattr(outbound_safety, '_send_write', lambda *a: events.append('write'))

    class Journal:
        def reserve(self, *a): events.append('reserve')
        def transition(self, *a): raise RuntimeError('STOP_AFTER_FIRST_WRITE')

    class Client:
        cfg = {'email': 'j-cherino@hsb-boden.com'}

    with pytest.raises(RuntimeError, match='STOP_AFTER_FIRST_WRITE'):
        outbound_safety.complete_delivery(Client(), Journal(), _Sheet('HSB-20260708-00001'), 'x', ['Lead-ID'], 5,
                                          {'email': 'a@b.de', 'owner': 'JOEL', 'lead_id': 'HSB-20260708-00001'},
                                          b'raw', '<m@x>', 10)
    assert events == ['bind', 'reserve', 'write']


def test_principal_cache_is_bound_to_the_credential_not_the_profile_name(monkeypatch):
    class C:
        def __init__(self, rt): self.refresh_token = rt
    keys = []
    monkeypatch.delenv('HSB_GOOGLE_AUTHORIZED_USER_JSON', raising=False)
    monkeypatch.setattr(sg, 'build', lambda *a, **k: 'svc')
    monkeypatch.setattr(sg, 'assert_hsb_principal', lambda c, k: keys.append(k))
    for rt in ('token-a', 'token-b'):
        monkeypatch.setattr(sg, '_profile_credentials', lambda p, rt=rt: C(rt))
        sg.get_sheets_service()
    assert keys[0] != keys[1]



@pytest.mark.row_guard
def test_missing_canary_stops_before_journal_reservation(monkeypatch):
    import outbound_safety
    monkeypatch.delenv('HSB_CRM_BINDINGS_VERIFIED', raising=False)

    class Journal:
        events = []
        def reserve(self, *a): self.events.append('reserve')

    with pytest.raises(RuntimeError, match='CRM_STABLE_BINDING_CANARY_REQUIRED'):
        outbound_safety.complete_delivery(object(), Journal(), _Sheet('HSB-20260708-00001'), 'x', ['Lead-ID'], 5,
                                          {'email': 'a@b.de', 'owner': 'JOEL', 'lead_id': 'HSB-20260708-00001'},
                                          b'raw', '<m@x>', 10)
    assert Journal.events == []


@pytest.mark.row_guard
@pytest.mark.parametrize('failure', ['CRM_METADATA_CAPACITY:29990+20>30000', 'CRM_STABLE_LEAD_BINDING_REQUIRED'])
def test_binding_failure_stops_before_journal_reservation(monkeypatch, failure):
    """Bindung anlegen und Eindeutigkeit prüfen gehören vor reserve(): sonst blockiert ein RESERVED-Rest jeden Folgeversand."""
    import outbound_safety, crm_bindings
    monkeypatch.setenv('HSB_CRM_BINDINGS_VERIFIED', 'yes')
    def fail(*a, **k): raise RuntimeError(failure)
    if failure.startswith('CRM_METADATA'):
        monkeypatch.setattr(crm_bindings, 'ensure_bindings', fail)
    else:
        monkeypatch.setattr(crm_bindings, 'ensure_bindings', lambda svc, sid, **k: {'conflicts': 0, 'skipped_duplicate': 0, 'skipped_invalid': 0})
        monkeypatch.setattr(outbound_safety, 'require_stable_crm_binding', fail)

    class Journal:
        def __init__(self): self.events = []
        def reserve(self, *a): self.events.append('reserve')
        def transition(self, *a): self.events.append('transition')

    j = Journal()
    with pytest.raises(RuntimeError, match=failure.split(':')[0]):
        outbound_safety.complete_delivery(object(), j, _Sheet('HSB-20260708-00001'), 'x', ['Lead-ID'], 5,
                                          {'email': 'a@b.de', 'owner': 'JOEL', 'lead_id': 'HSB-20260708-00001'},
                                          b'raw', '<m@x>', 10)
    assert j.events == []


@pytest.mark.row_guard
@pytest.mark.parametrize('field', ['conflicts', 'skipped_duplicate', 'skipped_invalid'])
def test_binding_that_was_silently_skipped_is_refused(monkeypatch, field):
    import outbound_safety, crm_bindings
    result = {'conflicts': 0, 'skipped_duplicate': 0, 'skipped_invalid': 0, field: 1}
    monkeypatch.setattr(crm_bindings, 'ensure_bindings', lambda svc, sid, **k: result)
    monkeypatch.setattr(outbound_safety, 'require_stable_crm_binding', lambda *a: {'ok': 1})
    with pytest.raises(RuntimeError, match='CRM_LEAD_BINDING_NOT_CREATED'):
        outbound_safety.prepare_lead_binding('svc', 'sid', 'HSB-20260708-00001')
