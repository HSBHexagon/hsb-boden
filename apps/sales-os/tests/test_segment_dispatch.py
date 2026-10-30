from outbound_safety import draft_segment, select_queue


def d(lead, s, sendable=True):
    return {'lead_id': lead, 'sendable': sendable, 'links': [f'https://www.hsb-boden.de/r/{lead}.abc123?s={s}']}


def test_draft_segment_from_click_link():
    assert draft_segment(d('L1', 'p')) == 'produktion'
    assert draft_segment(d('L1', 'a')) == 'architekten'
    assert draft_segment({'links': ['https://www.hsb-boden.de/flyer/']}) is None
    assert draft_segment({'links': ['https://evil.example/r/L1.x?s=p']}) is None


def test_select_queue_filters_segment_and_keeps_order_and_limits():
    queue = [{'owner': 'JOEL', 'lead_id': f'L{i}'} for i in range(1, 7)]
    drafts = [d('L1', 'a'), d('L2', 'p'), d('L3', 'p'), d('L4', 'a'), d('L5', 'p'), d('L6', 'p')]
    sel, used = select_queue(queue, drafts, ('JOEL',), 2, segments={'produktion'})
    assert [i['lead_id'] for i in sel] == ['L2', 'L3'] and used == {'JOEL': 2}


def test_select_queue_without_segments_unchanged():
    queue = [{'owner': 'JOEL', 'lead_id': 'L1'}, {'owner': 'JORDI', 'lead_id': 'L2'}]
    sel, used = select_queue(queue, [], ('JOEL', 'JORDI'), 1)
    assert len(sel) == 2 and used == {'JOEL': 1, 'JORDI': 1}


def test_unknown_or_unsendable_draft_excluded_when_filtering():
    queue = [{'owner': 'JOEL', 'lead_id': 'L1'}, {'owner': 'JOEL', 'lead_id': 'L2'}]
    sel, _ = select_queue(queue, [d('L1', 'p', sendable=False), {'lead_id': 'L2', 'sendable': True, 'links': []}], ('JOEL',), 5, segments={'produktion'})
    assert sel == []


def dv(lead, s, tid, sendable=True):
    return {**d(lead, s, sendable), 'template_id': tid}


def test_select_queue_variant_reparatur_only_takes_repair_drafts():
    # Kampagne Reparatur: nur Leads, deren versandbereiter Entwurf die Reparatur-Variante ist.
    queue = [{'owner': 'JOEL', 'lead_id': f'L{i}'} for i in range(1, 6)]
    drafts = [dv('L1', 'p', 'v2-produktion-s1'), dv('L2', 'p', 'v2-produktion-reparatur-s1'),
              dv('L3', 'a', 'v2-architekten-reparatur-s1'), dv('L4', 'p', 'v2-produktion-reparatur-s1'),
              dv('L5', 'p', 'v2-produktion-reparatur-s1', sendable=False)]
    sel, used = select_queue(queue, drafts, ('JOEL',), 10, segments={'produktion'}, variant='reparatur')
    assert [i['lead_id'] for i in sel] == ['L2', 'L4'] and used == {'JOEL': 2}
    sel, _ = select_queue(queue, drafts, ('JOEL',), 10, variant='reparatur')
    assert [i['lead_id'] for i in sel] == ['L2', 'L3', 'L4']


def test_select_queue_rejects_unknown_variant():
    import pytest
    with pytest.raises(ValueError):
        select_queue([], [], ('JOEL',), 1, variant='werbung')


def test_assess_message_reports_template_id():
    from test_template_v2 import lead, build
    from canonical_template_factory import render_email_v2
    from sales_reconciliation import assess_message
    row = lead()
    raw, _ = build(render_email_v2(row, 'JOEL', 1, variant='reparatur'))
    assert assess_message(raw, 'JOEL', [row])['template_id'] == 'v2-produktion-reparatur-s1'


def test_send_batch_cli_passes_segment_and_variant(monkeypatch):
    import sys, types
    import hsb_cli
    seen = {}
    fake = types.ModuleType('outbound_safety')
    fake.dispatch_verified = lambda **kw: seen.update(kw) or {'status': 'DRY_RUN_COMPLETED'}
    monkeypatch.setitem(sys.modules, 'outbound_safety', fake)
    monkeypatch.setattr(sys, 'argv', ['hsb_cli.py', 'send-batch', '--owner', 'JOEL', '--count', '10',
                                      '--segment', 'produktion', '--variant', 'reparatur'])
    hsb_cli.main()
    assert seen['segments'] == {'produktion'} and seen['variant'] == 'reparatur' and seen['dry_run'] is True
