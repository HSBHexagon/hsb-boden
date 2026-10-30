"""Vorlage v2, Variante Reparatur: Türöffner über Schadensbilder statt Firmenvorstellung."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from canonical_template_factory import render_email_v2
from sales_reconciliation import assess_message
from test_template_v2 import SEGMENT_LEADS, URL_RE, body_only, build

SEGMENTS = ['architekten', 'produktion']

# Aussagen nur aus apps/website/src/data/services/boden-reparatur-instandsetzung.ts belegt;
# unbelegte Zusagen dürfen nie in einer Mail stehen.
UNBELEGT = ['24 Stunden', 'Montag', 'garantiert', 'verbindlich', 'sofort', '65 %', 'Haftung',
            'Südzucker', 'Notfall', 'innerhalb von']


def render_all(factory, owner='JOEL'):
    first = render_email_v2(factory(), owner, 1, variant='reparatur')
    thread = {'message_id': '<step1@hsb-boden.com>', 'subject': first['subject']}
    return [first] + [render_email_v2(factory(), owner, s, thread=thread, variant='reparatur') for s in (2, 3)]


@pytest.mark.parametrize('segment', SEGMENTS)
def test_template_ids_mark_the_variant(segment):
    assert [r['template_id'] for r in render_all(SEGMENT_LEADS[segment])] == [
        f'v2-{segment}-reparatur-s{i}' for i in (1, 2, 3)]
    # Standard bleibt unverändert.
    assert render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1)['template_id'] == f'v2-{segment}-s1'


@pytest.mark.parametrize('segment', SEGMENTS)
def test_text_differs_from_standard_and_names_repair(segment):
    std = render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1)
    rep = render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1, variant='reparatur')
    assert rep['body_text'] != std['body_text'] and rep['subject'] != std['subject']
    for r in render_all(SEGMENT_LEADS[segment]):
        assert re.search(r'[Rr]eparatur|[Ii]nstand', body_only(r['body_text'])), r['template_id']


@pytest.mark.parametrize('segment', SEGMENTS)
def test_subject_2_to_5_words_max_50(segment):
    for firma in ('Musterbrauerei GmbH', 'Müller-Lüdenscheidt Industrieanlagenbau Nordwest GmbH', ''):
        s1 = render_email_v2(SEGMENT_LEADS[segment](Firma=firma), 'JOEL', 1, variant='reparatur')
        assert 2 <= len(s1['subject'].split()) <= 5 and len(s1['subject']) <= 50, s1['subject']


@pytest.mark.parametrize('segment', SEGMENTS)
@pytest.mark.parametrize('firma,contact', [('Musterbrauerei GmbH', 'Herr Beispiel'), ('', '')])
def test_body_60_to_120_words(segment, firma, contact):
    for r in render_all(lambda: SEGMENT_LEADS[segment](Firma=firma, Ansprechpartner=contact)):
        n = len(body_only(r['body_text']).split())
        assert 60 <= n <= 120, (r['template_id'], n)


@pytest.mark.parametrize('segment', SEGMENTS)
def test_one_link_in_step1_none_in_followups(segment):
    s1, s2, s3 = render_all(SEGMENT_LEADS[segment])
    assert len(URL_RE.findall(s1['body_text'])) == 1
    assert URL_RE.findall(s2['body_text']) == [] == URL_RE.findall(s3['body_text'])
    custom = render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1, click_url='https://www.hsb-boden.de/r/abc123',
                             variant='reparatur')
    assert URL_RE.findall(custom['body_text']) == ['https://www.hsb-boden.de/r/abc123']


@pytest.mark.parametrize('segment', SEGMENTS)
def test_no_unsupported_promises(segment):
    for r in render_all(SEGMENT_LEADS[segment]):
        text = r['subject'] + '\n' + body_only(r['body_text'])
        assert not [w for w in UNBELEGT if w.lower() in text.lower()], r['template_id']


@pytest.mark.parametrize('segment', SEGMENTS)
def test_company_named_at_most_once(segment):
    for r in render_all(lambda: SEGMENT_LEADS[segment](Firma='Muster Architekten GmbH, Beratende Ingenieure')):
        assert r['body_text'].count('Muster Architekten') <= 1 and 'GmbH, Beratende' not in r['body_text']


@pytest.mark.parametrize('segment', SEGMENTS)
@pytest.mark.parametrize('contact', ['Herr Beispiel', ''])
@pytest.mark.parametrize('owner', ['JOEL', 'JORDI'])
def test_passes_assess_message(segment, contact, owner):
    row = SEGMENT_LEADS[segment](Ansprechpartner=contact)
    if owner == 'JORDI':
        row['Verantwortlicher'] = 'Jordie Post'
    for res in render_all(lambda: dict(row), owner):
        raw, _ = build(res) if owner == 'JOEL' else (None, None)
        if raw is None:
            continue
        assert assess_message(raw, owner, [row])['issues'] == [], res['template_id']


def test_unknown_variant_rejected():
    with pytest.raises(ValueError):
        render_email_v2(SEGMENT_LEADS['produktion'](), 'JOEL', 1, variant='werbung')
