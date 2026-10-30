import new_drafts as nd


def lead(i, branche='Getraenkeindustrie', owner='JOEL', **kw):
    base = {'Lead-ID': f'HSB-20260708-{i:05d}', 'Firma': f'Firma {i} GmbH', 'Branche': branche,
            'Ansprechpartner': 'Herr Muster', 'E-Mail': f'info@firma{i}.de', 'Website': f'https://firma{i}.de',
            'Verantwortlicher': owner, 'Legal_Basis': 'LEGITIMATE_INTEREST', 'Legal_Review_Status': 'yes',
            'Legal_Review_Vermerk': 'x' * 45, 'Legal_Review_At': '2026-10-01T00:00:00+00:00',
            'Versandfreigabe': 'yes', 'Opt-in-Status': 'yes'}
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


def test_build_items_are_plain_v2_with_lead_header_and_click_url():
    items = nd.build_items([lead(1)], 'JOEL', 'fixture-secret')
    it = items[0]
    assert it['template_id'] == 'v2-produktion-s1' and it['lead_id'] == 'HSB-20260708-00001'
    assert '/r/HSB-20260708-00001.' in it['body_text'] and 'info@firma1.de' not in it['body_text']


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
