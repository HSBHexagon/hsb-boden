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
    def create_drafts_batch(self, items):
        self.batches.append(items); return [{'ok': True} for _ in items]


def test_dry_run_creates_nothing_and_apply_appends():
    c = FakeClient(); leads = [lead(i) for i in range(1, 4)]
    r = nd.create_v2_drafts('JOEL', 2, False, leads=leads, client=c, mx_check=MX)
    assert r['selected'] == 2 and r['created'] == 0 and c.batches == [] and r['customer_emails_sent'] == 0
    r = nd.create_v2_drafts('JOEL', 2, True, leads=leads, client=c, mx_check=MX)
    assert r['created'] == 2 and len(c.batches[0]) == 2
