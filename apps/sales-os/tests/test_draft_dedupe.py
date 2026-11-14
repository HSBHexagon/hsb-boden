"""Duplikat-Bereinigung: genau ein Entwurf je Empfänger, geschützte Kontakte bleiben unberührt."""
import hashlib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser

import pytest

from draft_dedupe import apply_dedupe, plan_dedupe
from draft_upgrade import ARCHIVE, mailbox_arg
from sales_reconciliation import contacted_firm_domains


def _raw(to, mid):
    m = EmailMessage(); m['From'] = 'j-cherino@hsb-boden.com'; m['To'] = to; m['Subject'] = 'S'
    m['Message-ID'] = mid; m.set_content('x')
    return m.as_bytes()


def _rec(uid, to, mid, owner='JOEL', issues=(), template_id='v2-produktion-s1'):
    raw = _raw(to, mid)
    return {'owner': owner, 'uid': str(uid), 'uidvalidity': '7', 'folder': 'Drafts', 'recipients': [to],
            'message_id': mid, 'sha256': hashlib.sha256(raw).hexdigest(), 'issues': list(issues),
            'template_id': template_id, 'internal_test': False, '_raw': raw}


def _lead(email, owner='Joel Cherino Diaz', draft_id=''):
    return {'E-Mail': email, 'Verantwortlicher': owner, 'Draft_ID': draft_id}


def test_keeps_crm_bound_draft_and_archives_the_rest():
    a, b = _rec(1, 'x@firma.de', '<a@h>', issues=['DUPLICATE_DRAFT_RECIPIENT']), _rec(2, 'x@firma.de', '<b@h>', issues=['DUPLICATE_DRAFT_RECIPIENT'])
    plan = plan_dedupe([a, b], [_lead('x@firma.de', draft_id='<a@h>')])
    assert plan['keep'] == [a] and plan['archive'] == [b] and plan['groups_with_duplicates'] == 1


def test_without_binding_prefers_current_repair_copy_then_newest():
    old = _rec(5, 'x@firma.de', '<a@h>', template_id='v2-produktion-reparatur-s1', issues=['OUTDATED_REPAIR_COPY'])
    cur = _rec(3, 'x@firma.de', '<b@h>', template_id='v2-produktion-reparatur-s1')
    plan = plan_dedupe([old, cur], [_lead('x@firma.de')])
    assert plan['keep'] == [cur] and plan['archive'] == [old]


def test_cross_mailbox_duplicate_keeps_crm_owner():
    joel, jordi = _rec(1, 'x@firma.de', '<a@h>'), _rec(9, 'x@firma.de', '<b@h>', owner='JORDI')
    plan = plan_dedupe([joel, jordi], [_lead('x@firma.de')])
    assert plan['keep'] == [joel] and plan['archive'] == [jordi]


@pytest.mark.parametrize('issue', ['ALREADY_CONTACTED', 'ALREADY_CONTACTED_DOMAIN', 'INBOUND_REQUIRES_REVIEW'])
def test_protected_groups_are_never_touched(issue):
    recs = [_rec(1, 'x@firma.de', '<a@h>', issues=[issue]), _rec(2, 'x@firma.de', '<b@h>')]
    plan = plan_dedupe(recs, [_lead('x@firma.de')])
    assert plan['archive'] == [] and plan['keep'] == [] and plan['protected_groups'] == ['x@firma.de']


def test_ambiguous_crm_is_left_alone():
    recs = [_rec(1, 'x@firma.de', '<a@h>'), _rec(2, 'x@firma.de', '<b@h>')]
    plan = plan_dedupe(recs, [_lead('x@firma.de'), _lead('x@firma.de')])
    assert plan['archive'] == [] and plan['ambiguous_groups'] == ['x@firma.de']


def test_single_drafts_and_internal_tests_are_ignored():
    single = _rec(1, 'y@firma.de', '<y@h>')
    test = dict(_rec(2, 'y@firma.de', '<z@h>'), internal_test=True)
    assert plan_dedupe([single, test], [_lead('y@firma.de')])['groups_with_duplicates'] == 0


def test_contacted_domains_skip_freemail_and_own_domains():
    assert contacted_firm_domains({'a@firma.de', 'b@gmail.com', 'c@hsb-boden.de'}) == {'firma.de'}


class FakeImap:
    capabilities = (b'MOVE',)

    def __init__(self, boxes):
        self.boxes, self.folder, self.calls = boxes, None, []

    def __enter__(self): return self
    def __exit__(self, *a): pass

    def select(self, folder, readonly=True):
        self.folder = folder
        return ('OK', [b'1']) if folder in self.boxes else ('NO', [])

    def response(self, key): return key, [b'7']
    def create(self, folder): self.boxes[folder] = {}; return 'OK', []

    def uid(self, verb, *args):
        self.calls.append(verb.upper())
        box = self.boxes[self.folder]
        if verb.lower() == 'fetch':
            return ('OK', [(b'h', box[str(args[0])])]) if str(args[0]) in box else ('OK', [])
        if verb.lower() == 'search':
            mid = str(args[-1]).strip('"')
            hits = [u for u, raw in box.items() if str(BytesParser(policy=policy.default).parsebytes(raw)['Message-ID']) == mid]
            return 'OK', [' '.join(hits).encode()]
        if verb.upper() == 'MOVE':
            uid, dest = args
            self.boxes[dest][str(100 + len(self.boxes[dest]))] = box.pop(str(uid))
            return 'OK', []
        pytest.fail('unexpected ' + verb)


class Client:
    def __init__(self, imap): self.imap = imap
    def _get_imap(self): return self.imap


def test_apply_moves_only_duplicates_never_deletes(tmp_path):
    keep = _rec(1, 'x@firma.de', '<a@h>')
    dup = _rec(2, 'x@firma.de', '<b@h>')
    archive = mailbox_arg(ARCHIVE)
    imap = FakeImap({'Drafts': {'1': keep['_raw'], '2': dup['_raw']}})
    plan = plan_dedupe([keep, dup], [_lead('x@firma.de', draft_id='<a@h>')])
    res = apply_dedupe(plan, {'JOEL': Client(imap)}, tmp_path / 'j.sqlite3')
    assert res['archived'] == 1 and res['customer_emails_sent'] == 0
    assert list(imap.boxes['Drafts']) == ['1'] and list(imap.boxes[archive].values()) == [dup['_raw']]
    assert not {'STORE', 'EXPUNGE', 'APPEND'} & set(imap.calls)
    # Wiederholung ist idempotent.
    again = apply_dedupe(plan, {'JOEL': Client(imap)}, tmp_path / 'j.sqlite3')
    assert again['archived'] == 0 and again['skipped']['ALREADY_DONE'] == 1


def test_apply_skips_draft_changed_since_audit(tmp_path):
    keep, dup = _rec(1, 'x@firma.de', '<a@h>'), _rec(2, 'x@firma.de', '<b@h>')
    imap = FakeImap({'Drafts': {'1': keep['_raw'], '2': _raw('x@firma.de', '<b@h>') + b'changed'}})
    plan = plan_dedupe([keep, dup], [_lead('x@firma.de', draft_id='<a@h>')])
    res = apply_dedupe(plan, {'JOEL': Client(imap)}, tmp_path / 'j.sqlite3')
    assert res['archived'] == 0 and res['skipped']['CHANGED_SINCE_AUDIT'] == 1
    assert set(imap.boxes['Drafts']) == {'1', '2'}


def test_keeper_gone_since_audit_leaves_group_untouched(tmp_path):
    # Codex-Review #465: ohne Prüfung des behaltenen Entwurfs bliebe der Empfänger ohne Entwurf.
    keep, dup = _rec(1, 'x@firma.de', '<a@h>'), _rec(2, 'x@firma.de', '<b@h>')
    imap = FakeImap({'Drafts': {'2': dup['_raw']}})
    plan = plan_dedupe([keep, dup], [_lead('x@firma.de', draft_id='<a@h>')])
    res = apply_dedupe(plan, {'JOEL': Client(imap)}, tmp_path / 'j.sqlite3')
    assert res['archived'] == 0 and res['skipped']['KEEPER_CHANGED_GROUP_UNTOUCHED'] == 1
    assert list(imap.boxes['Drafts']) == ['2'] and 'MOVE' not in imap.calls


def test_keeper_changed_since_audit_leaves_group_untouched(tmp_path):
    keep, dup = _rec(1, 'x@firma.de', '<a@h>'), _rec(2, 'x@firma.de', '<b@h>')
    imap = FakeImap({'Drafts': {'1': keep['_raw'] + b'edited', '2': dup['_raw']}})
    plan = plan_dedupe([keep, dup], [_lead('x@firma.de', draft_id='<a@h>')])
    assert apply_dedupe(plan, {'JOEL': Client(imap)}, tmp_path / 'j.sqlite3')['archived'] == 0
    assert set(imap.boxes['Drafts']) == {'1', '2'}


def test_cross_mailbox_apply_checks_keeper_in_other_mailbox(tmp_path):
    keep, dup = _rec(1, 'x@firma.de', '<a@h>'), _rec(9, 'x@firma.de', '<b@h>', owner='JORDI')
    joel, jordi = FakeImap({'Drafts': {'1': keep['_raw']}}), FakeImap({'Drafts': {'9': dup['_raw']}})
    plan = plan_dedupe([keep, dup], [_lead('x@firma.de', draft_id='<a@h>')])
    res = apply_dedupe(plan, {'JOEL': Client(joel), 'JORDI': Client(jordi)}, tmp_path / 'j.sqlite3')
    assert res['archived'] == 1 and list(joel.boxes['Drafts']) == ['1'] and jordi.boxes['Drafts'] == {}


@pytest.mark.parametrize('field,value', [('Opt-out-Status', 'yes'), ('Suppressed', 'ja'), ('Send_Status', 'sent'),
                                         ('Send_Datum', '2026-10-01')])
def test_crm_blocked_recipients_are_protected(field, value):
    # Codex-Review #465: CRM-Sperren stehen im Audit unter eligibility_reasons, nicht unter issues.
    recs = [_rec(1, 'x@firma.de', '<a@h>'), _rec(2, 'x@firma.de', '<b@h>')]
    plan = plan_dedupe(recs, [dict(_lead('x@firma.de', draft_id='<a@h>'), **{field: value})])
    assert plan['archive'] == [] and plan['protected_groups'] == ['x@firma.de']


def test_eligibility_optout_reason_protects_group():
    recs = [dict(_rec(1, 'x@firma.de', '<a@h>'), eligibility_reasons=['Opt_Out=YES']), _rec(2, 'x@firma.de', '<b@h>')]
    plan = plan_dedupe(recs, [_lead('x@firma.de', draft_id='<a@h>')])
    assert plan['archive'] == [] and plan['reasons']['PROTECTED_CRM_BLOCK'] == 1
