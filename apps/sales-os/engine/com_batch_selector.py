"""
HSB Sales OS - Lead Selector & Filter-Gate fuer .com Batch Engine.
Strikte Einhaltung von Compliance (§ 7 UWG), Dedup und Ausschlussfilter.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set


def _normalize_company(name: str) -> str:
    cleaned = re.sub(r'(gmbh|ag|kg|ohg|ug|haftungsbeschränkt|e\.k\.|co\.)', '', name, flags=re.IGNORECASE).strip()
    return re.sub(r'\s+', ' ', cleaned).lower()


def select_com_eligible_leads(
    leads: List[Dict[str, Any]],
    owner: str = 'JOEL',
    limit: int = 50,
    allow_overhaul: bool = False
) -> List[Dict[str, Any]]:
    """
    Waehlt autoritativ die naechsten qualifizierten Leads fuer den angegebenen Owner aus.
    """
    norm_owner = owner.strip().upper() if owner else 'JOEL'
    owner_match = 'JOEL' if norm_owner in ('JOEL', 'J-CHERINO') else 'JORDI'

    # Pre-pass: Sammle alle unterdrueckten Domains und Firmennamen
    suppressed_domains: Set[str] = set()
    suppressed_companies: Set[str] = set()
    for lead in leads:
        optout = str(lead.get('Opt_Out') or lead.get('Opt-out-Status') or '').lower().strip()
        suppressed = str(lead.get('Suppressed') or '').lower().strip()
        freigabe = str(lead.get('Versandfreigabe') or '').lower().strip()
        if optout in ('yes', 'ja') or suppressed in ('yes', 'ja'):
            em = str(lead.get('Email') or lead.get('E-Mail') or '').strip().lower()
            if '@' in em:
                dom = em.split('@')[-1]
                if dom not in {'test.de', 'example.com', 'example.org', 'gmail.com', 'gmx.de', 'web.de', 'outlook.com', 't-online.de', 'yahoo.de'}:
                    suppressed_domains.add(dom)
            comp = str(lead.get('Firma') or lead.get('Firmenname') or lead.get('Company') or '').strip()
            if comp:
                norm_c = _normalize_company(comp)
                if norm_c:
                    suppressed_companies.add(norm_c)

    eligible: List[Dict[str, Any]] = []
    seen_emails: Set[str] = set()

    for lead in leads:
        lead_owner = str(lead.get('Owner') or lead.get('Verantwortlicher') or '').upper()
        if owner_match == 'JOEL' and 'JOEL' not in lead_owner:
            continue
        if owner_match == 'JORDI' and 'JORD' not in lead_owner:
            continue

        freigabe = str(lead.get('Versandfreigabe') or '').lower().strip()
        if not allow_overhaul and freigabe not in ('yes', 'ja', '1', 'true'):
            continue

        drafted = str(lead.get('Drafted_At') or '').strip()
        sent = str(lead.get('Send_Status') or '').lower().strip()
        if sent in ('sent', 'gesendet'):
            continue
        if not allow_overhaul and drafted:
            continue

        optout = str(lead.get('Opt_Out') or lead.get('Opt-out-Status') or '').lower().strip()
        suppressed = str(lead.get('Suppressed') or '').lower().strip()
        if optout in ('yes', 'ja') or suppressed in ('yes', 'ja'):
            continue

        email = str(lead.get('Email') or lead.get('E-Mail') or '').strip().lower()
        if not email or '@' not in email or email in seen_emails:
            continue

        domain = email.split('@')[-1]
        if domain in suppressed_domains:
            continue

        comp = str(lead.get('Firma') or lead.get('Firmenname') or lead.get('Company') or '').strip()
        if comp and _normalize_company(comp) in suppressed_companies:
            continue

        seen_emails.add(email)
        eligible.append(lead)
        if len(eligible) >= limit:
            break

    return eligible
