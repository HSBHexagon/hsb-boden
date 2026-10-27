from datetime import date
import pytest
from sequence import next_step_due, reply_actions, SequenceJournal


def rows():
    return [{'lead_id':'L1','step':1,'sent_at':'2026-10-19','state':'VERIFIED'}]


def test_four_workdays_and_history_required():
    lead={'Lead-ID':'L1'}
    assert next_step_due(lead,rows(),date(2026,10,22)) is None
    assert next_step_due(lead,rows(),date(2026,10,23))==2
    assert next_step_due(lead,[],date(2026,10,23)) is None
    assert next_step_due(lead,rows(),date(2026,10,24)) is None


@pytest.mark.parametrize('field,value',[('Reply_Status','positiv'),('Opt-out-Status','yes'),('Bounce_Status','hard_bounce'),('Suppressed','yes')])
def test_suppression_and_reply_stop(field,value):
    assert next_step_due({'Lead-ID':'L1',field:value},rows(),date(2026,11,2)) is None


def test_ooo_and_late_second_step():
    lead={'Lead-ID':'L1','Reply_Status':'abwesend','Follow-up-Datum':'2026-11-10'}
    assert next_step_due(lead,rows(),date(2026,11,2)) is None
    history=rows()+[{'lead_id':'L1','step':2,'sent_at':'2026-11-02','state':'VERIFIED'}]
    assert next_step_due({'Lead-ID':'L1'},history,date(2026,11,3)) is None
    assert next_step_due({'Lead-ID':'L1'},history,date(2026,11,6))==3


def test_reply_sla_and_no_negative_overwrite():
    changes=reply_actions('HOT_LEAD',today=date(2026,10,23))
    assert changes['Follow-up-Datum']=='2026-10-26'
    assert changes['Reply_Status']=='positiv'
    assert reply_actions('OPTOUT')=={}
    assert reply_actions('OOO_URLAUB',return_date='2026-10-23')['Follow-up-Datum']=='2026-10-26'


def test_shared_daily_budget_and_restart(tmp_path):
    path=tmp_path/'sequence.db'
    j=SequenceJournal(path)
    with pytest.raises(RuntimeError):
        j.reserve('L1',2,'JOEL','<x@hsb-boden.com>','2026-10-27',10,10)
    j.reserve('L1',2,'JOEL','<x@hsb-boden.com>','2026-10-27',0,10)
    j.close()
    j=SequenceJournal(path)
    with pytest.raises(RuntimeError):
        j.reserve('L1',2,'JOEL','<y@hsb-boden.com>','2026-10-27',0,10)
    assert j.db.execute('SELECT count(*) FROM sequence').fetchone()[0]==1
    j.close()


def test_verified_first_contact_becomes_due_without_resetting_history(tmp_path):
    j=SequenceJournal(tmp_path/'seq.db')
    j.record_verified('L1',1,'JOEL','<first@hsb-boden.com>','2026-10-19T12:00:00Z')
    assert next_step_due({'Lead-ID':'L1','Send_Status':'sent'},j.rows(),date(2026,10,23))==2
    with pytest.raises(RuntimeError,match='CONFLICT'):
        j.record_verified('L1',1,'JOEL','<other@hsb-boden.com>','2026-10-19')
    assert j.rows()[0]['message_id']=='<first@hsb-boden.com>'
    j.close()


def test_first_step_and_final_send_state_are_one_transaction(tmp_path,monkeypatch):
    from email.message import EmailMessage
    from types import SimpleNamespace
    import outbound_safety as out
    journal=out.SendJournal(tmp_path/'outbound.db')
    client=SimpleNamespace(cfg={'email':'j-cherino@hsb-boden.com'},deliver_verified_bytes=lambda *a,**k:None)
    monkeypatch.setattr(out,'crm_write_readback',lambda *a:None)
    monkeypatch.setattr(out,'sent_copy_readback',lambda *a:None)
    msg=EmailMessage();msg['X-HSB-Template-ID']='v2-produktion-s1';msg.set_content('Test')
    item={'email':'a@firma.invalid','owner':'JOEL','lead_id':'L1'}
    out.complete_delivery(client,journal,None,'sheet',[],2,item,msg.as_bytes(),'<s1@hsb-boden.com>',10)
    assert journal.db.execute('SELECT state FROM attempts').fetchone()[0]=='VERIFIED'
    assert journal.db.execute('SELECT state FROM sequence').fetchone()[0]=='VERIFIED'
    journal.close()

