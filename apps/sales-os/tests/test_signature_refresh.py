"""Signatur-Austausch in place: gleiche Message-ID, kein CRM-Schreiben, wiederaufnehmbar."""
import hashlib
from contextlib import contextmanager
from email import policy
from email.parser import BytesParser

import pytest

import signature_refresh as sr
from canonical_template_factory import REPARATUR_COPY_REV
from com_mailbox_manager import ComMailboxClient


LEAD = {'Lead-ID': 'HSB-20261105-1', 'E-Mail': 'einkauf@musterwerk.de', 'Email': 'einkauf@musterwerk.de',
        'Firma': 'Musterwerk GmbH', 'Branche': 'Lebensmittelproduktion', 'Ansprechpartner': 'Frau Beispiel',
        'Verantwortlicher': 'Jordie Post', 'Draft_ID': '<alt@hsb-boden.com>',
        'Email_Template_ID': 'v2-produktion-reparatur-s1', 'Versandfreigabe': 'yes',
        'Legal_Basis': 'OPT_IN', 'Legal_Evidence': 'Consent record TEST-2026', 'Legal_Evidence_At': '2026-09-01T10:00:00Z'}


class FakeImap:
    def __init__(self, store):
        self.store = store  # {folder: {uid: raw}}
        self.selected = None
        self.capabilities = ('IMAP4REV1', 'MOVE')
        self.moves = 0

    def select(self, folder, readonly=True):
        if folder not in self.store:
            return 'NO', [b'']
        self.selected = folder
        return 'OK', [b'1']

    def response(self, name):
        return name, [b'7']

    def create(self, folder):
        self.store.setdefault(folder, {})
        return 'OK', [b'']

    def uid(self, cmd, *args):
        box = self.store[self.selected]
        if cmd == 'search':
            mid = args[-1].strip('"').encode()
            hits = [u for u, raw in box.items() if b'Message-ID: ' + mid in raw]
            return 'OK', [b' '.join(str(u).encode() for u in sorted(hits))]
        if cmd == 'fetch':
            return 'OK', [(b'1', box[int(args[0])])]
        if cmd == 'move':
            raw = box.pop(int(args[0]))
            self.store.setdefault('ARCHIV', {})[int(args[0])] = raw
            self.moves += 1
            return 'OK', [b'']
        raise AssertionError(cmd)

    def append(self, folder, flags, date, raw):
        box = self.store[folder]
        box[max(box) + 1] = raw
        return 'OK', [b'']

    def logout(self):
        pass


class FakeClient(ComMailboxClient):
    def __init__(self, owner, store):
        self.owner = owner
        self.cfg = {'display_name': 'Jordie Post', 'email': 'j-post@hsb-boden.com'}
        self.store = store

    def _get_imap(self):
        return FakeImap(self.store)


@contextmanager
def no_lock(client, release_on_error=False):
    yield


def old_draft():
    client = FakeClient('JORDI', {})
    raw, _ = client.build_draft_message(LEAD['E-Mail'], 'Alt', body_text='Sehr geehrte Frau Beispiel,\n\nalt\n',
                                        template_id=LEAD['Email_Template_ID'], lead_id=LEAD['Lead-ID'],
                                        custom_message_id=LEAD['Draft_ID'], copy_rev='2026-11-04')
    return sr._crlf(raw)


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(sr, 'mailbox_arg', lambda v: 'ARCHIV')
    import outbound_safety
    monkeypatch.setattr(outbound_safety, 'mailbox_dispatch_lock', no_lock)
    raw = old_draft()
    store = {'Drafts': {1: raw}, 'ARCHIV': {}}
    rec = {'owner': 'JORDI', 'folder': 'Drafts', 'uidvalidity': '7', 'uid': '1', 'lead_id': LEAD['Lead-ID'],
           'message_id': LEAD['Draft_ID'], 'template_id': LEAD['Email_Template_ID'],
           'sha256': hashlib.sha256(raw).hexdigest(), 'issues': ['OUTDATED_REPAIR_COPY']}
    return store, rec


def run(store, rec, apply=True):
    return sr.refresh_signatures(['JORDI'], [rec], [dict(LEAD)], apply=apply,
                                 make_client=lambda o: FakeClient(o, store),
                                 assess_message=lambda raw, owner, leads: {'issues': []}, connections=2)


def test_refresh_keeps_message_id_and_archives_original(setup):
    store, rec = setup
    result = run(store, rec)
    assert result['per_owner']['JORDI']['outcomes'] == {'REFRESHED': 1}
    assert result['crm_writes'] == 0 and result['customer_emails_sent'] == 0
    assert list(store['ARCHIV']) == [1]
    [new] = store['Drafts'].values()
    msg = BytesParser(policy=policy.default).parsebytes(new)
    assert msg['Message-ID'] == LEAD['Draft_ID']
    assert msg['X-HSB-Copy-Rev'] == REPARATUR_COPY_REV
    assert 'hsb-boden-logo.png' in new.decode('utf-8', 'replace')


def test_dry_run_changes_nothing(setup):
    store, rec = setup
    before = {k: dict(v) for k, v in store.items()}
    result = run(store, rec, apply=False)
    assert result['per_owner']['JORDI']['selected'] == 1
    assert store == before


def test_resume_after_append_moves_only_original(setup):
    store, rec = setup
    new_raw, _ = sr.build_replacement(FakeClient('JORDI', store), 'JORDI', dict(LEAD), LEAD['Draft_ID'])
    store['Drafts'][2] = new_raw  # Abbruch zwischen APPEND und MOVE
    result = run(store, rec)
    assert result['per_owner']['JORDI']['outcomes'] == {'RECOVERED': 1}
    assert store['Drafts'] == {2: new_raw}
    assert list(store['ARCHIV']) == [1]


def test_changed_original_is_left_alone(setup):
    store, rec = setup
    rec['sha256'] = '0' * 64
    result = run(store, rec)
    assert result['per_owner']['JORDI']['outcomes'] == {'CHANGED_ORIGINAL_HASH': 1}
    assert list(store['Drafts']) == [1] and not store['ARCHIV']


@pytest.mark.parametrize('change,reason', [
    ({'issues': ['OUTDATED_REPAIR_COPY', 'WRONG_OWNER']}, 'OTHER_ISSUES'),
    ({'message_id': '<anders@hsb-boden.com>'}, 'CRM_BINDING_DIFFERS'),
    ({'template_id': 'v2-produktion-reparatur-s2'}, 'NOT_FIRST_CONTACT'),
    ({'issues': []}, None),
])
def test_only_exactly_bound_outdated_first_contacts(setup, change, reason):
    store, rec = setup
    rec.update(change)
    chosen, skipped = sr.select_candidates('JORDI', [rec], [dict(LEAD)])
    assert not chosen
    if reason:
        assert skipped[reason] == 1


def test_invalid_twin_stops(setup):
    store, rec = setup
    store['Drafts'][2] = old_draft()
    with pytest.raises(RuntimeError, match='TWIN_DRAFT_INVALID'):
        sr.refresh_signatures(['JORDI'], [rec], [dict(LEAD)], apply=True,
                              make_client=lambda o: FakeClient(o, store),
                              assess_message=lambda raw, owner, leads: {'issues': ['X']}, connections=1)


def test_ineligible_lead_is_skipped(setup):
    store, rec = setup
    chosen, skipped = sr.select_candidates('JORDI', [rec], [dict(LEAD, Versandfreigabe='no')])
    assert not chosen and skipped['INELIGIBLE'] == 1


def test_outdated_planner_copy_is_refreshed_too(setup):
    store, rec = setup
    rec['issues'] = ['OUTDATED_PLANNER_COPY', 'OUTDATED_REPAIR_COPY']
    chosen, _ = sr.select_candidates('JORDI', [rec], [dict(LEAD)])
    assert len(chosen) == 1


def test_outdated_repair_draft_with_repair_link_has_no_link_issue(monkeypatch):
    import canonical_template_factory as ctf
    import sales_reconciliation
    from canonical_template_factory import render_email_v2
    lead = dict(LEAD)
    r = render_email_v2(lead, 'JORDI', step=1, variant='reparatur')
    client = FakeClient('JORDI', {})
    raw, _ = client.build_draft_message(r['to_email'], r['subject'], body_text=r['body_text'], body_html=r['body_html'],
                                        template_id=r['template_id'], lead_id=lead['Lead-ID'],
                                        custom_message_id=lead['Draft_ID'], copy_rev='2026-11-04')
    issues = sales_reconciliation.assess_message(raw, 'JORDI', [lead])['issues']
    assert 'OUTDATED_REPAIR_COPY' in issues
    assert 'V2_LINK_INVALID' not in issues



class FakeSheets:
    """Minimal values()-API über ein Dict {(col, row): value}."""
    def __init__(self, cells):
        self.cells = cells
        self.calls = []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def batchGet(self, spreadsheetId, ranges):
        self.calls.append('get')
        out = []
        for r in ranges:
            ref = r.split('!')[1]
            col = ''.join(c for c in ref if c.isalpha()); row = int(''.join(c for c in ref if c.isdigit()))
            v = self.cells.get((col, row))
            out.append({'values': [[v]]} if v is not None else {})
        return type('R', (), {'execute': lambda _s: {'valueRanges': out}})()

    def batchUpdate(self, spreadsheetId, body):
        self.calls.append('update')
        for d in body['data']:
            ref = d['range'].split('!')[1]
            col = ''.join(c for c in ref if c.isalpha()); row = int(''.join(c for c in ref if c.isdigit()))
            self.cells[(col, row)] = d['values'][0][0]
        return type('R', (), {'execute': lambda _s: {}})()


HEADERS = ['Lead-ID'] + [f'c{i}' for i in range(30)] + ['Email_Template_ID']  # Vorlage in Spalte AF


def test_old_planner_template_is_switched_in_place_and_crm_updated(setup):
    store, rec = setup
    planner = dict(LEAD, Branche='Architekturbüro', Email_Template_ID='v2-architekten-s1', _row=7)
    rec.update(template_id='v2-architekten-s1', issues=['OUTDATED_PLANNER_COPY'])
    sheets = FakeSheets({('A', 7): planner['Lead-ID'], ('AF', 7): 'v2-architekten-s1'})
    result = sr.refresh_signatures(['JORDI'], [rec], [planner], apply=True,
                                   make_client=lambda o: FakeClient(o, store),
                                   assess_message=lambda raw, owner, leads: {'issues': []}, connections=1,
                                   svc=sheets, spreadsheet_id='x', headers=HEADERS)
    assert result['per_owner']['JORDI']['outcomes'] == {'REFRESHED': 1}
    [new] = store['Drafts'].values()
    msg = BytesParser(policy=policy.default).parsebytes(new)
    assert msg['Message-ID'] == LEAD['Draft_ID']
    assert msg['X-HSB-Template-ID'] == 'v2-architekten-reparatur-s1'
    assert sheets.cells[('AF', 7)] == 'v2-architekten-reparatur-s1'
    assert result['crm_writes'] == 1 and sheets.calls == ['get', 'update', 'get']


def test_current_draft_with_stale_crm_template_is_crm_only(setup):
    store, rec = setup
    lead = dict(LEAD, Email_Template_ID='EMAIL_TEMPLATE_JORDI_PRIMARY', _row=9)
    rec.update(issues=[])
    chosen, _ = sr.select_candidates('JORDI', [rec], [lead])
    assert [m for _, _, m in chosen] == [False]
    sheets = FakeSheets({('A', 9): lead['Lead-ID'], ('AF', 9): 'EMAIL_TEMPLATE_JORDI_PRIMARY'})
    before = dict(store['Drafts'])
    result = sr.refresh_signatures(['JORDI'], [rec], [lead], apply=True,
                                   make_client=lambda o: FakeClient(o, store),
                                   assess_message=lambda raw, owner, leads: {'issues': []},
                                   svc=sheets, spreadsheet_id='x', headers=HEADERS)
    assert store['Drafts'] == before
    assert sheets.cells[('AF', 9)] == 'v2-produktion-reparatur-s1' and result['crm_writes'] == 1


def test_crm_write_stops_when_row_identity_changed():
    sheets = FakeSheets({('A', 5): 'HSB-ANDERER', ('AF', 5): 'alt'})
    with pytest.raises(RuntimeError, match='CRM_ROW_IDENTITY_CHANGED'):
        sr.write_crm_templates(sheets, 'x', HEADERS, [(5, 'HSB-20261105-1', 'v2-produktion-reparatur-s1')])
    assert sheets.cells[('AF', 5)] == 'alt'


def test_crm_binding_by_other_draft_is_skipped(setup):
    store, rec = setup
    chosen, skipped = sr.select_candidates('JORDI', [rec], [dict(LEAD, Draft_ID='<andere@hsb-boden.com>')])
    assert not chosen and skipped['CRM_BINDING_DIFFERS'] == 1


def test_deep_defect_is_refreshed(setup):
    store, rec = setup
    rec['issues'] = []
    key = f"{rec['owner']}|{rec['uidvalidity']}|{rec['uid']}|{rec['sha256']}"
    result = sr.refresh_signatures(['JORDI'], [rec], [dict(LEAD)], apply=True,
                                   make_client=lambda o: FakeClient(o, store),
                                   assess_message=lambda raw, owner, leads: {'issues': []}, connections=1,
                                   deep_defects=frozenset({key}))
    assert result['per_owner']['JORDI']['outcomes'] == {'REFRESHED': 1}
    [new] = store['Drafts'].values()
    msg = BytesParser(policy=policy.default).parsebytes(new)
    assert msg['Message-ID'] == LEAD['Draft_ID']
    assert msg['X-HSB-Copy-Rev'] == REPARATUR_COPY_REV


def test_deep_defect_cap_stops(setup):
    store, rec = setup
    rec['issues'] = []
    before = {k: dict(v) for k, v in store.items()}
    many = frozenset(f'JORDI|7|{i}|{"a" * 64}' for i in range(51))
    with pytest.raises(RuntimeError, match='DEEP_DEFECT_CAP_EXCEEDED'):
        sr.refresh_signatures(['JORDI'], [rec], [dict(LEAD)], apply=True,
                              make_client=lambda o: FakeClient(o, store),
                              assess_message=lambda raw, owner, leads: {'issues': []},
                              deep_defects=many)
    assert store == before


def test_blocked_lead_is_not_refreshed(setup):
    store, rec = setup
    rec['issues'] = []
    key = f"{rec['owner']}|{rec['uidvalidity']}|{rec['uid']}|{rec['sha256']}"
    chosen, skipped = sr.select_candidates('JORDI', [rec], [dict(LEAD, Versandfreigabe='no')],
                                           deep_defects=frozenset({key}))
    assert not chosen and skipped['INELIGIBLE'] == 1
