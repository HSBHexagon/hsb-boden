"""Safety regressions: unproven permissions and ambiguous SMTP must fail closed."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from hsb_core import check_eligibility


def lead(**overrides):
    row = {'Lead-ID': 'L1', 'E-Mail': 'buyer@example.org', 'Firma': 'Example GmbH',
           'Verantwortlicher': 'Joel Cherino Diaz', 'Legal_Basis': 'OPT_IN',
           'Versandfreigabe': 'yes', 'Legal_Evidence': 'consent-record-123',
           'Legal_Evidence_At': '2026-10-20T10:00:00Z', 'Send_Status': 'drafted'}
    row.update(overrides)
    return row


@pytest.mark.parametrize('basis', ['OWNER_APPROVED', 'CONTRACT_APPROVED'])
def test_operator_flag_is_not_recipient_evidence(basis):
    assert not check_eligibility(lead(Legal_Basis=basis)).eligible


@pytest.mark.parametrize('field,value', [
    ('Legal_Evidence', ''), ('Legal_Evidence_At', ''),
    ('Legal_Evidence', 'OWNER_APPROVED'), ('Legal_Evidence_At', '2099-01-01'),
    ('Suppression_Reason', 'opt out'), ('Last_Send_Attempt_At', '2026-10-25'),
    ('Reply_Status', 'replied'), ('Send_Status', 'SMTP_UNKNOWN')])
def test_missing_evidence_and_uncertain_or_suppressed_history_block(field, value):
    assert not check_eligibility(lead(**{field: value})).eligible


def test_valid_evidence_can_pass_without_inventing_permission():
    assert check_eligibility(lead()).eligible


def test_imap_duplicate_recipient_is_ambiguous_even_with_different_lead_ids():
    from sales_reconciliation import assess_message
    from email.message import EmailMessage
    m = EmailMessage()
    m['From'] = 'j-cherino@hsb-boden.com'
    m['To'] = 'buyer@example.org'
    m['Subject'] = 'Example GmbH'
    m['Message-ID'] = '<draft@example.org>'
    m.set_content('Example GmbH https://www.hsb-boden.de/flyer https://www.hsb-boden.de/abmelden?email=buyer%40example.org')
    a = assess_message(m.as_bytes(), 'JOEL', [lead(), lead(**{'Lead-ID': 'L2'})])
    assert 'CRM_RECIPIENT_AMBIGUOUS' in a['issues']


def test_journal_reservation_survives_process_restart(tmp_path):
    from outbound_safety import SendJournal
    p = tmp_path / 'outbound.sqlite3'
    j = SendJournal(p)
    j.reserve('JOEL', 'L1', 'buyer@example.org', '<one@example.org>', 35)
    j.close()
    k = SendJournal(p)
    with pytest.raises(RuntimeError, match='DUPLICATE|UNRESOLVED'):
        k.reserve('JORDI', 'L2', 'buyer@example.org', '<two@example.org>', 35)


def test_daily_cap_persists_across_runs(tmp_path):
    from outbound_safety import SendJournal
    j = SendJournal(tmp_path / 'outbound.sqlite3')
    j.reserve('JOEL', 'L1', 'one@example.org', '<one@example.org>', 1)
    j.transition('one@example.org', 'VERIFIED')
    with pytest.raises(RuntimeError, match='DAILY_CAP'):
        j.reserve('JOEL', 'L2', 'two@example.org', '<two@example.org>', 1)


@pytest.mark.parametrize('failure,expected_smtp', [('crm_intent',0),('smtp_timeout',1),('sent_copy',1),('crm_final',1)])
def test_delivery_failures_leave_durable_stop_and_never_retry(tmp_path,monkeypatch,failure,expected_smtp):
    import outbound_safety as safety
    from types import SimpleNamespace
    calls=[];writes=[]
    def deliver(*args,**kwargs):
        calls.append('SMTP')
        if failure=='smtp_timeout':raise TimeoutError('possibly accepted')
    def write(*args):
        writes.append(args[-1])
        if (failure=='crm_intent' and len(writes)==1) or (failure=='crm_final' and len(writes)==2):
            raise RuntimeError('readback mismatch')
    def sent(*args):
        if failure=='sent_copy':raise RuntimeError('append/readback failed')
    monkeypatch.setattr(safety,'crm_write_readback',write)
    monkeypatch.setattr(safety,'sent_copy_readback',sent)
    client=SimpleNamespace(cfg={'email':'j-cherino@hsb-boden.com'},deliver_verified_bytes=deliver)
    path=tmp_path/'attempts.sqlite3';j=safety.SendJournal(path)
    with pytest.raises((RuntimeError,TimeoutError)):
        safety.complete_delivery(client,j,None,'sheet',[],2,
            {'email':'buyer@example.org','owner':'JOEL','lead_id':'L1'},b'mime','<one@example.org>',35)
    j.close();again=safety.SendJournal(path)
    with pytest.raises(RuntimeError,match='UNRESOLVED|DUPLICATE'):
        again.reserve('JOEL','L1','buyer@example.org','<two@example.org>',35)
    assert len(calls)==expected_smtp


def test_real_company_matching_its_domain_is_not_a_freemail_name():
    assert check_eligibility(lead(Firma='Example')).eligible


def test_live_optout_cannot_be_masked_by_an_alias():
    assert not check_eligibility(lead(Opt_Out='no', **{'Opt-out-Status':'yes'})).eligible


def test_draft_target_blocks_more_generation_without_any_write():
    from com_mailbox_manager import ComMailboxClient
    client=object.__new__(ComMailboxClient);client.cfg={'drafts_folder':'Drafts'}
    class Imap:
        def select(self,folder,readonly):
            assert readonly is True
            return 'OK',[b'50']
        def uid(self,*args):return 'OK',[b' '.join(str(i).encode() for i in range(1,51))]
    with pytest.raises(RuntimeError,match='DRAFT_TARGET_ALREADY_MET'):
        client._assert_draft_capacity(Imap(),['buyer@example.org'])


def test_new_com_message_has_alternatives_links_and_no_pdf_or_reply_to():
    from com_mailbox_manager import ComMailboxClient
    from email.parser import BytesParser
    from email import policy
    client=ComMailboxClient('JOEL')
    raw,_=client.build_draft_message('buyer@example.org','Example GmbH',
        '<p>Example GmbH</p><a href="https://www.hsb-boden.de/flyer?lead=HSB-20260708-00001">Flyer</a>')
    msg=BytesParser(policy=policy.default).parsebytes(raw)
    assert msg.get('Reply-To') is None
    assert msg.get_body(('plain',)) is not None and msg.get_body(('html',)) is not None
    assert not list(msg.iter_attachments())
    assert msg['X-HSB-Lead-ID']=='HSB-20260708-00001'
    assert 'https://www.hsb-boden.de/flyer' in msg.get_body(('plain',)).get_content()


def test_legacy_customer_transport_cannot_bypass_gate(monkeypatch):
    from com_mailbox_manager import ComMailboxClient
    monkeypatch.setenv('HSB_INTERNAL_TEST_SEND_ENABLED','yes')
    client=ComMailboxClient('JOEL')
    with pytest.raises(PermissionError,match='verified dispatch queue'):
        client.send_message('buyer@example.org','subject','<p>body</p>')


def test_daily_count_uses_berlin_date_and_original_sender():
    from outbound_safety import count_owner_attempts_today
    from datetime import date
    rows=[{'Verantwortlicher':'Jordie Post','Sender_Account':'j-cherino@hsb-boden.com',
        'Last_Send_Attempt_At':'2026-10-25T23:30:00+00:00'}]
    assert count_owner_attempts_today(rows,'JOEL',date(2026,10,26))==1
    assert count_owner_attempts_today(rows,'JORDI',date(2026,10,26))==0


def test_audit_holds_historical_reply_to_before_dispatch():
    from sales_reconciliation import assess_message
    from email.message import EmailMessage
    m=EmailMessage();m['From']='j-cherino@hsb-boden.com';m['To']='buyer@example.org'
    m['Subject']='Example GmbH';m['Message-ID']='<old@example.org>'
    m['Reply-To']='j-cherino@hsb-boden.de';m['X-HSB-Lead-ID']='L1'
    m.set_content('Example GmbH https://www.hsb-boden.de/flyer https://www.hsb-boden.de/abmelden?email=buyer%40example.org')
    assert 'HISTORICAL_VARIANT_REQUIRES_REVIEW' in assess_message(m.as_bytes(),'JOEL',[lead()])['issues']


def test_missing_rfc_message_id_uses_stable_namespaced_original_hash():
    from com_mailbox_manager import stable_inbound_id
    raw=b'From: sender@example.org\r\n\r\nPlease unsubscribe'
    assert stable_inbound_id(raw,'JOEL')==stable_inbound_id(raw,'JOEL')
    assert stable_inbound_id(raw,'JOEL')!=stable_inbound_id(raw,'JORDI')
    assert stable_inbound_id(raw,'JOEL','<rfc@example.org>')=='<rfc@example.org>'


def test_confirmed_sent_evidence_records_history_without_granting_permission():
    from closed_loop_crm import select_sent_evidence
    item=lead(**{'_row':2,'Send_Status':'drafted','Legal_Basis':'UNKNOWN'})
    msg={'from':'j-post@hsb-boden.com','to':'buyer@example.org',
         'internet_message_id':'<sent@example.org>','date_str':'Mon, 26 Oct 2026 10:00:00 +0000'}
    rows=select_sent_evidence([msg],[item])
    assert rows[0]['updates']['Send_Status']=='sent'
    assert rows[0]['updates']['Sender_Account']=='j-post@hsb-boden.com'
    assert rows[0]['updates']['Internet_Message_ID']=='<sent@example.org>'
    assert 'Legal_Basis' not in rows[0]['updates'] and 'Versandfreigabe' not in rows[0]['updates']
    assert select_sent_evidence([dict(msg,**{'from':'other@example.org'})],[item])==[]
    assert select_sent_evidence([msg],[dict(item,Send_Status='sent')])==[]
