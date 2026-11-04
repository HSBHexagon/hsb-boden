#!/usr/bin/env python3
"""
HSB Sales OS - Opt-Out & Tracking Helper.
Generates secure HMAC tokens and fully tracked UTM URLs for outbound campaigns.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import urllib.parse
from typing import Dict, Any

OPTOUT_SECRET = os.environ.get("HSB_OPTOUT_SECRET", "hsb-hexagon-2026-optout-token-salt")
BASE_URL = "https://www.hsb-boden.de"


def generate_optout_token(lead_id: str, email: str) -> str:
    """Erzeugt ein manipulationssicheres HMAC-SHA256 Token (16 Hex-Zeichen)."""
    norm_lead = str(lead_id or "").strip()
    norm_email = str(email or "").strip().lower()
    raw = f"{norm_lead}:{norm_email}".encode("utf-8")
    return hmac.new(OPTOUT_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()[:16]


def verify_optout_token(lead_id: str, email: str, token: str) -> bool:
    """Verifiziert das HMAC-Token gegen Lead-ID und E-Mail."""
    expected = generate_optout_token(lead_id, email)
    return hmac.compare_digest(expected, str(token or "").strip())


def build_optout_url(
    lead_id: str,
    email: str,
    campaign: str = "flyer_outreach_2026",
    base_url: str = BASE_URL
) -> str:
    """Erzeugt die vollständige, getrackte und signierte Abmelde-URL."""
    norm_lead = str(lead_id or "").strip()
    norm_email = str(email or "").strip().lower()
    token = generate_optout_token(norm_lead, norm_email)
    params = {
        "lead_id": norm_lead,
        "email": norm_email,
        "token": token,
        "utm_source": "outbound_email",
        "utm_medium": "email",
        "utm_campaign": campaign,
        "utm_content": "footer_unsubscribe"
    }
    return f"{base_url.rstrip('/')}/abmelden?{urllib.parse.urlencode(params)}"


def build_tracked_website_url(
    content: str = "signature_website",
    campaign: str = "flyer_outreach_2026",
    base_url: str = BASE_URL
) -> str:
    """Erzeugt eine voll getrackte UTM-URL zur Firmen-Website."""
    params = {
        "utm_source": "outbound_email",
        "utm_medium": "email",
        "utm_campaign": campaign,
        "utm_content": content
    }
    return f"{base_url.rstrip('/')}/?{urllib.parse.urlencode(params)}"
