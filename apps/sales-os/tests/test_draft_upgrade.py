import hashlib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from types import SimpleNamespace
import pytest
from com_mailbox_manager import ComMailboxClient
from draft_upgrade import upgrade_drafts, modified_utf7, mailbox_arg
from test_outbound_safety_gate import _crm_lead


def setup_case(tmp_path,monkeypatch):
    lead=_crm_lead(**{'Lead-ID':'HSB-20261001-0001','Verantwortlicher':'Joel Cherino Diaz',
                     'Branche':'Getraenkeindustrie','Draft_ID':'<old@hsb-boden.com>',
                     'Email_Template_ID':'v1','Drafted_At':'','_row':2})
    m=EmailMessage();m['From']='j-cherino@hsb-boden.com';m['To']=lead['E-Mail'];m['Subject']='Alt';m['Message-ID']='<old@hsb-boden.com>';m.set_content('Original')
    old=m.as_bytes()
    record={'owner':'JOEL','lead_id':lead['Lead-ID'],'folder':'Drafts','uid':'1','uidvalidity':'7','sha256':hashlib.sha256(old).hexdigest(),'issues':[]}
    boxes={'Drafts':{'1':old}};calls=[]
    class Imap:
        capabilities=(b'MOVE',b'UIDPLUS')
        folder='Drafts'
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def select(self,folder,readonly=True):
            self.folder=folder
            return ('OK',[b'1']) if folder in boxes else ('NO',[])
        def response(self,key): return key,[b'7']
        def create(self,folder): boxes[folder]={};return 'OK',[]
        def uid(self,verb,*args):
            calls.append(verb)
            if verb.lower()=='fetch': return 'OK',[(b'header',boxes[self.folder][str(args[0])])]
            if verb.lower()=='search':
                mid=str(args[-1]).strip('"')
                ids=[u for u,raw in boxes[self.folder].items() if str(BytesParser(policy=policy.default).parsebytes(raw)['Message-ID'])==mid]
                return 'OK',[' '.join(ids).encode()]
            if verb=='MOVE':
                uid,dest=args; boxes[dest]['8']=boxes[self.folder].pop(str(uid));return 'OK',[]
            pytest.fail('Unerwarteter IMAP-Befehl '+verb)
        def append(self,folder,flags,stamp,raw):
            calls.append('APPEND');boxes[folder]['2']=raw;return 'OK',[]
    imap=Imap()
    client=object.__new__(ComMailboxClient)
    client.cfg={'email':'j-cherino@hsb-boden.com','display_name':'Joel Cherino Diaz','drafts_folder':'Drafts'}
    client._get_imap=lambda:imap
    headers=[k for k in lead if k!='_row']
    class Values:
        def get(self,**kw):
            values=[[lead['Lead-ID']]] if kw['range']=='ALL_LEADS!A2:A2' else [headers] if kw['range'].endswith('BU1') else [headers,[lead.get(k,'') for k in headers]]
            return SimpleNamespace(execute=lambda:{'values':values})
    svc=SimpleNamespace(spreadsheets=lambda:SimpleNamespace(values=lambda:Values()))
    writes=[]
    def write(svc,sheet,headers,row,values): writes.append(values);lead.update(values)
    monkeypatch.setattr('outbound_safety.crm_write_readback',write)
    from contextlib import nullcontext
    monkeypatch.setattr('outbound_safety.mailbox_dispatch_lock',lambda c:nullcontext())
    kwargs=dict(lock_client=client,records=[record],leads=[lead],client=client,svc=svc,mx_check=lambda _:True,journal_path=tmp_path/'upgrade.db')
    return kwargs, boxes, calls, writes, old


def test_dry_run_changes_nothing(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    assert upgrade_drafts('JOEL',apply=False,**kwargs)['selected']==1
    assert calls==writes==[]
    assert not (tmp_path/'upgrade.db').exists()
    assert boxes['Drafts']=={'1':old}


def test_apply_readback_archive_and_resume(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    result=upgrade_drafts('JOEL',apply=True,**kwargs)
    assert result['appended']==result['archived']==result['crm_updated']==1
    assert list(boxes['Drafts'])==['2']
    assert boxes[mailbox_arg('Entwürfe-Archiv-v1')]['8']==old
    assert 'EXPUNGE' not in calls
    assert upgrade_drafts('JOEL',apply=True,**kwargs)['appended']==0
    assert calls.count('APPEND')==1


def test_changed_original_and_optout_untouched(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    boxes['Drafts']['1']=old+b'changed'
    result=upgrade_drafts('JOEL',apply=True,**kwargs)
    assert result['skipped_reasons']['CHANGED_V1_HASH']==1
    assert writes==[]
    kwargs['leads'][0]['Opt-out-Status']='yes'
    assert upgrade_drafts('JOEL',apply=False,**kwargs)['selected']==0


def test_uncertain_append_never_repeated(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    imap=kwargs['client']._get_imap()
    def uncertain(*a): raise TimeoutError('lost response')
    monkeypatch.setattr(imap,'append',uncertain)
    with pytest.raises(TimeoutError): upgrade_drafts('JOEL',apply=True,**kwargs)
    with pytest.raises(RuntimeError,match='UNCERTAIN_APPEND'): upgrade_drafts('JOEL',apply=True,**kwargs)
    assert boxes['Drafts']=={'1':old}


def test_archive_encoding():
    assert modified_utf7('Entwürfe-Archiv-v1')=='Entw&APw-rfe-Archiv-v1'


def test_existing_v2_not_upgraded_again_from_new_snapshot(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    kwargs['leads'][0]['Email_Template_ID']='v2-produktion-s1'
    result=upgrade_drafts('JOEL',apply=True,**kwargs)
    assert result['selected']==0
    assert calls==writes==[]


def test_missing_move_preserves_original_and_reuses_replacement(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    imap=kwargs['client']._get_imap();imap.capabilities=(b'UIDPLUS',)
    with pytest.raises(RuntimeError,match='UID_MOVE_REQUIRED'):
        upgrade_drafts('JOEL',apply=True,**kwargs)
    assert boxes['Drafts']['1']==old
    assert len(boxes['Drafts'])==2
    assert not writes
    with pytest.raises(RuntimeError,match='UID_MOVE_REQUIRED'):
        upgrade_drafts('JOEL',apply=True,**kwargs)
    assert calls.count('APPEND')==1


def test_busy_shared_dispatch_lock_blocks_before_append(tmp_path,monkeypatch):
    from contextlib import contextmanager
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    @contextmanager
    def busy(client):
        raise RuntimeError('DISPATCH_LOCK_EXISTS')
        yield
    monkeypatch.setattr('outbound_safety.mailbox_dispatch_lock',busy)
    with pytest.raises(RuntimeError,match='DISPATCH_LOCK_EXISTS'):
        upgrade_drafts('JOEL',apply=True,**kwargs)
    assert calls==writes==[]
    assert boxes['Drafts']=={'1':old}


def test_saved_tier_z_remains_excluded(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    kwargs['leads'][0]['Tier']='Z'
    assert upgrade_drafts('JOEL',apply=True,**kwargs)['selected']==0
    assert calls==writes==[]


def test_done_records_are_filtered_before_limit(tmp_path,monkeypatch):
    import sqlite3
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    first=kwargs['records'][0];lead2=dict(kwargs['leads'][0],**{'Lead-ID':'HSB-20261001-0002','E-Mail':'b@firma.invalid'})
    kwargs['leads'].append(lead2)
    kwargs['records'].append(dict(first,lead_id=lead2['Lead-ID'],uid='3'))
    db=sqlite3.connect(kwargs['journal_path'])
    db.execute('CREATE TABLE upgrades(key TEXT PRIMARY KEY,mid TEXT,raw BLOB,state TEXT,old_raw BLOB)')
    key='|'.join(str(first[k]) for k in ('owner','uidvalidity','uid','sha256'))
    db.execute('INSERT INTO upgrades VALUES(?,?,?,?,?)',(key,'<done@x.invalid>',b'','DONE',old));db.commit();db.close()
    result=upgrade_drafts('JOEL',limit=1,cohort='all',apply=False,**kwargs)
    assert result['selected']==1 and result['skipped_reasons']['ALREADY_DONE']==1


def test_identity_change_blocks_crm_write(monkeypatch):
    from outbound_safety import crm_write_lead_readback
    headers=['Lead-ID','Draft_ID']
    class Values:
        def get(self,**kw):
            rows=[headers,['L1','old']] if kw['range'].endswith('BU6425') else [['L2']]
            return SimpleNamespace(execute=lambda:{'values':rows})
    svc=SimpleNamespace(spreadsheets=lambda:SimpleNamespace(values=lambda:Values()))
    monkeypatch.setattr('outbound_safety.crm_write_readback',lambda *a:pytest.fail('keine falsche Zeile schreiben'))
    with pytest.raises(RuntimeError,match='CRM_IDENTITY_CHANGED_BEFORE_WRITE'):
        crm_write_lead_readback(svc,'sheet','L1',{'Draft_ID':'new'})
