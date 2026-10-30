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
