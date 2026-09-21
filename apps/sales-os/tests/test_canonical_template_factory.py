from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from canonical_template_factory import render_canonical_email


def test_render_canonical_email_valid_lead():
    lead = {
        "Lead_ID": "TEST-001",
        "Firmenname": "Molkerei Biedermann AG",
        "Email": "info@biedermann.ch",
        "Anrede": "Herr",
        "Nachname": "Muster",
    }
    rendered = render_canonical_email(lead, owner="JOEL")
    assert rendered["to_address"] == "info@biedermann.ch"
    assert "Molkerei Biedermann AG" in rendered["subject"]
    assert "Jordie Post" in rendered["body_html"]
    assert "Jordi Post" not in rendered["body_html"]
    assert "HSB-Flyer-Joel-Cherino_FINAL.pdf" in rendered["flyer_filename"]
    assert "hsb-boden-logo.png" in rendered["body_html"]
    assert 'width="102" height="75"' in rendered["body_html"]


def test_render_canonical_email_fail_closed_on_missing_email():
    lead = {"Lead_ID": "TEST-EMPTY", "Firmenname": "Dummy GmbH", "Email": ""}
    with pytest.raises(ValueError, match="Recipient email missing or invalid"):
        render_canonical_email(lead, owner="JOEL")


def test_render_canonical_email_fail_closed_on_invalid_email():
    lead = {"Lead_ID": "TEST-NO-AT", "Firmenname": "Dummy GmbH", "Email": "invalid-email"}
    with pytest.raises(ValueError, match="Recipient email missing or invalid"):
        render_canonical_email(lead, owner="JOEL")


def test_render_canonical_email_jordie_owner():
    lead = {
        "Lead_ID": "TEST-002",
        "Firmenname": "Brauerei Test GmbH",
        "E-Mail": "kontakt@brauerei-test.de",
        "Anrede": "Frau",
        "Nachname": "Schmidt",
    }
    rendered = render_canonical_email(lead, owner="JORDI")
    assert rendered["to_address"] == "kontakt@brauerei-test.de"
    assert "HSB-Flyer-Jordie-Post_FINAL.pdf" in rendered["flyer_filename"]
    assert "Jordie Post" in rendered["body_html"]
    assert "j.post@hsb-boden.de" in rendered["body_html"]
    assert "Geschäftsführer" in rendered["body_html"]


def test_render_canonical_email_generic_consumer_email_fallback():
    lead = {
        "Lead_ID": "TEST-003",
        "Firmenname": "Private Bauherr",
        "Email": "bauherr@gmail.com",
    }
    rendered = render_canonical_email(lead, owner="JOEL")
    assert "Ihr Unternehmen" in rendered["subject"]
    assert "Guten Tag," in rendered["body_html"]
