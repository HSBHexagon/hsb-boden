import new_drafts as nd


def lead(i, branche='Getraenkeindustrie', owner='JOEL', **kw):
    base = {'Lead-ID': f'HSB-20260708-{i:05d}', 'Firma': f'Firma {i} GmbH', 'Branche': branche,
            'Ansprechpartner': 'Herr Muster', 'E-Mail': f'info@firma{i}.de', 'Website': f'https://firma{i}.de',
            'Verantwortlicher': owner, 'Legal_Basis': 'LEGITIMATE_INTEREST', 'Legal_Review_Status': 'yes',
            'Legal_Review_Vermerk': 'x' * 45, 'Legal_Review_At': '2026-10-01T00:00:00+00:00',
            'Versandfreigabe': 'yes', 'Opt-in-Status': 'yes'}
    if branche == 'Architekten':
        base['Projektart'] = 'Umbau eines Produktionsstandorts'
    base.update(kw)
    return base


MX = lambda domain: True


def test_selects_only_eligible_owner_leads_without_existing_v2_and_80_20_mix():
    leads = [lead(i) for i in range(1, 11)] + [lead(i, 'Architekten') for i in range(11, 21)]
    leads += [lead(30, owner='JORDI'), lead(31, Send_Status='sent'), lead(32, Suppressed='yes'), lead(33, Bounce_Status='hard_bounce')]
    picked = nd.select_leads(leads, 'JOEL', 10, {'HSB-20260708-00001'}, mx_check=MX)
    ids = [l['Lead-ID'] for l in picked]
    assert len(ids) == 10 and 'HSB-20260708-00001' not in ids
    assert not {'HSB-20260708-00030', 'HSB-20260708-00031', 'HSB-20260708-00032', 'HSB-20260708-00033'} & set(ids)
    assert sum(nd.segment_for(l) == 'produktion' for l in picked) == 8


def test_architects_fill_when_production_runs_out():
    leads = [lead(1)] + [lead(i, 'Architekten') for i in range(2, 12)]
    picked = nd.select_leads(leads, 'JOEL', 5, set(), mx_check=MX)
    assert len(picked) == 5 and sum(nd.segment_for(l) == 'produktion' for l in picked) == 1


def test_planners_need_a_relevant_project_type(monkeypatch):
    # Sperrlogik bleibt prüfbar, wenn die Owner-Freigabe vom 04.11.2026 zurückgenommen wird.
    monkeypatch.setattr('lead_quality.PLANNER_OUTREACH_WITHOUT_PROJECT', False)
    leads = [lead(1, 'Architekten', Projektart='', Notizen='Import Architektenliste'),
             lead(2, 'Sonstiges', Projektart='Umbau Lebensmittelbetrieb'),
             lead(3, 'Architekten', Projektart='Wohnbau'),
             lead(4, 'Architekten', Projektart='Umbau Lebensmittelbetrieb')]
    picked = nd.select_leads(leads, 'JOEL', 10, set(), mx_check=MX)
    assert [l['Lead-ID'] for l in picked] == [leads[3]['Lead-ID']]


def test_build_items_are_repair_v2_with_lead_header_and_readable_link():
    items = nd.build_items([lead(1)], 'JOEL', 'fixture-secret')
    it = items[0]
    assert it['template_id'] == 'v2-produktion-reparatur-s1' and it['lead_id'] == 'HSB-20260708-00001'
    # Owner-Entscheidung 2026-11-04: lesbarer Reparatur-Link statt Klick-Token, keine Empfängeradresse im Text.
    assert 'https://www.hsb-boden.de/reparatur/' in it['body_text'] and '/r/' not in it['body_text']
    assert 'info@firma1.de' not in it['body_text']


class FakeImap:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def select(self, *a, **k): return 'OK', [b'0']
    def uid(self, *a): return 'OK', [b'']


class FakeClient:
    def __init__(self): self.batches = []
    def _get_imap(self): return FakeImap()
    def create_drafts_batch(self, items, max_existing=50):
        self.max_existing = max_existing
        self.batches.append(items); return [{'ok': True} for _ in items]


def test_dry_run_creates_nothing_and_apply_appends(tmp_path):
    c = FakeClient(); leads = [lead(i) for i in range(1, 4)]
    r = nd.create_v2_drafts('JOEL', 2, False, leads=leads, client=c, mx_check=MX, state_dir=tmp_path)
    assert r['selected'] == 2 and r['created'] == 0 and c.batches == [] and r['customer_emails_sent'] == 0
    import pytest
    with pytest.raises(RuntimeError, match='CLICK_SECRET_MISSING'):
        nd.create_v2_drafts('JOEL', 2, True, leads=leads, client=c, mx_check=MX, state_dir=tmp_path,
                            lock_client=LockClient([]))
    r = nd.create_v2_drafts('JOEL', 2, True, leads=leads, client=c, mx_check=MX, state_dir=tmp_path, secret='s',
                            lock_client=LockClient([]))
    assert r['created'] == 2 and len(c.batches[0]) == 2
    assert c.max_existing == nd.MAX_DRAFTS_PER_MAILBOX


def test_recipient_in_several_crm_rows_is_never_selected():
    leads = [lead(1), lead(2, **{'E-Mail': 'info@firma1.de'}, Send_Status='sent'), lead(3)]
    ids = [l['Lead-ID'] for l in nd.select_leads(leads, 'JOEL', 10, set(), mx_check=MX)]
    assert ids == ['HSB-20260708-00003']


def test_parallel_run_for_same_mailbox_is_refused(tmp_path):
    import pytest
    with nd.owner_lock('JOEL', tmp_path):
        with pytest.raises(RuntimeError, match='CREATE_V2_ALREADY_RUNNING'):
            with nd.owner_lock('JOEL', tmp_path):
                pass
    with nd.owner_lock('JORDI', tmp_path):
        pass


def test_deferred_tier_z_lead_is_never_selected():
    """Gespeicherter CRM-Tier Z (Website-Signale/Operator) gilt, auch wenn die Neuberechnung ohne Signale C ergibt."""
    leads = [lead(1, 'Architekten', Tier='Z'), lead(2, 'Architekten', Tier=' z '), lead(3, 'Architekten')]
    ids = [l['Lead-ID'] for l in nd.select_leads(leads, 'JOEL', 10, set(), mx_check=MX)]
    assert ids == ['HSB-20260708-00003']


def test_recipient_with_any_existing_draft_is_skipped_not_selected():
    leads = [lead(1), lead(2), lead(3)]
    ids = [l['Lead-ID'] for l in nd.select_leads(leads, 'JOEL', 10, set(), mx_check=MX,
                                                 draft_recipients={'INFO@firma2.de'})]
    assert ids == ['HSB-20260708-00001', 'HSB-20260708-00003']


class DraftImap(FakeImap):
    """Entwurfsordner mit einem alten v1-/Hand-Entwurf an firma2 (ohne X-HSB-Lead-ID)."""
    def uid(self, cmd, *args):
        if cmd.upper() == 'SEARCH' and args[1:3] == ('HEADER', 'To'):
            return 'OK', [b'7' if 'info@firma2.de' in args[3] else b'']
        if cmd.upper() == 'SEARCH' and args[1:] == ('ALL',):
            return 'OK', [b'7']
        if cmd.upper() == 'FETCH' and args[0] in (b'7', '7', b'1:*', '1:*'):
            return 'OK', [(b'7 (BODY[HEADER.FIELDS (TO)] {30}', b'To: Info <info@firma2.de>\r\n\r\n'), b')']
        return 'OK', [b'']


class StrictClient(FakeClient):
    """Bricht wie ComMailboxManager._assert_draft_capacity ab, sobald ein Empfänger schon einen Entwurf hat."""
    def _get_imap(self): return DraftImap()
    def create_drafts_batch(self, items, max_existing=50):
        if any(i['to_email'] == 'info@firma2.de' for i in items):
            raise RuntimeError('EXISTING_DRAFT_REQUIRES_RECONCILIATION')
        return super().create_drafts_batch(items, max_existing)


def test_leftover_non_v2_draft_does_not_abort_the_batch(tmp_path):
    c = StrictClient(); leads = [lead(i) for i in range(1, 4)]
    r = nd.create_v2_drafts('JOEL', 3, True, leads=leads, client=c, mx_check=MX, state_dir=tmp_path, secret='s',
                            lock_client=LockClient([]))
    assert r['created'] == 2 and r['existing_draft_recipients'] == 1
    assert [i['lead_id'] for i in c.batches[0]] == ['HSB-20260708-00001', 'HSB-20260708-00003']


class LockImap:
    """JOEL-Sperrordner wie in outbound_safety.mailbox_dispatch_lock; `held` simuliert einen laufenden Versand."""
    def __init__(self, events, held=False): self.events, self.held = events, held
    def create(self, folder):
        self.events.append('lock'); return ('NO' if self.held else 'OK'), [b'']
    def append(self, folder, flags, date, raw):
        self.marker = raw; return 'OK', [b'']
    def select(self, folder, readonly=True): return 'OK', [b'1']
    def uid(self, verb, *args):
        return ('OK', [b'1']) if verb == 'search' else ('OK', [(b'h', self.marker)])
    def close(self): pass
    def delete(self, folder):
        self.events.append('unlock'); return 'OK', [b'']
    def logout(self): pass


class LockClient:
    def __init__(self, events, held=False): self.imap = LockImap(events, held)
    def _get_imap(self): return self.imap


class RecordingClient(FakeClient):
    def __init__(self, events): super().__init__(); self.events = events
    def create_drafts_batch(self, items, max_existing=50):
        self.events.append('append'); return super().create_drafts_batch(items, max_existing)


def test_apply_holds_the_shared_dispatch_lock_around_append(tmp_path):
    """Codex [high]: ohne gemeinsame Sperre ändert APPEND den Ordner mitten im Versand-Scan (MAILBOX_CHANGED_DURING_SCAN)."""
    events = []
    nd.create_v2_drafts('JOEL', 2, True, leads=[lead(i) for i in range(1, 4)], client=RecordingClient(events),
                        mx_check=MX, state_dir=tmp_path, secret='s', lock_client=LockClient(events))
    assert events == ['lock', 'append', 'unlock']


def test_running_dispatch_blocks_draft_creation(tmp_path):
    import pytest
    events = []
    with pytest.raises(RuntimeError, match='DISPATCH_LOCK_EXISTS'):
        nd.create_v2_drafts('JOEL', 2, True, leads=[lead(i) for i in range(1, 4)], client=RecordingClient(events),
                            mx_check=MX, state_dir=tmp_path, secret='s', lock_client=LockClient(events, held=True))
    assert 'append' not in events


def test_dry_run_takes_no_dispatch_lock(tmp_path):
    events = []
    nd.create_v2_drafts('JOEL', 2, False, leads=[lead(i) for i in range(1, 4)], client=RecordingClient(events),
                        mx_check=MX, state_dir=tmp_path, lock_client=LockClient(events))
    assert events == []


def test_missing_click_secret_fails_before_taking_the_dispatch_lock(tmp_path):
    """Die Versandsperre bleibt bei Fehlern absichtlich stehen – eine Vorbedingung darf sie nie auslösen."""
    import pytest
    events = []
    with pytest.raises(RuntimeError, match='CLICK_SECRET_MISSING'):
        nd.create_v2_drafts('JOEL', 2, True, leads=[lead(i) for i in range(1, 4)], client=RecordingClient(events),
                            mx_check=MX, state_dir=tmp_path, lock_client=LockClient(events))
    assert events == []


def test_new_drafts_use_repair_copy_without_click_token():
    # Codex-Review #465: neue Entwürfe dürfen keinen /r/-Token und keine alte Fassung mehr tragen.
    from new_drafts import build_items
    from canonical_template_factory import REPAIR_URL, REPARATUR_COPY_REV
    lead = {'Lead-ID': 'HSB-20261104-0001', 'E-Mail': 'einkauf@musterbrauerei.de', 'Firma': 'Musterbrauerei GmbH',
            'Branche': 'Brauerei', 'Ansprechpartner': 'Herr Beispiel'}
    item = build_items([lead], 'JOEL', 'secret')[0]
    assert item['template_id'] == 'v2-produktion-reparatur-s1' and item['copy_rev'] == REPARATUR_COPY_REV
    assert REPAIR_URL in item['body_text'] and '/r/' not in item['body_text']


class MemoryImap:
    def __init__(self, store):
        self.store = store  # {uid_int: raw_bytes}
        self.appends = 0

    def __enter__(self): return self
    def __exit__(self, *a): return False
    def logout(self): pass

    def select(self, folder, readonly=True):
        return 'OK', [str(len(self.store)).encode()]

    def response(self, key):
        return key, [b'11']

    def append(self, folder, flags, date, raw):
        self.appends += 1
        uid = max(self.store, default=0) + 1
        self.store[uid] = raw
        return 'OK', [b'']

    def uid(self, cmd, *args):
        verb = cmd.upper()
        if verb == 'SEARCH':
            if args[1:] == ('ALL',):
                return 'OK', [b' '.join(str(u).encode() for u in sorted(self.store))]
            if args[1:3] == ('HEADER', 'Message-ID'):
                want = args[3].strip('"').encode()
                hits = [u for u, raw in self.store.items() if b'Message-ID: ' + want in raw]
                return 'OK', [b' '.join(str(u).encode() for u in sorted(hits))]
            if args[1:3] == ('HEADER', 'X-HSB-Template-ID'):
                hits = [u for u, raw in self.store.items() if b'X-HSB-Template-ID: v2-' in raw]
                return 'OK', [b' '.join(str(u).encode() for u in sorted(hits))]
            if args[1:3] == ('HEADER', 'X-HSB-Lead-ID'):
                want = args[3].strip('"').encode()
                hits = [u for u, raw in self.store.items() if b'X-HSB-Lead-ID: ' + want in raw]
                return 'OK', [b' '.join(str(u).encode() for u in sorted(hits))]
            if args[1:3] == ('HEADER', 'To'):
                want = args[3].strip('"').lower().encode()
                hits = [u for u, raw in self.store.items() if want in raw.lower()]
                return 'OK', [b' '.join(str(u).encode() for u in sorted(hits))]
        if verb == 'FETCH':
            target = args[0].decode() if isinstance(args[0], bytes) else str(args[0])
            spec = args[1]
            uids = sorted(self.store) if target == '1:*' else [int(target)]
            out = []
            for u in uids:
                raw = self.store[u]
                if 'HEADER.FIELDS' in spec:
                    head = raw.split(b'\r\n\r\n', 1)[0] + b'\r\n\r\n'
                    out.append((f'{u} BODY'.encode(), head))
                else:
                    out.append((f'{u} BODY[]'.encode(), raw))
            return 'OK', out
        raise AssertionError((cmd, args))


class MemoryClient:
    def __init__(self, owner, store):
        from com_mailbox_manager import ComMailboxClient
        self._real = ComMailboxClient.__new__(ComMailboxClient)
        names = {'JOEL': ('Joel Cherino Diaz', 'j-cherino@hsb-boden.com'),
                 'JORDI': ('Jordie Post', 'j-post@hsb-boden.com')}
        self.cfg = {'display_name': names[owner][0], 'email': names[owner][1], 'drafts_folder': '"Entw&APw-rfe"'}
        self._real.cfg = self.cfg
        self.store = store
        self.imap = MemoryImap(store)

    def _get_imap(self): return self.imap

    def build_draft_message(self, *a, **kw):
        return self._real.build_draft_message(*a, **kw)


class FakeCrmSheets:
    def __init__(self, headers, rows):
        self.headers = headers
        self.rows = [list(r) for r in rows]  # 0-based data rows (sheet row 2 == index 0)

    def _col_idx(self, letters):
        idx = 0
        for ch in letters:
            idx = idx * 26 + (ord(ch) - 64)
        return idx - 1

    def spreadsheets(self): return self
    def values(self): return self

    def get(self, spreadsheetId, range):
        matrix = [self.headers] + self.rows
        return type('R', (), {'execute': lambda _s: {'values': matrix}})()

    def batchGet(self, spreadsheetId, ranges):
        out = []
        for rng in ranges:
            ref = rng.split('!')[1]
            col = self._col_idx(''.join(c for c in ref if c.isalpha()))
            row = int(''.join(c for c in ref if c.isdigit())) - 2
            val = self.rows[row][col] if 0 <= row < len(self.rows) and col < len(self.rows[row]) else ''
            out.append({'values': [[val]]})
        return type('R', (), {'execute': lambda _s: {'valueRanges': out}})()

    def batchUpdate(self, spreadsheetId, body):
        for item in body['data']:
            ref = item['range'].split('!')[1]
            col = self._col_idx(''.join(c for c in ref if c.isalpha()))
            row = int(''.join(c for c in ref if c.isdigit())) - 2
            while len(self.rows[row]) <= col:
                self.rows[row].append('')
            self.rows[row][col] = item['values'][0][0]
        return type('R', (), {'execute': lambda _s: {}})()


def _eligible_crm_lead(nr, owner='JOEL', **kw):
    names = {'JOEL': 'Joel Cherino Diaz', 'JORDI': 'Jordie Post'}
    d = {'Lead-ID': f'HSB-20261105-{nr}', 'Firma': f'Musterwerk {nr} GmbH', 'Branche': 'Brauerei',
         'Ansprechpartner': 'Frau Beispiel', 'E-Mail': f'kontakt{nr}@musterwerk{nr}.de',
         'Verantwortlicher': names[owner], 'Versandfreigabe': 'yes', 'Legal_Basis': 'OPT_IN',
         'Legal_Evidence': 'Consent record TEST-2026', 'Legal_Evidence_At': '2026-09-01T10:00:00Z',
         'Draft_ID': '', 'Email_Template_ID': '', 'Drafted_At': '', 'Tier': 'A', '_row': nr + 1}
    d.update(kw)
    return d


def test_fill_missing_drafts_creates_repair_drafts_and_binds_crm():
    import draft_verify as dv
    l1 = _eligible_crm_lead(1, 'JOEL')
    l2 = _eligible_crm_lead(2, 'JORDI', Branche='Architekturbüro', Projektart='')
    l3 = _eligible_crm_lead(3, 'JOEL', **{'Opt-out-Status': 'yes'})
    leads = [l1, l2, l3]
    headers = [k for k in l1 if k != '_row']
    sheets = FakeCrmSheets(headers, [[r.get(h, '') for h in headers] for r in leads])
    balances = [
        {'lead_id': l1['Lead-ID'], 'owner': 'JOEL', 'reasons': ['NO_DRAFT']},
        {'lead_id': l2['Lead-ID'], 'owner': 'JORDI', 'reasons': ['NO_DRAFT']},
        {'lead_id': l3['Lead-ID'], 'owner': 'JOEL', 'reasons': ['NO_DRAFT', 'Opt_Out=YES']},
    ]
    stores = {'JOEL': {}, 'JORDI': {}}
    clients = {o: MemoryClient(o, stores[o]) for o in ('JOEL', 'JORDI')}
    res = nd.fill_missing_drafts(['JOEL', 'JORDI'], balances, [], leads, apply=True,
                                 make_client=lambda o: clients[o], lock_client=LockClient([]),
                                 svc=sheets, spreadsheet_id='sheet', headers=headers, connections=1)
    assert res['per_owner']['JOEL']['created'] == 1
    assert res['per_owner']['JORDI']['created'] == 1
    assert res['crm_writes'] == 2 and res['customer_emails_sent'] == 0
    # Beide neuen Entwürfe bestehen deep_check gegen den geschriebenen CRM-Stand
    for idx, owner in ((0, 'JOEL'), (1, 'JORDI')):
        updated = dict(zip(headers, sheets.rows[idx]))
        [raw] = stores[owner].values()
        assert dv.deep_check(raw, updated, owner) == []


def test_fill_missing_drafts_recovers_existing_unlinked_v2_draft_without_duplicate_append():
    import draft_verify as dv
    from canonical_template_factory import render_email_v2
    l1 = _eligible_crm_lead(1, 'JOEL')
    headers = [k for k in l1 if k != '_row']
    sheets = FakeCrmSheets(headers, [[l1.get(h, '') for h in headers]])
    store = {}
    client = MemoryClient('JOEL', store)
    mail = render_email_v2(l1, 'JOEL', step=1, variant='reparatur')
    raw, mid = client.build_draft_message(mail['to_email'], mail['subject'], body_text=mail['body_text'],
                                          body_html=mail['body_html'], template_id=mail['template_id'],
                                          lead_id=l1['Lead-ID'], copy_rev=mail['copy_rev'])
    store[5] = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n').replace(b'\n', b'\r\n')
    balances = [{'lead_id': l1['Lead-ID'], 'owner': 'JOEL', 'reasons': ['NO_DRAFT']}]
    res = nd.fill_missing_drafts(['JOEL'], balances, [], [l1], apply=True,
                                 make_client=lambda o: client, lock_client=LockClient([]),
                                 svc=sheets, spreadsheet_id='sheet', headers=headers, connections=1)
    assert client.imap.appends == 0
    assert res['per_owner']['JOEL']['recovered'] == 1
    assert res['crm_writes'] == 1
    updated = dict(zip(headers, sheets.rows[0]))
    assert updated['Draft_ID'] == mid
    assert dv.deep_check(store[5], updated, 'JOEL') == []


def test_fill_missing_drafts_skips_live_blocked_lead():
    l1 = _eligible_crm_lead(1, 'JOEL')
    headers = [k for k in l1 if k != '_row']
    live_blocked = dict(l1, Tier='Z')
    sheets = FakeCrmSheets(headers, [[live_blocked.get(h, '') for h in headers]])
    store = {}
    client = MemoryClient('JOEL', store)
    balances = [{'lead_id': l1['Lead-ID'], 'owner': 'JOEL', 'reasons': ['NO_DRAFT']}]
    res = nd.fill_missing_drafts(['JOEL'], balances, [], [l1], apply=True,
                                 make_client=lambda o: client, lock_client=LockClient([]),
                                 svc=sheets, spreadsheet_id='sheet', headers=headers, connections=1)
    assert res['per_owner']['JOEL']['created'] == 0
    assert res['per_owner']['JOEL']['skipped']['LIVE_BLOCKED'] == 1
    assert store == {}
