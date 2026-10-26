from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from mass_draft_generator import build_draft_payload

def test_build_draft_payload_contains_no_attachment_and_valid_link():
    lead = {
        "Lead_ID": "HSB-TEST-999",
        "Firma": "Brauerei Müller GmbH",
        "E-Mail": "info@mueller-braeu.de",
        "Ansprechpartner": "Herr Müller",
        "_row": 100
    }
    payload = build_draft_payload(owner="JORDI", lead=lead)
    assert payload["to_email"] == "info@mueller-braeu.de"
    assert "Brauerei Müller" in payload["subject"]
    assert "www.hsb-boden.de/flyer" in payload["body_html"]
    assert payload["flyer_path"] is None
