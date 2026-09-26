"""
HSB Sales OS - Lead Selector & Filter-Gate fuer .com Batch Engine.
Strikte Einhaltung von Compliance (§ 7 UWG), Dedup und Ausschlussfilter.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set


def select_com_eligible_leads(
    leads: List[Dict[str, Any]],
    owner: str = "JOEL",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Waehlt autoritativ die naechsten qualifizierten Leads fuer den angegebenen Owner aus.
    
    Filter-Kriterien:
    - Owner-Match: Lead gehoert zu Joel bzw. Jordi
    - Versandfreigabe: 'yes' / 'ja' / '1' / 'true'
    - Drafted_At: muss leer sein (noch kein Entwurf erzeugt)
    - Send_Status: darf nicht 'sent' / 'gesendet' sein
    - Opt-Out / Suppression: ausgeschlossen
    - E-Mail-Syntax & Dedup: gueltige Adresse mit '@', keine Duplikate
    """
    norm_owner = owner.strip().upper() if owner else "JOEL"
    owner_match = "JOEL" if norm_owner in ("JOEL", "J-CHERINO") else "JORDI"

    eligible: List[Dict[str, Any]] = []
    seen_emails: Set[str] = set()

    for lead in leads:
        lead_owner = str(lead.get("Owner") or lead.get("Verantwortlicher") or "").upper()
        if owner_match == "JOEL" and "JOEL" not in lead_owner:
            continue
        if owner_match == "JORDI" and "JORD" not in lead_owner:
            continue

        freigabe = str(lead.get("Versandfreigabe") or "").lower().strip()
        if freigabe not in ("yes", "ja", "1", "true"):
            continue

        drafted = str(lead.get("Drafted_At") or "").strip()
        sent = str(lead.get("Send_Status") or "").lower().strip()
        if drafted or sent in ("sent", "gesendet"):
            continue

        optout = str(lead.get("Opt_Out") or lead.get("Opt-out-Status") or "").lower().strip()
        suppressed = str(lead.get("Suppressed") or "").lower().strip()
        if optout in ("yes", "ja") or suppressed in ("yes", "ja"):
            continue

        email = str(lead.get("Email") or lead.get("E-Mail") or "").strip().lower()
        if not email or "@" not in email or email in seen_emails:
            continue

        seen_emails.add(email)
        eligible.append(lead)
        if len(eligible) >= limit:
            break

    return eligible
