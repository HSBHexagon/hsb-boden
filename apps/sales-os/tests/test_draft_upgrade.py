import hashlib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from types import SimpleNamespace
import pytest
from com_mailbox_manager import ComMailboxClient
from draft_upgrade import upgrade_drafts, modified_utf7, mailbox_arg
from sales_reconciliation import assess_message
from test_outbound_safety_gate import _crm_lead


def setup_case(tmp_path,monkeypatch):
    monkeypatch.setenv('HSB_CRM_BINDINGS_VERIFIED','yes')
    lead=_crm_lead(**{'Lead-ID':'HSB-20261001-0001','Verantwortlicher':'Joel Cherino Diaz',
                     'Branche':'Getraenkeindustrie','Draft_ID':'<old@hsb-boden.com>',
                     'Email_Template_ID':'v1','Drafted_At':'','Tier':'','Projektart':'','_row':2})
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
    monkeypatch.setattr('outbound_safety.require_stable_crm_binding',lambda *a:{'developerMetadataLookup':{'metadataId':17}})
    monkeypatch.setattr('outbound_safety.crm_write_lead_readback',lambda svc,sheet,lead_id,values,**k:write(svc,sheet,headers,2,values))
    monkeypatch.setattr('crm_bindings.existing_bindings',lambda *a,**k:{})
    monkeypatch.setattr('crm_bindings.ensure_bindings',lambda *a,**k:{'created':len(k.get('only') or ())})
    monkeypatch.setattr('crm_bindings.remove_bindings',lambda *a,**k:0)
    from contextlib import nullcontext
    monkeypatch.setattr('outbound_safety.mailbox_dispatch_lock',lambda c,**k:nullcontext())
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
    appends=[]
    def uncertain(*a): appends.append(1); raise TimeoutError('lost response')
    monkeypatch.setattr(imap,'append',uncertain)
    monkeypatch.setattr('draft_upgrade.time.sleep',lambda s:None)
    # Nach dem Wiederverbinden ist der APPEND-Zustand unklar: nie wiederholen, sondern anhalten.
    with pytest.raises(RuntimeError,match='UNCERTAIN_APPEND'): upgrade_drafts('JOEL',apply=True,**kwargs)
    with pytest.raises(RuntimeError,match='UNCERTAIN_APPEND'): upgrade_drafts('JOEL',apply=True,**kwargs)
    assert appends==[1] and boxes['Drafts']=={'1':old}


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
    def busy(client, **k):
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


def test_stable_binding_never_writes_wrong_lead(monkeypatch):
    from outbound_safety import crm_write_lead_readback
    binding={'developerMetadataLookup':{'metadataId':17}}
    monkeypatch.setattr('outbound_safety.require_stable_crm_binding',lambda *a:binding)
    class Values:
        def get(self,**kw):return SimpleNamespace(execute=lambda:{'values':[['Lead-ID','Draft_ID']]})
        def batchGetByDataFilter(self,**kw):return SimpleNamespace(execute=lambda:{'valueRanges':[{'valueRange':{'values':[['OTHER','old']]}}]})
        def batchUpdateByDataFilter(self,**kw):pytest.fail('falsche Lead-Bindung darf nichts schreiben')
    svc=SimpleNamespace(spreadsheets=lambda:SimpleNamespace(values=lambda:Values()))
    with pytest.raises(RuntimeError,match='CRM_IDENTITY_BINDING_MISMATCH'):
        crm_write_lead_readback(svc,'sheet','L1',{'Draft_ID':'new'})


def test_stable_binding_uses_metadata_not_row_index(monkeypatch):
    from outbound_safety import crm_write_lead_readback
    binding={'developerMetadataLookup':{'metadataId':17}}; current=['L1','old']
    monkeypatch.setattr('outbound_safety.require_stable_crm_binding',lambda *a:binding)
    class Values:
        def get(self,**kw):return SimpleNamespace(execute=lambda:{'values':[['Lead-ID','Draft_ID']]})
        def batchGetByDataFilter(self,**kw):return SimpleNamespace(execute=lambda:{'valueRanges':[{'valueRange':{'range':'ALL_LEADS!A99:BU99','values':[list(current)]}}]})
        def batchUpdateByDataFilter(self,**kw):
            assert kw['body']['data'][0]['dataFilter']==binding
            assert kw['body']['data'][0]['values']==[[None,'new']]
            current[1]='new'
            return SimpleNamespace(execute=lambda:{'responses':[{'updatedRows':1}]})
    svc=SimpleNamespace(spreadsheets=lambda:SimpleNamespace(values=lambda:Values()))
    crm_write_lead_readback(svc,'sheet','L1',{'Draft_ID':'new'})
    assert current==['L1','new']


def test_live_tier_z_blocks_before_mailbox_mutation(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    live=kwargs['leads'][0]
    kwargs['leads']=[dict(live)]
    live['Tier']='Z'
    with pytest.raises(RuntimeError,match='LIVE_LEAD_GATE_BLOCKED'):
        upgrade_drafts('JOEL',apply=True,**kwargs)
    assert calls==writes==[]


def test_unverified_crm_binding_blocks_before_any_mutation(tmp_path,monkeypatch):
    kwargs,boxes,calls,writes,old=setup_case(tmp_path,monkeypatch)
    monkeypatch.delenv('HSB_CRM_BINDINGS_VERIFIED')
    with pytest.raises(RuntimeError,match='CANARY_REQUIRED'):
        upgrade_drafts('JOEL',apply=True,**kwargs)
    assert calls==writes==[]
    assert not kwargs['journal_path'].exists()


def test_upgrade_v2_standard_to_reparatur(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    kwargs['leads'][0]['Email_Template_ID'] = 'v2-produktion-s1'
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['selected'] == 1
    assert result['appended'] == 1
    assert calls.count('APPEND') == 1
    assert writes and writes[-1]['Email_Template_ID'] == 'v2-produktion-reparatur-s1'


def test_upgrade_reparatur_already_done_skipped(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    kwargs['leads'][0]['Email_Template_ID'] = 'v2-produktion-reparatur-s1'
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['selected'] == 0
    assert result['skipped_reasons']['ALREADY_V2'] == 1
    assert calls == writes == []


@pytest.mark.parametrize('project,interrupted', [
    ('Umbau einer Lebensmittelproduktion', False),
    ('Umbau einer Lebensmittelproduktion', True),
    ('', False),
])
def test_upgrade_replaces_obsolete_planner_copy_only_once(tmp_path, monkeypatch, project, interrupted):
    monkeypatch.setattr('lead_quality.PLANNER_OUTREACH_WITHOUT_PROJECT', False)
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    lead.update({'Branche': 'Architekturbüro', 'Projektart': project,
                 'Email_Template_ID': 'v2-architekten-reparatur-s1'})
    msg = EmailMessage()
    msg['From'] = 'j-cherino@hsb-boden.com'
    msg['To'] = lead['E-Mail']
    msg['Subject'] = 'Industrieböden im Bestand'
    msg['Message-ID'] = lead['Draft_ID']
    msg['X-HSB-Template-ID'] = lead['Email_Template_ID']
    msg.set_content(f"Für {lead['Firma']}: Nicht jeder Bestandsboden muss komplett neu verlegt werden.\nAbmelden")
    old = msg.as_bytes()
    boxes['Drafts']['1'] = old
    kwargs['records'][0].update(assess_message(old, 'JOEL', [lead]))
    kwargs['leads'] = [dict(lead)]

    assert 'OUTDATED_PLANNER_COPY' in kwargs['records'][0]['issues']
    def run_upgrade():
        return upgrade_drafts('JOEL', apply=True, cohort='all', variant='reparatur', **kwargs)

    if not project:
        assert 'PLANNING_PROJECT_UNVERIFIED' in kwargs['records'][0]['issues']
        assert run_upgrade()['selected'] == 0
        assert boxes['Drafts'] == {'1': old} and calls == writes == []
        assert not kwargs['journal_path'].exists()
        return
    if interrupted:
        from outbound_safety import crm_write_lead_readback

        def lose_crm_response(*args, **kwargs):
            crm_write_lead_readback(*args, **kwargs)
            raise TimeoutError('CRM response lost after write')

        with monkeypatch.context() as patch:
            patch.setattr('outbound_safety.crm_write_lead_readback', lose_crm_response)
            with pytest.raises(TimeoutError, match='CRM response lost'):
                run_upgrade()

    result = run_upgrade()
    assert result['archived'] == result['crm_updated'] == 1
    assert result['appended'] == (0 if interrupted else 1)
    assert boxes[mailbox_arg('Entwürfe-Archiv-v1')]['8'] == old
    new = assess_message(boxes['Drafts']['2'], 'JOEL', [lead])
    assert new['issues'] == []
    kwargs['records'] = [dict(new, uid='2', uidvalidity='7', folder='Drafts')]
    assert run_upgrade()['selected'] == 0
    assert calls.count('APPEND') == calls.count('MOVE') == 1


@pytest.mark.parametrize('issue', ['ALREADY_CONTACTED', 'ALREADY_CONTACTED_DOMAIN', 'DUPLICATE_DRAFT_RECIPIENT',
                                   'INBOUND_REQUIRES_REVIEW'])
def test_contacted_or_duplicate_drafts_are_never_upgraded(tmp_path, monkeypatch, issue):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    kwargs['records'][0]['issues'] = [issue]
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['selected'] == 0 and calls == writes == [] and boxes['Drafts'] == {'1': old}


def test_reparatur_upgrade_writes_current_copy(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['appended'] == result['archived'] == 1
    new = BytesParser(policy=policy.default).parsebytes(boxes['Drafts']['2'])
    from canonical_template_factory import REPAIR_URL, REPARATUR_COPY_REV
    assert new['X-HSB-Copy-Rev'] == REPARATUR_COPY_REV
    assert [p.get_content_type() for p in new.walk()] == ['multipart/alternative', 'text/plain', 'text/html']
    assert REPAIR_URL in new.get_body(('plain',)).get_content()
    assert not any(p.get_content_disposition() == 'attachment' for p in new.walk())


def test_prechecked_binding_and_headers_skip_lookups_but_keep_identity_readback(monkeypatch):
    # Google-Quote: mit übergebener Bindung/Kopfzeile keine Metadatensuche und kein Header-Read, Rücklesen bleibt.
    from outbound_safety import crm_write_lead_readback
    monkeypatch.setattr('outbound_safety.require_stable_crm_binding', lambda *a: pytest.fail('Bindung doppelt gesucht'))
    binding = {'developerMetadataLookup': {'metadataId': 17}}; current = ['OTHER', 'old']; reads = []
    class Values:
        def get(self, **kw): pytest.fail('Header doppelt gelesen')
        def batchGetByDataFilter(self, **kw):
            reads.append(1); return SimpleNamespace(execute=lambda: {'valueRanges': [{'valueRange': {'values': [list(current)]}}]})
        def batchUpdateByDataFilter(self, **kw): pytest.fail('falsche Lead-Bindung darf nichts schreiben')
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: Values()))
    with pytest.raises(RuntimeError, match='CRM_IDENTITY_BINDING_MISMATCH'):
        crm_write_lead_readback(svc, 'sheet', 'L1', {'Draft_ID': 'new'}, binding=binding, headers=['Lead-ID', 'Draft_ID'])
    assert reads == [1]


def test_sheet_id_is_read_once_per_service(monkeypatch):
    import outbound_safety
    monkeypatch.setattr(outbound_safety, '_SHEET_IDS', {})
    calls = []
    def get(**kw):
        calls.append(1)
        return SimpleNamespace(execute=lambda: {'sheets': [{'properties': {'title': 'ALL_LEADS', 'sheetId': 5}}]})
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(get=get))
    assert outbound_safety._all_leads_sheet_ids(svc, 's') == [5] == outbound_safety._all_leads_sheet_ids(svc, 's')
    assert calls == [1]


def test_binding_cleanup_runs_even_if_creation_fails(tmp_path, monkeypatch):
    # Codex-Review #524: Fehler beim Verifizieren nach dem Anlegen darf keine Bindungen liegen lassen.
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    removed = []
    def fail(*a, **k): raise RuntimeError('verify read failed')
    monkeypatch.setattr('crm_bindings.ensure_bindings', fail)
    monkeypatch.setattr('crm_bindings.remove_bindings', lambda svc, sid, ids: removed.append(set(ids)))
    with pytest.raises(RuntimeError, match='verify read failed'):
        upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert removed == [{kwargs['leads'][0]['Lead-ID']}] and boxes['Drafts'] == {'1': old}


def test_connection_reset_mid_draft_reconnects_and_finishes_once(tmp_path, monkeypatch):
    # Lauf 04.11.2026: 'Connection reset by peer' mitten in der Tranche. Neu anmelden, Entwurf genau einmal anlegen.
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    imap = kwargs['client']._get_imap()
    real_select = imap.select
    resets = []
    def flaky_select(*a, **k):
        if not resets:
            resets.append(1)
            raise ConnectionResetError(104, 'Connection reset by peer')
        return real_select(*a, **k)
    monkeypatch.setattr(imap, 'select', flaky_select)
    monkeypatch.setattr('draft_upgrade.time.sleep', lambda s: None)
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['imap_reconnects'] == 1 and result['appended'] == result['crm_updated'] == 1
    assert calls.count('APPEND') == 1 and len(boxes['Drafts']) == 1


def _replacement(lead, mid='<neu@hsb-boden.com>', to=None, step=1):
    from canonical_template_factory import render_email_v2
    from com_mailbox_manager import ComMailboxClient as C
    client = object.__new__(C)
    client.cfg = {'email': 'j-cherino@hsb-boden.com', 'display_name': 'Joel Cherino Diaz', 'drafts_folder': 'Drafts'}
    thread = {'message_id': '<erst@hsb-boden.com>', 'subject': 'Erstkontakt'} if step > 1 else None
    r = render_email_v2(lead, 'JOEL', step=step, thread=thread, variant='reparatur')
    raw, _ = client.build_draft_message(to or r['to_email'], r['subject'], body_text=r['body_text'], template_id=r['template_id'],
                                        lead_id=lead['Lead-ID'], custom_message_id=mid, copy_rev=r.get('copy_rev'))
    return raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')


def _header_search(imap, boxes):
    real = imap.uid
    def uid(verb, *args):
        if verb.lower() == 'search' and 'X-HSB-Lead-ID' in args:
            want = str(args[-1]).strip('"')
            ids = [u for u, raw in boxes[imap.folder].items()
                   if str(BytesParser(policy=policy.default).parsebytes(raw).get('X-HSB-Lead-ID') or '') == want]
            return 'OK', [' '.join(ids).encode()]
        return real(verb, *args)
    return uid


def test_restart_with_empty_journal_adopts_replacement_instead_of_second_append(tmp_path, monkeypatch):
    # Codex-Review #524: Das Journal liegt je Lauf auf dem Runner. APPEND war angenommen, der Lauf starb, der
    # Neustart hat ein leeres Journal und dasselbe Original: kein zweiter Ersatzentwurf für denselben Empfänger.
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    boxes['Drafts']['2'] = _replacement(lead)
    imap = kwargs['client']._get_imap()
    monkeypatch.setattr(imap, 'uid', _header_search(imap, boxes))
    monkeypatch.setattr(imap, 'append', lambda *a: pytest.fail('zweiter APPEND'))
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['replacements_adopted'] == 1 and result['appended'] == 0 and result['crm_updated'] == 1
    assert list(boxes['Drafts']) == ['2'] and writes[-1]['Draft_ID'] == '<neu@hsb-boden.com>'


def test_replacement_for_other_recipient_is_not_adopted(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    boxes['Drafts']['2'] = _replacement(lead, to='fremd@firma.de')
    imap = kwargs['client']._get_imap()
    monkeypatch.setattr(imap, 'uid', _header_search(imap, boxes))
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result.get('replacements_adopted', 0) == 0 and result['appended'] == 1


def test_rendered_followup_is_not_adopted_as_first_contact(tmp_path, monkeypatch):
    # Codex-Review #526: Ein echter Folgekontakt besteht assess_message, ersetzt aber nie den Erstkontakt.
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    boxes['Drafts']['2'] = _replacement(lead, step=2)
    imap = kwargs['client']._get_imap()
    monkeypatch.setattr(imap, 'uid', _header_search(imap, boxes))
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result.get('replacements_adopted', 0) == 0 and result['appended'] == 1


def test_two_replacements_stop_before_any_mailbox_change(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    boxes['Drafts']['2'] = _replacement(lead)
    boxes['Drafts']['3'] = _replacement(lead, mid='<neu2@hsb-boden.com>')
    imap = kwargs['client']._get_imap()
    monkeypatch.setattr(imap, 'uid', _header_search(imap, boxes))
    with pytest.raises(RuntimeError, match='REPLACEMENT_NOT_UNIQUE'):
        upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert set(boxes['Drafts']) == {'1', '2', '3'} and 'APPEND' not in calls and writes == []


def test_tranche_binds_missing_leads_and_removes_only_its_own(tmp_path, monkeypatch):
    # Lauf 04.11.2026 brach mit CRM_STABLE_LEAD_BINDING_REQUIRED ab: Umstellung legte keine Bindungen an.
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    seen = {}
    monkeypatch.setattr('crm_bindings.ensure_bindings', lambda *a, **k: seen.setdefault('ensure', set(k['only'])))
    monkeypatch.setattr('crm_bindings.remove_bindings', lambda svc, sid, ids: seen.setdefault('remove', set(ids)))
    lead_id = kwargs['leads'][0]['Lead-ID']
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['crm_updated'] == 1
    assert seen == {'ensure': {lead_id}, 'remove': {lead_id}}


def test_prebound_lead_binding_is_kept(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead_id = kwargs['leads'][0]['Lead-ID']
    removed = []
    monkeypatch.setattr('crm_bindings.existing_bindings', lambda *a, **k: {lead_id: [1]})
    monkeypatch.setattr('crm_bindings.remove_bindings', lambda svc, sid, ids: removed.append(set(ids)))
    upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert removed == [set()]


def test_missing_binding_skips_draft_without_touching_mailbox(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    def no_binding(*a): raise RuntimeError('CRM_STABLE_LEAD_BINDING_REQUIRED')
    monkeypatch.setattr('outbound_safety.require_stable_crm_binding', no_binding)
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['skipped_reasons']['CRM_BINDING_UNAVAILABLE'] == 1 and result['appended'] == 0
    assert boxes['Drafts'] == {'1': old} and 'APPEND' not in calls and writes == []


def test_owner_decision_upgrades_planner_without_project(tmp_path, monkeypatch):
    # Owner-Entscheidung 04.11.2026: jeder offene Entwurf, auch Planer ohne belegtes Projekt.
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    kwargs['leads'][0].update({'Branche': 'Architekturbüro', 'Projektart': ''})
    result = upgrade_drafts('JOEL', apply=True, variant='reparatur', **kwargs)
    assert result['crm_updated'] == 1 and 'PLANNING_PROJECT_UNVERIFIED' not in result['skipped_reasons']
    assert writes[-1]['Email_Template_ID'].startswith('v2-architekten-reparatur-')


def test_outdated_planner_copy_with_divergent_crm_binding_is_upgraded(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    lead.update({'Branche': 'Architekturbüro', 'Projektart': 'Wohnbau',
                 'Email_Template_ID': 'v2-architekten-reparatur-s1',
                 'Draft_ID': '<anderer-entwurf@hsb-boden.com>'})
    msg = EmailMessage()
    msg['From'] = 'j-cherino@hsb-boden.com'
    msg['To'] = lead['E-Mail']
    msg['Subject'] = 'Industrieböden im Bestand'
    msg['Message-ID'] = '<alt-im-postfach@hsb-boden.com>'
    msg['X-HSB-Template-ID'] = 'v2-architekten-reparatur-s1'
    msg['X-HSB-Lead-ID'] = lead['Lead-ID']
    msg.set_content('Nicht jeder Bestandsboden muss komplett neu verlegt werden.\nAbmelden')
    old = msg.as_bytes()
    boxes['Drafts']['1'] = old
    kwargs['records'][0].update(assess_message(old, 'JOEL', [lead]))
    kwargs['leads'] = [dict(lead)]
    result = upgrade_drafts('JOEL', apply=True, cohort='all', variant='reparatur', **kwargs)
    assert result['appended'] == result['archived'] == result['crm_updated'] == 1
    assert writes[-1]['Draft_ID'] != '<anderer-entwurf@hsb-boden.com>'


def test_deep_defect_with_divergent_crm_binding_is_upgraded(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, old = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    lead.update({'Email_Template_ID': 'v2-produktion-reparatur-s1', 'Draft_ID': '<fremd@hsb-boden.com>'})
    rec = kwargs['records'][0]
    rec['issues'] = []
    key = f"{rec['owner']}|{rec['uidvalidity']}|{rec['uid']}|{rec['sha256']}"
    result = upgrade_drafts('JOEL', apply=True, cohort='all', variant='reparatur',
                            deep_defects=frozenset({key}), **kwargs)
    assert result['appended'] == result['archived'] == result['crm_updated'] == 1


def _resaved_outlook_raw(lead, body_override=None):
    from canonical_template_factory import render_email_v2
    rendered = render_email_v2(lead, 'JOEL', step=1, variant='reparatur')
    msg = EmailMessage()
    msg['From'] = 'Joel Cherino Diaz <j-cherino@hsb-boden.com>'
    msg['To'] = lead['E-Mail']
    msg['Subject'] = rendered['subject']
    msg['Message-ID'] = '<outlook-resaved@hsb-boden.com>'
    html_body = body_override if body_override is not None else rendered['body_html']
    msg.set_content(rendered['body_text'])
    msg.add_alternative(html_body, subtype='html')
    return msg.as_bytes()


def test_resaved_same_text_is_rebuilt(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    lead.update({'Email_Template_ID': 'v2-produktion-reparatur-s1', 'Draft_ID': '<vor-outlook@hsb-boden.com>'})
    old = _resaved_outlook_raw(lead)
    boxes['Drafts']['1'] = old
    kwargs['records'][0].update({'sha256': hashlib.sha256(old).hexdigest(), 'issues': ['LEAD_ID_INFERRED_ONLY'],
                                 'message_id': '<outlook-resaved@hsb-boden.com>'})
    result = upgrade_drafts('JOEL', apply=True, cohort='all', variant='reparatur', **kwargs)
    assert result['appended'] == result['archived'] == result['crm_updated'] == 1
    new_msg = BytesParser(policy=policy.default).parsebytes(boxes['Drafts']['2'])
    assert new_msg['X-HSB-Lead-ID'] == lead['Lead-ID']
    assert writes[-1]['Draft_ID'] == new_msg['Message-ID']


def test_resaved_with_changed_text_is_held(tmp_path, monkeypatch):
    from canonical_template_factory import render_email_v2
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    lead.update({'Email_Template_ID': 'v2-produktion-reparatur-s1', 'Draft_ID': '<vor-outlook@hsb-boden.com>'})
    edited_html = render_email_v2(lead, 'JOEL', step=1, variant='reparatur')['body_html'].replace(
        'Schadstelle', 'Persönliche Notiz für Herrn Beispiel', 1)
    old = _resaved_outlook_raw(lead, body_override=edited_html)
    boxes['Drafts']['1'] = old
    kwargs['records'][0].update({'sha256': hashlib.sha256(old).hexdigest(), 'issues': ['LEAD_ID_INFERRED_ONLY'],
                                 'message_id': '<outlook-resaved@hsb-boden.com>'})
    result = upgrade_drafts('JOEL', apply=True, cohort='all', variant='reparatur', **kwargs)
    assert result['skipped_reasons']['HUMAN_EDITED'] == 1
    assert result['appended'] == 0 and 'APPEND' not in calls and writes == []
    assert boxes['Drafts'] == {'1': old}


def test_resaved_with_two_drafts_is_skipped(tmp_path, monkeypatch):
    kwargs, boxes, calls, writes, _ = setup_case(tmp_path, monkeypatch)
    lead = kwargs['leads'][0]
    old = _resaved_outlook_raw(lead)
    boxes['Drafts']['1'] = old
    kwargs['records'][0].update({'sha256': hashlib.sha256(old).hexdigest(), 'issues': ['LEAD_ID_INFERRED_ONLY']})
    kwargs['records'].append(dict(kwargs['records'][0], uid='9'))
    result = upgrade_drafts('JOEL', apply=False, cohort='all', variant='reparatur', **kwargs)
    assert result['selected'] == 0 and result['skipped_reasons']['AMBIGUOUS_LEAD_OR_DRAFT'] == 2
