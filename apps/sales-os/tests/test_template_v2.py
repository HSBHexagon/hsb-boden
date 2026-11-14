"""Vorlage v2: reiner Text, 2 Segmente, 3 Schritte."""
import re
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from canonical_template_factory import render_email_v2, short_company, CANONICAL_FLYERS
from com_mailbox_manager import ComMailboxClient
from sales_reconciliation import assess_message

URL_RE = re.compile(r'https?://[^\s<>"\']+')


def lead(**overrides):
    row = {'Lead-ID': 'HSB-20261027-1', 'E-Mail': 'buyer@example.org', 'Firma': 'Musterbrauerei GmbH',
           'Ansprechpartner': 'Herr Beispiel', 'Branche': 'Brauerei', 'Verantwortlicher': 'Joel Cherino Diaz'}
    row.update(overrides)
    return row


def arch(**o):
    return lead(**{'Branche': 'Architekturbüro', 'Firma': 'Beispiel Architekten GmbH',
                   'Projektart': 'Umbau Produktionsstandort', **o})


SEGMENT_LEADS = {'architekten': arch, 'produktion': lead}
THREAD = {'message_id': '<step1@hsb-boden.com>', 'subject': 'Hygieneboden bei Musterbrauerei'}


def render_all(factory):
    first = render_email_v2(factory(), 'JOEL', 1)
    thread = {'message_id': '<step1@hsb-boden.com>', 'subject': first['subject']}
    return [first] + [render_email_v2(factory(), 'JOEL', s, thread=thread) for s in (2, 3)]


def body_only(text):
    """Text zwischen Anrede und Gruss (ohne Anrede, Signatur, Abmeldezeile)."""
    after_greeting = text.split('\n\n', 1)[1]
    return after_greeting.split('\n\nMit freundlichen Grüßen', 1)[0]


def client():
    c = ComMailboxClient.__new__(ComMailboxClient)
    c.cfg = {'display_name': 'Joel Cherino Diaz', 'email': 'j-cherino@hsb-boden.com'}
    return c


def build(res):
    raw, mid = client().build_draft_message(
        res['to_email'], res['subject'], body_text=res['body_text'], template_id=res['template_id'],
        in_reply_to=res['in_reply_to'], references=res['references'], lead_id=res['lead_id'],
        custom_message_id='<m1@hsb-boden.com>', copy_rev=res.get('copy_rev'))
    return raw, mid


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_subject_2_to_5_words_max_50(segment):
    s1 = render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1)
    assert 2 <= len(s1['subject'].split()) <= 5
    assert len(s1['subject']) <= 50
    long_name = render_email_v2(SEGMENT_LEADS[segment](Firma='Müller-Lüdenscheidt Industrieanlagenbau Nordwest GmbH'), 'JOEL', 1)
    assert 2 <= len(long_name['subject'].split()) <= 5 and len(long_name['subject']) <= 50


def test_short_company_strips_legal_form():
    assert short_company('maiermaier innen:architektur, Innenarchitektin und Architektin Partnerschaftsgesellschaft') == 'maiermaier innen:architektur'
    assert short_company('Musterbrauerei GmbH') == 'Musterbrauerei'
    assert short_company('Beispiel GmbH & Co. KG') == 'Beispiel'
    assert short_company('Mustermann e.K.') == 'Mustermann'
    assert short_company('Bau UG (haftungsbeschränkt)') == 'Bau'
    assert len(short_company('A' * 30 + ' ' + 'B' * 30)) <= 40


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_body_60_to_120_words(segment):
    for r in render_all(SEGMENT_LEADS[segment]):
        n = len(body_only(r['body_text']).split())
        assert 60 <= n <= 120, (r['template_id'], n)


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_step1_at_most_one_link_steps_2_3_none(segment):
    s1, s2, s3 = render_all(SEGMENT_LEADS[segment])
    assert len(URL_RE.findall(s1['body_text'])) == 1
    assert 'utm_campaign=iboden_v2_' + segment in s1['body_text']
    assert URL_RE.findall(s2['body_text']) == [] and URL_RE.findall(s3['body_text']) == []
    custom = render_email_v2(lead(), 'JOEL', 1, click_url='https://www.hsb-boden.de/r/abc123')
    assert URL_RE.findall(custom['body_text']) == ['https://www.hsb-boden.de/r/abc123']


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_no_email_or_name_in_urls(segment):
    for r in render_all(SEGMENT_LEADS[segment]):
        for url in URL_RE.findall(r['body_text']):
            assert 'buyer' not in url and '@' not in url and 'example.org' not in url
            assert 'beispiel' not in url.lower() and 'HSB-2026' not in url


def test_plain_text_part_first_no_attachment_no_reply_to():
    res = render_email_v2(lead(), 'JOEL', 1)
    raw, _ = build(res)
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    # text/plain zuerst, dann gleichlautendes HTML: Outlook bearbeitet IMAP-Entwürfe im HTML-Editor.
    assert [p.get_content_type() for p in msg.walk()] == ['multipart/alternative', 'text/plain', 'text/html']
    plain = msg.get_body(('plain',))
    assert plain.get_content_charset() == 'utf-8'
    assert msg['Reply-To'] is None
    assert msg['X-HSB-Template-ID'] == 'v2-produktion-s1'
    assert msg['X-HSB-Lead-ID'] == 'HSB-20261027-1'
    assert plain.get_content().replace('\r\n', '\n').strip() == res['body_text'].strip()
    assert not any(p.get_content_disposition() == 'attachment' for p in msg.walk())


@pytest.mark.parametrize('variant', ['standard', 'reparatur'])
def test_paragraphs_survive_in_plain_and_html_with_crlf(variant):
    import html as _html
    import re as _re
    res = render_email_v2(lead(), 'JOEL', 1, variant=variant)
    raw, _ = build(res)
    # Nur CRLF-Zeilenenden: nackte LF lassen Outlook-Entwürfe zu einem Block zusammenfallen.
    assert raw.replace(b'\r\n', b'').count(b'\n') == 0 and b'\r' not in raw.replace(b'\r\n', b'')
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    plain = msg.get_body(('plain',)).get_content().replace('\r\n', '\n')
    html_part = msg.get_body(('html',)).get_content()
    paragraphs = [p for p in plain.strip().split('\n\n') if p.strip()]
    assert len(paragraphs) >= 6
    assert html_part.count('<p ') == len(paragraphs)
    # Jede Zeile innerhalb eines Absatzes bleibt im HTML als Umbruch erhalten.
    assert html_part.count('<br>') == sum(p.count('\n') for p in paragraphs)
    assert all(p.get('Content-Transfer-Encoding') == 'quoted-printable'
               for p in msg.walk() if not p.is_multipart())
    for url in _re.findall(r'https?://[^\s<>"\x27]+', plain):
        esc = _html.escape(url, quote=True)
        assert f'<a href="{esc}">{esc}</a>' in html_part


def test_v1_build_draft_message_unchanged():
    raw, _ = client().build_draft_message('buyer@example.org', 'Betreff', '<p>Hallo HSB-20261027-1</p>',
                                          flyer_bytes=b'%PDF-1.4')
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    assert msg.is_multipart() and msg['X-HSB-Template-ID'] is None
    assert msg['X-HSB-Lead-ID'] == 'HSB-20261027-1'
    assert [p.get_content_type() for p in msg.walk()][1:] == ['multipart/alternative', 'text/plain', 'text/html', 'application/pdf']


@pytest.mark.parametrize('owner', ['JOEL', 'JORDI'])
def test_signature_contains_phone(owner):
    r = render_email_v2(lead(), owner, 1)
    assert CANONICAL_FLYERS[owner]['sender_phone'] in r['body_text']
    assert {'JOEL': 'j-cherino@hsb-boden.com', 'JORDI': 'j-post@hsb-boden.com'}[owner] in r['body_text']
    assert 'HRB 21481' in r['body_text'] and 'Jordie Post' in r['body_text']
    assert '‚Abmelden‘' in r['body_text']


def test_greeting_without_contact():
    r = render_email_v2(lead(Ansprechpartner=''), 'JOEL', 1)
    assert r['body_text'].startswith('Sehr geehrte Damen und Herren,\n')
    r = render_email_v2(lead(), 'JOEL', 1)
    assert r['body_text'].startswith('Sehr geehrter Herr Beispiel,\n')


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_followups_thread_with_in_reply_to_and_references(segment):
    s1, s2, s3 = render_all(SEGMENT_LEADS[segment])
    assert s1['in_reply_to'] is None and s1['references'] is None
    for r in (s2, s3):
        assert r['subject'] == 'Re: ' + s1['subject']
        assert r['in_reply_to'] == '<step1@hsb-boden.com>' == r['references']
        raw, _ = build(r)
        msg = BytesParser(policy=policy.default).parsebytes(raw)
        assert msg['In-Reply-To'] == '<step1@hsb-boden.com>' and msg['References'] == '<step1@hsb-boden.com>'
    assert [r['template_id'] for r in (s1, s2, s3)] == [f'v2-{segment}-s{i}' for i in (1, 2, 3)]
    with pytest.raises(ValueError):
        render_email_v2(lead(), 'JOEL', 2)


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
@pytest.mark.parametrize('contact', ['Herr Beispiel', ''])
def test_v2_passes_assess_message(segment, contact):
    factory = SEGMENT_LEADS[segment]
    row = factory(Ansprechpartner=contact)
    first = render_email_v2(row, 'JOEL', 1)
    thread = {'message_id': '<step1@hsb-boden.com>', 'subject': first['subject']}
    for step in (1, 2, 3):
        res = first if step == 1 else render_email_v2(row, 'JOEL', step, thread=thread)
        raw, _ = build(res)
        a = assess_message(raw, 'JOEL', [row])
        assert a['issues'] == [], (res['template_id'], a['issues'])


def test_v2_assess_flags_violations():
    row = lead()
    res = render_email_v2(row, 'JOEL', 1)

    def issues(text=None, subject=None, tid=None):
        raw, _ = client().build_draft_message(
            res['to_email'], subject or res['subject'], body_text=text or res['body_text'],
            template_id=tid or res['template_id'], lead_id=res['lead_id'], custom_message_id='<m1@hsb-boden.com>')
        return assess_message(raw, 'JOEL', [row])['issues']

    assert 'SUBJECT_TOO_LONG' in issues(subject='x' * 51)
    assert 'V2_LINK_INVALID' in issues(text=res['body_text'] + '\nhttps://evil.example/x')
    assert 'V2_LINK_INVALID' in issues(tid='v2-produktion-s2')
    assert 'V2_OPTOUT_LINE_MISSING' in issues(text=res['body_text'].replace('Abmelden', 'Stopp'))

    assert 'V2_LINK_INVALID' in issues(text=res['body_text'].replace('utm_campaign=', 'x=buyer%40example.org&utm_campaign='))
    assert 'V2_LINK_INVALID' in issues(text=res['body_text'].replace('utm_campaign=', 'who=buyer&utm_campaign='))
    assert 'V2_LINK_INVALID' in issues(text=res['body_text'].replace('utm_campaign=', 'n=Beispiel&utm_campaign='))


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
@pytest.mark.parametrize('owner', ['JOEL', 'JORDI'])
def test_body_contains_only_from_mailbox_address(segment, owner):
    from_addr = {'JOEL': 'j-cherino@hsb-boden.com', 'JORDI': 'j-post@hsb-boden.com'}[owner]
    row = SEGMENT_LEADS[segment]()
    thread = {'message_id': '<s1@hsb-boden.com>', 'subject': 'Betreff'}
    for step in (1, 2, 3):
        r = render_email_v2(row, owner, step, thread=thread)
        assert set(re.findall(r'[\w.+-]+@[\w.-]+\w', r['body_text'])) == {from_addr}


@pytest.mark.parametrize('segment', ['architekten', 'produktion'])
def test_body_word_range_without_company_and_contact(segment):
    row = SEGMENT_LEADS[segment](Firma='', Ansprechpartner='')
    first = render_email_v2(row, 'JOEL', 1)
    thread = {'message_id': '<s1@hsb-boden.com>', 'subject': first['subject']}
    for r in [first] + [render_email_v2(row, 'JOEL', s, thread=thread) for s in (2, 3)]:
        assert 60 <= len(body_only(r['body_text']).split()) <= 120, r['template_id']


def test_company_named_at_most_once_in_short_form():
    thread = {'message_id': '<s1@hsb-boden.com>', 'subject': 'Betreff'}
    for seg in SEGMENT_LEADS:
        row = SEGMENT_LEADS[seg](Firma='Muster Architekten GmbH, Beratende Ingenieure')
        for step in (1, 2, 3):
            r = render_email_v2(row, 'JOEL', step, thread=thread)
            assert r['body_text'].count('Muster Architekten') <= 1, (seg, step)
            assert 'GmbH, Beratende' not in r['body_text']
            assert 'Projekte bei' not in r['body_text']


@pytest.mark.parametrize('contact,expected', [
    ('Herr Max Müller', 'Sehr geehrter Herr Müller,'),
    ('Frau Dr. Anna von der Heide', 'Sehr geehrte Frau Dr. von der Heide,'),
    ('Mag. Arch. Raimund', 'Sehr geehrte Damen und Herren,'),
    ('Architekturhalle Mag. Arch. Raimund', 'Sehr geehrte Damen und Herren,'),
    ('Herr Dipl.-Ing. Peter Lang', 'Sehr geehrte Damen und Herren,'),
    ('Frau Einkauf', 'Sehr geehrte Damen und Herren,'),
    ('Herr hans meier', 'Sehr geehrte Damen und Herren,'),
    ('Raimund', 'Sehr geehrte Damen und Herren,'),
    ('', 'Sehr geehrte Damen und Herren,'),
])
def test_v2_greeting_only_with_verified_salutation_and_surname(contact, expected):
    from canonical_template_factory import anrede_v2
    assert anrede_v2({'Ansprechpartner': contact}) == expected
    assert render_email_v2(lead(Ansprechpartner=contact), 'JOEL', 1)['body_text'].startswith(expected + '\n')


def test_v2_greeting_prefers_explicit_salutation_fields():
    from canonical_template_factory import anrede_v2
    assert anrede_v2({'Anrede': 'Frau', 'Nachname': 'Kowalski'}) == 'Sehr geehrte Frau Kowalski,'
    assert anrede_v2({'Anrede': 'Divers', 'Nachname': 'Kowalski'}) == 'Sehr geehrte Damen und Herren,'


def test_greeting_uses_surname_only_and_keeps_title_and_particles():
    from canonical_template_factory import anrede_fuer_lead as a
    assert a({'Ansprechpartner': 'Herr Per Grunwald'}) == 'Sehr geehrter Herr Grunwald,'
    assert a({'Ansprechpartner': 'Frau Dr. Anna von der Heide'}) == 'Sehr geehrte Frau Dr. von der Heide,'
    assert a({'Ansprechpartner': 'Herr Müller'}) == 'Sehr geehrter Herr Müller,'
    assert a({'Ansprechpartner': 'Guten Tag Herr Günther Jauch'}) == 'Sehr geehrter Herr Jauch,'
    assert a({'Ansprechpartner': ''}) == 'Guten Tag,'


def test_greeting_keeps_name_suffix_with_surname():
    from canonical_template_factory import anrede_fuer_lead as a
    assert a({'Ansprechpartner': 'Herr Peter Wacker jun.'}) == 'Sehr geehrter Herr Wacker jun.,'
    assert a({'Ansprechpartner': 'Herr Hans Meier sen.'}) == 'Sehr geehrter Herr Meier sen.,'


def test_v2_html_part_carries_canonical_signature_with_logo():
    from canonical_template_factory import render_email_v2, LOGO_URL, REPAIR_URL
    lead = {"Lead_ID": "HSB-20260101-9", "Email": "a.b@beispiel.de", "Firma": "Beispiel GmbH",
            "Branche": "Lebensmittelproduktion", "Anrede": "Frau", "Nachname": "Beispiel"}
    r = render_email_v2(lead, owner="JORDI", step=1, variant="reparatur")
    html_part = r["body_html"]
    assert f'src="{LOGO_URL}"' in html_part and 'width="102" height="75"' in html_part
    assert "<strong" in html_part and "Jordie Post" in html_part
    assert f'href="{REPAIR_URL}"' in html_part
    assert "Registergericht: Amtsgericht Coesfeld, HRB 21481" in html_part
    assert "font-size:11px" in html_part  # Pflichtangaben klein
    assert LOGO_URL not in r["body_text"]  # Textteil bleibt reiner Text
    import re as _re
    # Ein Inhalts-Link, dazu Impressum und Datenschutz in der Fußzeile (Owner-Entscheidung 05.11.2026).
    assert _re.findall(r'href="(https?://[^"]+)"', html_part) == [
        REPAIR_URL, "https://www.hsb-boden.de/impressum/", "https://www.hsb-boden.de/datenschutz/"]


def test_v2_logo_is_not_counted_as_link():
    from canonical_template_factory import render_email_v2
    from com_mailbox_manager import ComMailboxClient
    from sales_reconciliation import assess_message
    lead = {"Lead_ID": "HSB-20260101-9", "Lead-ID": "HSB-20260101-9", "Email": "a.b@beispiel.de",
            "E-Mail": "a.b@beispiel.de", "Firma": "Beispiel GmbH", "Branche": "Lebensmittelproduktion",
            "Anrede": "Frau", "Nachname": "Beispiel", "Verantwortlicher": "JORDI"}
    r = render_email_v2(lead, owner="JORDI", step=1, variant="reparatur")
    client = ComMailboxClient.__new__(ComMailboxClient)
    client.cfg = {"display_name": "Jordie Post", "email": "j-post@hsb-boden.com"}
    raw, _ = client.build_draft_message(r["to_email"], r["subject"], body_text=r["body_text"],
                                        body_html=r["body_html"], template_id=r["template_id"],
                                        lead_id=lead["Lead_ID"], copy_rev=r["copy_rev"])
    result = assess_message(raw, "JORDI", [lead])
    assert result["issues"] == []
    assert result["links"] == ["https://www.hsb-boden.de/reparatur/", "https://www.hsb-boden.de/impressum/",
                               "https://www.hsb-boden.de/datenschutz/"]


def test_new_drafts_items_carry_html_signature():
    import inspect, new_drafts
    assert "'body_html': mail['body_html']" in inspect.getsource(new_drafts)
