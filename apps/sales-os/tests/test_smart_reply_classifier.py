import pytest
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from smart_reply_classifier import classify_reply_intent, evaluate_cadence_due


def test_classify_positive_interest():
    res = classify_reply_intent(
        subject="Re: Industrieböden für Molkerei",
        body="Guten Tag Herr Cherino, bitte senden Sie uns ein unverbindliches Angebot für unsere 1.200 m² Halle."
    )
    assert res["classification"] == "POSITIVE_INTEREST"
    assert res["stop_followup"] is True
    assert "angebot" in res["matched_keywords"] or "m²" in res["matched_keywords"]


def test_classify_out_of_office():
    res = classify_reply_intent(
        subject="Automatische Antwort: Abwesenheit",
        body="Ich befinde mich bis einschließlich 15.10. im Urlaub. In dringenden Fällen wenden Sie sich an Herrn Schmidt."
    )
    assert res["classification"] == "OUT_OF_OFFICE"
    assert res["stop_followup"] is False
    assert "urlaub" in res["matched_keywords"] or "automatische antwort" in res["matched_keywords"]


def test_classify_opt_out():
    res = classify_reply_intent(
        subject="Abmelden",
        body="Bitte löschen Sie unsere E-Mail-Adresse aus Ihrem Verteiler. Wir haben keinen Bedarf."
    )
    assert res["classification"] == "OPT_OUT"
    assert res["stop_followup"] is True
    assert "abmelden" in res["matched_keywords"] or "löschen" in res["matched_keywords"]


def test_classify_generic_needs_review():
    res = classify_reply_intent(
        subject="Re: Frage zur E-Mail",
        body="Wer hat Ihnen meine Visitenkarte gegeben?"
    )
    assert res["classification"] == "NEEDS_REVIEW"
    assert res["stop_followup"] is False


def test_evaluate_cadence_due_logic():
    import datetime
    now = datetime.datetime.now()
    
    # 8 days ago -> Due!
    sent_8d = (now - datetime.timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")
    due, reason = evaluate_cadence_due(sent_8d, reply_status="")
    assert due is True
    assert "Schritt 2 Follow-Up" in reason

    # 3 days ago -> Too early
    sent_3d = (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    due, reason = evaluate_cadence_due(sent_3d, reply_status="")
    assert due is False
    assert "Zu frueh" in reason

    # Already replied -> No follow up
    due, reason = evaluate_cadence_due(sent_8d, reply_status="replied")
    assert due is False
