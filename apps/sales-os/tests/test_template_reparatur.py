"""Vorlage v2, Variante Reparatur: Türöffner über Schadensbilder statt Firmenvorstellung."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from canonical_template_factory import REPAIR_URL, render_email_v2
from sales_reconciliation import assess_message
from test_template_v2 import SEGMENT_LEADS, URL_RE, body_only, build

SEGMENTS = ['architekten', 'produktion']

# Aussagen nur aus apps/website/src/data/services/boden-reparatur-instandsetzung.ts belegt;
# unbelegte Zusagen dürfen nie in einer Mail stehen.
UNBELEGT = ['24 Stunden', 'Montag', 'garantiert', 'verbindlich', 'sofort', '65 %', 'Haftung',
            'Südzucker', 'Notfall', 'innerhalb von',
            # Review PR #511: unterstellt Schaden, unbelegte Mengen/Wertungen.
            'Bodenschäden bei', 'mehr Sicherheit', 'Häufig', 'meist ', 'Schichtaufbau',
            # Owner-Entscheidung 2026-11-04: keine Massenfloskel und kein Online-Upload-Versprechen
            # (die Reparaturseite bietet Formular, E-Mail und Telefon, keinen Datei-Upload).
            'aktuelles Vorhaben in Ihrem Büro interessant', 'hochladen', 'Upload']
# Ausdrückliche Owner-Zusage 2026-11-04 (nicht aus der Website belegt, vom Owner vorgegeben).
OWNER_ZUSAGE = 'innerhalb eines Arbeitstags kostenfrei'


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


@pytest.mark.parametrize('variant', ['standard'])
def test_architect_first_contact_names_the_client_project_and_planning_role(variant):
    lead = SEGMENT_LEADS['architekten'](Firma='Muster Architekten GmbH')
    message = render_email_v2(lead, 'JOEL', 1, variant=variant)
    body = body_only(message['body_text'])

    assert 'für einen Bauherrn' in body
    assert 'Ausschreibung' in body
    assert 'Muster Architekten' in body
    assert 'Falls bei Muster Architekten' not in body


FIXED_SUBJECTS = {
    'produktion': 'Schadstelle im Industrieboden? Ersteinschätzung per Foto',
    'architekten': 'Industrieböden im Bestand – Einschätzung vor der Ausschreibung',
}


@pytest.mark.parametrize('segment', SEGMENTS)
def test_subject_is_fixed_owner_subject_without_company(segment):
    for firma in ('Musterbrauerei GmbH', 'Architekturhalle Mag. Arch. Raimund', ''):
        s1 = render_email_v2(SEGMENT_LEADS[segment](Firma=firma), 'JOEL', 1, variant='reparatur')
        assert s1['subject'] == FIXED_SUBJECTS[segment] and len(s1['subject']) <= 65


@pytest.mark.parametrize('segment', SEGMENTS)
def test_no_crm_company_or_title_artifacts_in_body(segment):
    lead = SEGMENT_LEADS[segment](Firma='Architekturhalle Mag. Arch. Raimund GmbH & Co. KG',
                                  Ansprechpartner='Mag. Arch. Raimund')
    for r in render_all(lambda: dict(lead)):
        text = r['subject'] + '\n' + r['body_text']
        for artifact in ('Architekturhalle', 'Mag.', 'Arch.', 'Raimund', 'GmbH & Co'):
            assert artifact not in text, (r['template_id'], artifact)
        assert r['body_text'].startswith('Sehr geehrte Damen und Herren,\n')


def test_first_contact_copy_follows_repair_first_strategy():
    prod = body_only(render_email_v2(SEGMENT_LEADS['produktion'](), 'JOEL', 1, variant='reparatur')['body_text'])
    for phrase in ('Fliese lose', 'Fuge ausbricht', 'Rinnenanschluss undicht', 'Gefälle und Abläufe',
                   'nicht gleich der gesamte Boden neu verlegt', OWNER_ZUSAGE, 'Foto'):
        assert phrase in prod, phrase
    plan = body_only(render_email_v2(SEGMENT_LEADS['architekten'](), 'JOEL', 1, variant='reparatur')['body_text'])
    for phrase in ('im Bestand', 'Fotos oder Bestandsdaten', 'erhalten bleiben', 'Ausschreibung',
                   'Fugen, Rinnen- oder Wandanschlüsse'):
        assert phrase in plan, phrase
    assert 'interessant?' not in plan


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
    assert URL_RE.findall(s1['body_text']) == [REPAIR_URL]
    # Kein Klick-Token mit Hash im Sichttext, auch wenn eines übergeben wird.
    custom = render_email_v2(SEGMENT_LEADS[segment](), 'JOEL', 1, click_url='https://www.hsb-boden.de/r/abc123',
                             variant='reparatur')
    assert URL_RE.findall(custom['body_text']) == [REPAIR_URL]


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


@pytest.mark.parametrize('segment', SEGMENTS)
def test_previous_repair_copy_is_flagged_outdated_but_repairable(segment):
    from draft_upgrade import REPAIRABLE
    row = SEGMENT_LEADS[segment](Ansprechpartner='Herr Beispiel')
    res = render_email_v2(dict(row), 'JOEL', 1, variant='reparatur')
    raw, _ = build(dict(res, copy_rev=None))
    issues = assess_message(raw, 'JOEL', [row])['issues']
    assert 'OUTDATED_REPAIR_COPY' in issues and set(issues) <= REPAIRABLE | {'V2_LINK_INVALID',
                                                                          'BODY_NOT_COMPANY_OR_CONTACT_SPECIFIC'}


def test_unknown_variant_rejected():
    with pytest.raises(ValueError):
        render_email_v2(SEGMENT_LEADS['produktion'](), 'JOEL', 1, variant='werbung')


def _html_links(owner='JOEL', **extra):
    import re
    from canonical_template_factory import render_email_v2
    lead = {'Lead-ID': 'HSB-20261105-9', 'E-Mail': 'einkauf@musterwerk.de', 'Firma': 'Musterwerk GmbH',
            'Branche': 'Lebensmittelproduktion', 'Ansprechpartner': 'Frau Beispiel', **extra}
    mail = render_email_v2(lead, owner, step=1, variant='reparatur')
    return mail, re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', mail['body_html'])


def test_footer_links_are_clickable_in_html():
    _, links = _html_links()
    assert ('https://www.hsb-boden.de/impressum/', 'Impressum') in links
    assert ('https://www.hsb-boden.de/datenschutz/', 'Datenschutz') in links


def test_optout_word_opens_a_reply_to_the_senders_own_mailbox():
    for owner, mailbox in (('JOEL', 'j-cherino@hsb-boden.com'), ('JORDI', 'j-post@hsb-boden.com')):
        mail, links = _html_links(owner)
        target = f'mailto:{mailbox}?subject=Abmelden&amp;body=HSB-ABMELDUNG%3A%20HSB-20261105-9'
        assert (target, '‚Abmelden‘') in links
        assert 'Antworten Sie kurz mit ‚Abmelden‘' in mail['body_text']
        assert 'https://www.hsb-boden.de/abmelden' not in mail['body_html']


def test_only_three_web_links_and_plain_text_stays_unlinked_legal_line():
    import re
    from canonical_template_factory import LOGO_URL, REPAIR_URL
    mail, links = _html_links()
    web = {u for u, _ in links if u.startswith('http')}
    assert web == {REPAIR_URL, 'https://www.hsb-boden.de/impressum/', 'https://www.hsb-boden.de/datenschutz/'}
    assert LOGO_URL not in web
    assert 'www.hsb-boden.de/impressum/ und www.hsb-boden.de/datenschutz/' in mail['body_text']
    assert re.findall(r'https?://[^\s<>"\x27]+', mail['body_text']) == [REPAIR_URL]


def test_legal_links_do_not_fail_the_audit_rule():
    from email.message import EmailMessage
    from canonical_template_factory import REPARATUR_COPY_REV, render_email_v2
    from sales_reconciliation import assess_message
    lead = {'Lead-ID': 'HSB-20261105-9', 'E-Mail': 'einkauf@musterwerk.de', 'Firma': 'Musterwerk GmbH',
            'Branche': 'Lebensmittelproduktion', 'Ansprechpartner': 'Frau Beispiel', 'Verantwortlicher': 'Joel Cherino Diaz'}
    mail = render_email_v2(lead, 'JOEL', step=1, variant='reparatur')
    msg = EmailMessage()
    msg['From'] = 'Joel Cherino Diaz <j-cherino@hsb-boden.com>'
    msg['To'] = lead['E-Mail']
    msg['Subject'] = mail['subject']
    msg['Message-ID'] = '<x@hsb-boden.com>'
    msg['X-HSB-Lead-ID'] = lead['Lead-ID']
    msg['X-HSB-Template-ID'] = mail['template_id']
    msg['X-HSB-Copy-Rev'] = REPARATUR_COPY_REV
    msg.set_content(mail['body_text'])
    msg.add_alternative(mail['body_html'], subtype='html')
    assert 'V2_LINK_INVALID' not in assess_message(msg.as_bytes(), 'JOEL', [lead])['issues']
    html = mail['body_html'].replace('</body>', '<a href="https://www.hsb-boden.de/kontakt/">K</a></body>')
    msg.get_body(('html',)).set_content(html, subtype='html')
    assert 'V2_LINK_INVALID' in assess_message(msg.as_bytes(), 'JOEL', [lead])['issues']


def test_optout_link_carries_the_same_token_as_list_unsubscribe():
    import html
    import re
    from email.message import EmailMessage
    from urllib.parse import parse_qs, unquote, urlsplit
    from outbound_safety import UNSUBSCRIBE_TOKEN_RE, add_list_unsubscribe
    mail, links = _html_links()
    href = html.unescape(next(u for u, t in links if t == '‚Abmelden‘'))
    assert add_list_unsubscribe(EmailMessage(), 'JOEL', 'HSB-20261105-9')['List-Unsubscribe'] == f'<{href}>'
    body = parse_qs(urlsplit(href).query)['body'][0]
    assert UNSUBSCRIBE_TOKEN_RE.findall(body) == ['HSB-20261105-9']
    assert '@musterwerk' not in unquote(href) and not re.search('https?://', href)
