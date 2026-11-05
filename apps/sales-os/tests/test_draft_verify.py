"""Prüfer: jeder Entwurf gegen ein frisches Rendering, nur Zahlen im Ergebnis."""
import hashlib
import json

import pytest

import draft_verify as dv
from canonical_template_factory import LOGO_URL, REPARATUR_COPY_REV, render_email_v2
from com_mailbox_manager import ComMailboxClient

FREIGABE = {'Versandfreigabe': 'yes', 'Legal_Basis': 'OPT_IN', 'Legal_Evidence': 'Consent record TEST-2026',
            'Legal_Evidence_At': '2026-09-01T10:00:00Z'}
SENDER = {'JOEL': ('Joel Cherino Diaz', 'j-cherino@hsb-boden.com'), 'JORDI': ('Jordie Post', 'j-post@hsb-boden.com')}


def lead(owner='JORDI', nr=1, **extra):
    row = {'Lead-ID': f'HSB-20261105-{nr}', 'E-Mail': f'einkauf{nr}@musterwerk.de', 'Firma': 'Musterwerk GmbH',
           'Branche': 'Lebensmittelproduktion', 'Ansprechpartner': 'Frau Beispiel',
           'Verantwortlicher': SENDER[owner][0], 'Draft_ID': f'<d{nr}@hsb-boden.com>',
           'Email_Template_ID': 'v2-produktion-reparatur-s1', **FREIGABE}
    row.update(extra)
    return row


def client_for(owner):
    client = ComMailboxClient.__new__(ComMailboxClient)
    client.owner = owner
    client.cfg = {'display_name': SENDER[owner][0], 'email': SENDER[owner][1]}
    return client


def raw_for(row, owner='JORDI', rev=REPARATUR_COPY_REV, body_html=None, body_text=None):
    rendered = render_email_v2(row, owner, step=1, variant='reparatur')
    raw, _ = client_for(owner).build_draft_message(
        rendered['to_email'], rendered['subject'],
        body_text=body_text if body_text is not None else rendered['body_text'],
        body_html=body_html if body_html is not None else rendered['body_html'],
        template_id=rendered['template_id'], lead_id=row['Lead-ID'],
        custom_message_id=row['Draft_ID'], copy_rev=rev)
    return raw


def record(row, raw, owner='JORDI', issues=(), uid='1'):
    return {'owner': owner, 'lead_id': row['Lead-ID'], 'message_id': row['Draft_ID'], 'issues': list(issues),
            'sendable': not issues, 'internal_test': False, 'uid': uid, 'uidvalidity': '7',
            'template_id': row['Email_Template_ID'], 'sha256': hashlib.sha256(raw).hexdigest()}


def write_audit(tmp_path, entries, extra_leads=(), balances=()):
    """entries: [(lead, owner, raw, issues)]; legt ein Audit-Verzeichnis wie sales_reconciliation an."""
    rows = [e[0] for e in entries] + list(extra_leads)
    headers = sorted({k for r in rows for k in r})
    (tmp_path / 'crm-original.json').write_text(json.dumps(
        {'valueRanges': [{'values': [headers] + [[r.get(h, '') for h in headers] for r in rows]}]}))
    drafts = []
    for i, (row, owner, raw, issues) in enumerate(entries):
        path = tmp_path / f'{owner}-{i}.eml'
        path.write_bytes(raw)
        drafts.append(dict(record(row, raw, owner, issues, uid=str(i)), path=str(path)))
    (tmp_path / 'drafts.json').write_text(json.dumps(drafts))
    (tmp_path / 'leads.json').write_text(json.dumps(list(balances)))
    return tmp_path


def healthy(tmp_path, **kwargs):
    joel, jordi = lead('JOEL', 1), lead('JORDI', 2)
    return write_audit(tmp_path, [(joel, 'JOEL', raw_for(joel, 'JOEL'), []),
                                  (jordi, 'JORDI', raw_for(jordi, 'JORDI'), [])], **kwargs)


def test_fresh_draft_passes_deep_check():
    row = lead()
    assert dv.deep_check(raw_for(row), row, 'JORDI') == []


def test_stale_name_is_text_differs():
    row = lead()
    raw = raw_for(row)
    assert 'TEXT_DIFFERS' in dv.deep_check(raw, dict(row, Ansprechpartner='Frau Anders'), 'JORDI')


def test_umlauts_and_qp_match():
    row = lead(Ansprechpartner='Frau Müller-Lüdenscheidt', Firma='Bäckerei Größe & Söhne GmbH')
    assert dv.deep_check(raw_for(row), row, 'JORDI') == []


def test_missing_logo_is_flagged():
    row = lead()
    html = render_email_v2(row, 'JORDI', step=1, variant='reparatur')['body_html'].replace(LOGO_URL, 'https://x.invalid/l.png')
    assert 'LOGO_MISSING' in dv.deep_check(raw_for(row, body_html=html), row, 'JORDI')


def test_second_link_is_flagged():
    row = lead()
    html = render_email_v2(row, 'JORDI', step=1, variant='reparatur')['body_html'].replace(
        '</body>', '<a href="https://www.hsb-boden.de/kontakt/">K</a></body>')
    assert 'LINKS_UNEXPECTED' in dv.deep_check(raw_for(row, body_html=html), row, 'JORDI')


def test_old_revision_is_flagged():
    row = lead()
    assert 'REV_WRONG' in dv.deep_check(raw_for(row, rev='2026-11-04'), row, 'JORDI')


def test_stale_crm_template_and_binding_are_flagged():
    row = lead()
    raw = raw_for(row)
    codes = dv.deep_check(raw, dict(row, Email_Template_ID='EMAIL_TEMPLATE_JORDI_PRIMARY', Draft_ID='<x@y>'), 'JORDI')
    assert {'CRM_TEMPLATE_STALE', 'CRM_BINDING_DIFFERS'} <= set(codes)


def test_contacted_outranks_outdated():
    row = lead()
    raw = raw_for(row)
    rec = record(row, raw, issues=['ALREADY_CONTACTED', 'OUTDATED_REPAIR_COPY'])
    assert dv.classify(rec, row, raw) == ('HELD', 'ALREADY_CONTACTED')


def test_ineligible_is_held():
    row = lead(Versandfreigabe='no')
    raw = raw_for(row)
    assert dv.classify(record(row, raw, issues=['OUTDATED_PLANNER_COPY']), row, raw) == ('HELD', 'INELIGIBLE')


def test_company_unverified_is_human_review():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(record(row, raw, issues=['COMPANY_UNVERIFIED']), row, raw) == ('HELD', 'HUMAN_REVIEW')


def test_resaved_is_defect_client_resaved():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(record(row, raw, issues=['LEAD_ID_INFERRED_ONLY']), row, raw) == ('DEFECT', 'CLIENT_RESAVED')


def test_resaved_with_edit_is_held():
    row = lead()
    html = render_email_v2(row, 'JORDI', step=1, variant='reparatur')['body_html'].replace(
        'Schadstelle', 'Von Hand geänderte Stelle', 1)
    raw = raw_for(row, body_html=html)
    assert dv.classify(record(row, raw, issues=['LEAD_ID_INFERRED_ONLY']), row, raw) == ('HELD', 'HUMAN_EDITED')


def test_issue_details_do_not_reach_the_reason():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(record(row, raw, issues=['LINK_BROKEN:www.hsb-boden.de/x']), row, raw) == ('DEFECT', 'LINK_BROKEN')


def test_draft_without_lead_is_a_defect_not_ineligible():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(record(row, raw), None, raw) == ('DEFECT', 'CRM_RECIPIENT_MISSING')
    assert dv.classify(record(row, raw, issues=['CRM_RECIPIENT_AMBIGUOUS']), None, raw) == ('DEFECT', 'CRM_RECIPIENT_AMBIGUOUS')


def test_internal_test_draft_is_held():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(dict(record(row, raw), internal_test=True, sendable=False), None, raw) == ('HELD', 'INTERNAL_TEST')


def test_clean_draft_is_ok():
    row = lead()
    raw = raw_for(row)
    assert dv.classify(record(row, raw), row, raw) == ('OK', '')


def test_healthy_audit_is_perfect(tmp_path):
    result = dv.verify_audit_dir(healthy(tmp_path))
    assert result['verdict'] == 'PERFECT'
    assert result['owners']['JORDI'] == {'scanned': 1, 'ok': 1, 'held': {}, 'defects': {}, 'eligible_without_draft': 0}
    assert result['customer_emails_sent'] == 0


def test_defect_blocks_perfect_and_is_listed_for_refresh(tmp_path):
    joel, jordi = lead('JOEL', 1), lead('JORDI', 2)
    stale = raw_for(jordi, 'JORDI')
    audit = write_audit(tmp_path, [(joel, 'JOEL', raw_for(joel, 'JOEL'), []),
                                   (dict(jordi, Ansprechpartner='Frau Anders'), 'JORDI', stale, [])])
    result = dv.verify_audit_dir(audit)
    assert result['verdict'] == 'NOT_READY'
    assert result['owners']['JORDI']['defects'] == {'TEXT_DIFFERS': 1}
    keys = json.loads((audit / 'deep_defects.json').read_text())
    assert keys == [f"JORDI|7|1|{hashlib.sha256(stale).hexdigest()}"]


def test_eligible_without_draft_blocks_perfect(tmp_path):
    audit = healthy(tmp_path, balances=[{'lead_id': 'HSB-1', 'owner': 'JOEL', 'reasons': ['NO_DRAFT']},
                                        {'lead_id': 'HSB-2', 'owner': 'JOEL', 'reasons': ['NO_DRAFT', 'Opt_Out=YES']}])
    result = dv.verify_audit_dir(audit)
    assert result['verdict'] == 'NOT_READY'
    assert result['owners']['JOEL']['eligible_without_draft'] == 1


@pytest.mark.parametrize('breakage', ['missing_raw', 'empty', 'hash', 'one_owner', 'no_crm'])
def test_incomplete_snapshot_is_never_perfect(tmp_path, breakage, capsys):
    audit = healthy(tmp_path)
    drafts = json.loads((audit / 'drafts.json').read_text())
    if breakage == 'missing_raw':
        (tmp_path / 'JORDI-1.eml').unlink()
    elif breakage == 'empty':
        (audit / 'drafts.json').write_text('[]')
    elif breakage == 'hash':
        drafts[1]['sha256'] = '0' * 64
        (audit / 'drafts.json').write_text(json.dumps(drafts))
    elif breakage == 'one_owner':
        (audit / 'drafts.json').write_text(json.dumps(drafts[:1]))
    else:
        (audit / 'crm-original.json').unlink()
    assert dv.main(['--audit-dir', str(audit)]) == 2
    assert 'PERFECT' not in capsys.readouterr().out


def test_cli_exit_codes(tmp_path, capsys):
    assert dv.main(['--audit-dir', str(healthy(tmp_path))]) == 0
    assert json.loads(capsys.readouterr().out)['verdict'] == 'PERFECT'
    (tmp_path / 'leads.json').write_text(json.dumps([{'owner': 'JOEL', 'reasons': ['NO_DRAFT']}]))
    assert dv.main(['--audit-dir', str(tmp_path)]) == 3


def test_output_has_no_personal_data(tmp_path, capsys):
    joel, jordi = lead('JOEL', 1), lead('JORDI', 2)
    audit = write_audit(tmp_path, [(joel, 'JOEL', raw_for(joel, 'JOEL'), ['LINK_BROKEN:einkauf1@musterwerk.de']),
                                   (jordi, 'JORDI', raw_for(jordi, 'JORDI'), [])])
    dv.main(['--audit-dir', str(audit)])
    out = capsys.readouterr().out
    assert '@' not in out and 'HSB-' not in out and 'Musterwerk' not in out
