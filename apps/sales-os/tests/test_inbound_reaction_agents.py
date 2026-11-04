import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from bounce_rescue_agent import BounceRescueAgent, RescueResult
from smart_vacation_agent import SmartVacationAgent, calculate_next_business_day

def test_bounce_rescue_agent_derives_domain():
    agent = BounceRescueAgent()
    domain = agent._derive_domain("https://www.brauerei-huber.de/kontakt", "chef@brauerei-huber.de")
    assert domain == "brauerei-huber.de"

def test_bounce_rescue_fallback_to_email_domain():
    agent = BounceRescueAgent()
    domain = agent._derive_domain("", "einkauf@molkerei-alpen.de")
    assert domain == "molkerei-alpen.de"

def test_bounce_rescue_skips_failed_email(monkeypatch):
    monkeypatch.setattr("bounce_rescue_agent.check_domain_mx", lambda dom: True)
    agent = BounceRescueAgent()
    # Mock search_alternative_emails
    agent.search_alternative_emails = lambda dom: [
        ("failed@kunde.de", "https://kunde.de/impressum", 0.9),
        ("info@kunde.de", "https://kunde.de/kontakt", 0.95)
    ]
    lead = {"Firma": "Kunde GmbH", "E-Mail": "failed@kunde.de"}
    res = agent.rescue_lead(lead, failed_email="failed@kunde.de")
    assert res.status == "SUCCESS"
    assert res.rescued_email == "info@kunde.de"

def test_smart_vacation_date_calculation():
    # Test weekday stays weekday
    weekday = calculate_next_business_day("2026-11-13")
    assert weekday == "2026-11-13"

    # Test weekend skip (2026-11-14 is Saturday -> should skip to Monday 2026-11-16)
    next_monday = calculate_next_business_day("2026-11-14")
    assert next_monday == "2026-11-16"

    # Test Sunday skip (2026-11-15 is Sunday -> should skip to Monday 2026-11-16)
    from_sunday = calculate_next_business_day("2026-11-15")
    assert from_sunday == "2026-11-16"

def test_smart_vacation_agent_processing():
    agent = SmartVacationAgent()
    lead = {
        "Lead_ID": "HSB-TEST-VAC",
        "Firma": "Brauhaus Köln GmbH",
        "E-Mail": "info@brauhaus-koeln.de",
        "Ansprechpartner": "Herr Schmitz"
    }
    reply = "Guten Tag, ich bin bis zum 05.11.2026 im Urlaub."
    today = datetime.date(2026, 10, 23)
    res = agent.process_reply(lead, reply, owner="JOEL", reference_date=today)
    assert res.status == "SCHEDULED"
    assert "2026-11-06" in res.followup_date
    assert "Brauhaus Köln GmbH" in res.subject
    assert "Willkommen zurück" in res.subject
    assert "Hier abmelden" in res.body_html
