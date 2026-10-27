from datetime import datetime, timezone, date
import json
import pytest
from send_governance import daily_budget, pause_reason, enforce_send_health


def health():
    return {'sample_sent':100,'hard_bounces':2,'policy_bounces':0,'deferrals_today':0,'spam_reports':0,'seed_dkim_pass':True,
            'checked_at':datetime.now(timezone.utc).isoformat(),'first_send_date':date.today().isoformat()}


def test_budget_10_20_30_cap_35():
    assert [daily_budget('2026-10-01',d) for d in ['2026-10-01','2026-10-08','2026-10-15','2027-01-01']]==[10,20,30,30]


@pytest.mark.parametrize('field,value,reason',[('hard_bounces',3,'HARD_BOUNCES'),('policy_bounces',1,'POLICY_BOUNCE'),('deferrals_today',3,'DEFERRALS'),('spam_reports',1,'SPAM_REPORT'),('seed_dkim_pass',False,'SEED_DKIM_NOT_PASS')])
def test_each_problem_pauses(field,value,reason):
    h=health(); h[field]=value
    assert pause_reason(h)==reason
    assert pause_reason({})=='HEALTH_EVIDENCE_MISSING'


def test_pause_is_persistent_and_health_reread(tmp_path,monkeypatch):
    p=tmp_path/'send-health.json'; h=health(); p.write_text(json.dumps(h))
    assert enforce_send_health(tmp_path)==10
    h['policy_bounces']=1; p.write_text(json.dumps(h))
    with pytest.raises(RuntimeError,match='DOMAIN_PAUSED'): enforce_send_health(tmp_path)
    h['policy_bounces']=0; p.write_text(json.dumps(h))
    with pytest.raises(RuntimeError,match='ACK_REQUIRED'): enforce_send_health(tmp_path)
    ack=json.loads((tmp_path/'send-pause.json').read_text())['ack_id']
    monkeypatch.setenv('HSB_SEND_PAUSE_ACK',ack)
    assert enforce_send_health(tmp_path)==10


def test_stale_stats_and_missing_stats_block(tmp_path):
    with pytest.raises(RuntimeError): enforce_send_health(tmp_path)
    h=health();h['checked_at']='2020-01-01T00:00:00+00:00'
    (tmp_path/'send-health.json').write_text(json.dumps(h))
    with pytest.raises(RuntimeError): enforce_send_health(tmp_path)


def test_health_guard_runs_before_each_delivery(tmp_path,monkeypatch):
    """Beim zweiten Kontakt neu auftauchende Sperre stoppt vor dem Transport."""
    import hashlib
    from contextlib import nullcontext
    from email.message import EmailMessage
    from types import SimpleNamespace
    import outbound_safety as out
    import sales_reconciliation as recon
    import sync_to_google_sheet as sheets
    import com_mailbox_manager as mail
    import closed_loop_crm as inbound
    import send_governance as guard
    from test_outbound_safety_gate import _crm_lead
    leads=[_crm_lead(**{'Lead-ID':f'L{i}','Verantwortlicher':'Joel Cherino Diaz','E-Mail':f'test{i}@firma.invalid'}) for i in (1,2)]
    headers=list(leads[0])
    raws={}
    queue=[];drafts=[]
    for i,lead in enumerate(leads,1):
        msg=EmailMessage();msg['To']=lead['E-Mail'];msg['From']='j-cherino@hsb-boden.com';msg['Subject']='x';msg['Message-ID']=f'<{i}@hsb-boden.com>';msg.set_content('Test')
        raw=msg.as_bytes();raws[str(i)]=raw
        queue.append({'lead_id':lead['Lead-ID'],'owner':'JOEL','email':lead['E-Mail']})
        drafts.append({'lead_id':lead['Lead-ID'],'sendable':True,'folder':'Drafts','uidvalidity':'7','uid':str(i),'sha256':hashlib.sha256(raw).hexdigest()})
    class IMAP:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def select(self,*a,**k):return 'OK',[]
        def response(self,*a):return None,[b'7']
        def uid(self,cmd,uid,*a):return 'OK',[(b'h',raws[uid])]
    client=SimpleNamespace(_get_imap=lambda:IMAP(),cfg={})
    monkeypatch.setattr(mail,'ComMailboxClient',lambda o:client)
    monkeypatch.setattr(out,'mailbox_dispatch_lock',lambda c:nullcontext())
    monkeypatch.setattr(inbound,'sync_inbounds',lambda **k:None)
    def audit(path):
        path.mkdir(parents=True)
        (path/'queue.json').write_text(json.dumps(queue));(path/'drafts.json').write_text(json.dumps(drafts))
    monkeypatch.setattr(recon,'run_audit',audit)
    monkeypatch.setattr(recon,'assess_message',lambda *a:{'issues':[]})
    monkeypatch.setattr(recon,'has_unreviewed_legacy_variant',lambda *a:False)
    values=SimpleNamespace(get=lambda **k:SimpleNamespace(execute=lambda:{'values':[headers]+[[l.get(h,'') for h in headers] for l in leads]}))
    monkeypatch.setattr(sheets,'get_sheets_service',lambda:SimpleNamespace(spreadsheets=lambda:SimpleNamespace(values=lambda:values)))
    monkeypatch.setattr('lead_quality.deliverability_flags',lambda *a:[])
    checks=[];deliveries=[]
    def health_check(*a):
        checks.append(1)
        if len(checks)==2:raise RuntimeError('DOMAIN_PAUSED:POLICY_BOUNCE')
        return 10
    monkeypatch.setattr(guard,'enforce_domain_health',health_check)
    monkeypatch.setattr(out,'complete_delivery',lambda *a:deliveries.append(a))
    monkeypatch.setattr(out.time,'sleep',lambda *a:None)
    monkeypatch.setenv('HSB_CUSTOMER_SEND_ENABLED','yes')
    monkeypatch.setenv('HSB_SALES_STATE_DIR',str(tmp_path))
    with pytest.raises(RuntimeError,match='DOMAIN_PAUSED'):
        out.dispatch_verified(2,owners=('JOEL',),dry_run=False)
    assert len(checks)==2 and len(deliveries)==1


def test_pause_propagates_to_second_device(tmp_path,monkeypatch):
    from send_governance import enforce_domain_health
    class Shared:
        event=None
        def read(self): return self.event
        def append(self,event): self.event=event
    shared=Shared()
    a=tmp_path/'A';b=tmp_path/'B';a.mkdir();b.mkdir()
    h=health();h['policy_bounces']=1;(a/'send-health.json').write_text(json.dumps(h))
    (b/'send-health.json').write_text(json.dumps(health()))
    with pytest.raises(RuntimeError):enforce_domain_health(a,date.today(),shared,collector=lambda **k:[])
    with pytest.raises(RuntimeError,match='SERVER_ACK_REQUIRED'):enforce_domain_health(b,date.today(),shared,collector=lambda **k:[])
    monkeypatch.setenv('HSB_SEND_PAUSE_ACK',shared.event['ack_id'])
    assert enforce_domain_health(b,date.today(),shared,collector=lambda **k:[])==10
    assert shared.event['state']=='ack'


def test_new_policy_event_is_observed_before_next_mail(tmp_path):
    from types import SimpleNamespace
    from send_governance import enforce_domain_health
    class Shared:
        event=None
        def read(self):return self.event
        def append(self,event):self.event=event
    (tmp_path/'send-health.json').write_text(json.dumps(health()))
    shared=Shared()
    incoming=[]
    collect=lambda **k:incoming
    assert enforce_domain_health(tmp_path,date.today(),shared,collector=collect)==10
    incoming.append(SimpleNamespace(message_id='<new@server.invalid>',sender='mailer-daemon@firma.invalid',date=datetime.now(timezone.utc).isoformat(),subject='Undeliverable',body='Status: 5.7.1\nDiagnostic-Code: smtp; 554 5.7.1 spam policy'))
    with pytest.raises(RuntimeError,match='DOMAIN_PAUSED:POLICY_BOUNCE'):
        enforce_domain_health(tmp_path,date.today(),shared,collector=collect)
    assert shared.event['state']=='paused'
