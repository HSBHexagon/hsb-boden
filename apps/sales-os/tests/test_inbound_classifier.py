from pathlib import Path
import sys
import datetime
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from inbound_classifier import classify_inbound_message, extract_return_date, InboundClassificationResult, strip_quoted_reply

def test_classify_bounce_undeliverable():
    subj = "Undeliverable: Industrieböden für Maier GmbH"
    body = "Diagnostic-Code: smtp; 550 5.1.1 User unknown: info@maier-gmbh.de"
    res = classify_inbound_message(sender="mailer-daemon@kasserver.com", subject=subj, body=body)
    assert res.category == "BOUNCE"
    assert res.extracted_email == "info@maier-gmbh.de"

def test_classify_ooo_with_14_days():
    today = datetime.date(2026, 10, 22)
    subj = "Automatische Antwort: Bin im Urlaub"
    body = "Guten Tag, ich bin für die nächsten 14 Tage nicht im Büro und melde mich danach."
    res = classify_inbound_message(sender="chef@kunde.de", subject=subj, body=body, reference_date=today)
    assert res.category == "OOO_URLAUB"
    assert res.recontact_date == "2026-11-05"

def test_classify_ooo_with_specific_date():
    today = datetime.date(2026, 10, 22)
    subj = "Abwesenheitsnotiz"
    body = "Ich bin bis einschließlich 12.11.2026 im Urlaub."
    res = classify_inbound_message(sender="einkauf@kunde.de", subject=subj, body=body, reference_date=today)
    assert res.category == "OOO_URLAUB"
    assert res.recontact_date == "2026-11-13"

def test_classify_optout_widerspruch():
    subj = "Re: Industrieböden für Schmidt GmbH"
    body = "Bitte nehmen Sie mich sofort aus Ihrem Verteiler und löschen Sie meine Daten. Kein Interesse."
    res = classify_inbound_message(sender="gs@schmidt.de", subject=subj, body=body)
    assert res.category == "OPTOUT"

def test_classify_hot_lead():
    subj = "Re: Industrieböden für Brauerei Weber"
    body = "Guten Tag Herr Post, das Thema passt gerade gut. Wann können Sie bei uns vorbeikommen?"
    res = classify_inbound_message(sender="leitung@brauerei-weber.de", subject=subj, body=body)
    assert res.category == "HOT_LEAD"

def test_classify_neutral_fallback():
    subj = "Re: Industrieböden für Logistikzentrum"
    body = "Können Sie mir sagen, woher Sie meine Kontaktdaten haben?"
    res = classify_inbound_message(sender="info@logistik.de", subject=subj, body=body)
    assert res.category == "NEUTRAL"

def test_internal_sender_not_optout():
    subj = "Kopie: Industrieböden für Kunde"
    body = "Hier ist der Footer: Impressum · Datenschutz · Hier abmelden"
    res = classify_inbound_message(sender="Joel Cherino Diaz <j-cherino@hsb-boden.com>", subject=subj, body=body)
    assert res.category == "NEUTRAL"

def test_hot_lead_with_quoted_optout_footer():
    subj = "Re: Industrieböden für Werkshalle"
    body = (
        "Guten Tag Herr Cherino,\n"
        "wir hätten gerne ein Angebot für 500qm Industrieboden.\n\n"
        "-----Original Message-----\n"
        "Von: j-cherino@hsb-boden.com\n"
        "Impressum · Datenschutz · Hier abmelden"
    )
    res = classify_inbound_message(sender="kunde@industrie.de", subject=subj, body=body)
    assert res.category == "HOT_LEAD"
