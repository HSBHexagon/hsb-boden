import os
import sys
import pathlib
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine"))

from optout_helper import (
    generate_optout_token,
    verify_optout_token,
    build_optout_url,
    build_tracked_website_url,
)
from canonical_template_factory import render_canonical_email


def test_generate_and_verify_optout_token():
    lead_id = "HSB-20261012-0042"
    email = "vorstand@musterbrauerei.de"
    token = generate_optout_token(lead_id, email)
    assert len(token) == 16
    assert verify_optout_token(lead_id, email, token) is True
    # Falsche E-Mail scheitert
    assert verify_optout_token(lead_id, "anderer@muster.de", token) is False
    # Falsche Lead-ID scheitert
    assert verify_optout_token("HSB-99999999-0000", email, token) is False


def test_build_optout_url_structure():
    lead_id = "HSB-20261012-0042"
    email = "kontakt@molkerei-mueller.de"
    url = build_optout_url(lead_id, email)

    assert url.startswith("https://www.hsb-boden.de/abmelden?")
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert params["lead_id"][0] == lead_id
    assert params["email"][0] == email
    assert "token" in params
    assert params["utm_source"][0] == "outbound_email"
    assert params["utm_medium"][0] == "email"
    assert params["utm_campaign"][0] == "flyer_outreach_2026"
    assert params["utm_content"][0] == "footer_unsubscribe"


def test_build_tracked_website_url():
    url = build_tracked_website_url("signature_logo")
    assert url.startswith("https://www.hsb-boden.de/?")
    assert "utm_content=signature_logo" in url
    assert "utm_source=outbound_email" in url


def test_canonical_email_includes_tracked_optout_url():
    lead = {
        "Lead_ID": "HSB-20261012-0099",
        "Company": "Brauerei Test GmbH",
        "Contact": "Herr Markus Schneider",
        "Email": "m.schneider@brauerei-test.de",
    }
    rendered = render_canonical_email(lead, owner="JOEL", domain="com")
    body = rendered["body_html"]

    assert "https://www.hsb-boden.de/abmelden?" in body
    assert "lead_id=HSB-20261012-0099" in body
    assert "m.schneider%40brauerei-test.de" in body or "m.schneider@brauerei-test.de" in body
    assert "Hier abmelden" in body
    assert "Jordie Post" in body
