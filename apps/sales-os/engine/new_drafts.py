"""Neue v2-Entwürfe direkt aus dem CRM erzeugen: Lead → Text → Entwurf.

Kein Austausch alter Entwürfe, keine Zeilenbindungen. Der Versand (`dispatch_verified`) prüft jeden
Entwurf vor dem Senden erneut gegen das CRM. Auswahl: nur sendefähige Leads des Owners ohne
vorhandenen v2-Entwurf, Produktion vor Architekten (80/20), innerhalb des Segments Tier A → B → C.
"""
import os
import subprocess

from canonical_template_factory import render_email_v2
from click_sync import click_url
from hsb_core import check_eligibility, normalize_owner
from lead_quality import deliverability_flags, fit_score, segment_for

PRODUCTION_SHARE = 0.8
TIER_ORDER = {'A': 0, 'B': 1, 'C': 2}


def click_secret():
    """CLICK_SECRET aus der Umgebung oder dem macOS-Schlüsselbund; None → Link ohne Lead-Bezug."""
    secret = os.environ.get('HSB_CLICK_SECRET')
    if secret:
        return secret
    try:
        out = subprocess.run(['security', 'find-generic-password', '-a', os.environ.get('USER', ''),
                              '-s', 'hsb-click-secret', '-w'], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def select_leads(leads, owner, limit, existing_ids, mx_check=None):
    """Sendefähige Leads des Owners ohne bestehenden v2-Entwurf, 80 % Produktion, Tier A → B → C."""
    owner = normalize_owner(owner)
    mx_cache = {}
    buckets = {'produktion': [], 'architekten': []}
    for lead in leads:
        lid = str(lead.get('Lead-ID') or '').strip()
        if not lid or lid in existing_ids or normalize_owner(lead.get('Verantwortlicher')) != owner:
            continue
        lead = dict(lead)
        lead['Deliverability_Flags'] = deliverability_flags(lead, mx_cache, set(), mx_check=mx_check)
        if not check_eligibility(lead).eligible:
            continue
        score, tier, _ = fit_score(lead, {'positive': [], 'negative': [], 'quotes': []})
        if tier not in TIER_ORDER:
            continue
        buckets[segment_for(lead)].append((TIER_ORDER[tier], -score, lid, lead))
    for items in buckets.values():
        items.sort(key=lambda x: x[:3])
    want_prod = min(len(buckets['produktion']), round(limit * PRODUCTION_SHARE))
    want_arch = min(len(buckets['architekten']), limit - want_prod)
    want_prod = min(len(buckets['produktion']), limit - want_arch)
    return [x[3] for x in buckets['produktion'][:want_prod] + buckets['architekten'][:want_arch]]


def build_items(selected, owner, secret):
    items = []
    for lead in selected:
        lid = str(lead['Lead-ID']).strip()
        seg = segment_for(lead)
        mail = render_email_v2(lead, owner, step=1, click_url=click_url(lid, seg, secret))
        items.append({'to_email': mail['to_email'], 'subject': mail['subject'], 'body_text': mail['body_text'],
                      'template_id': mail['template_id'], 'lead_id': lid})
    return items


def existing_v2_lead_ids(imap, folder='"Entw&APw-rfe"'):
    """Lead-IDs, für die im Entwurfsordner schon ein v2-Entwurf liegt (Doppel-Schutz)."""
    imap.select(folder, readonly=True)
    typ, data = imap.uid('SEARCH', None, 'HEADER', 'X-HSB-Template-ID', 'v2-')
    uids = data[0].split() if typ == 'OK' and data and data[0] else []
    ids = set()
    for uid in uids:
        typ, msg = imap.uid('FETCH', uid, '(BODY.PEEK[HEADER.FIELDS (X-HSB-LEAD-ID)])')
        for part in msg or []:
            if isinstance(part, tuple):
                for line in part[1].decode('utf-8', 'replace').splitlines():
                    if line.lower().startswith('x-hsb-lead-id:'):
                        ids.add(line.split(':', 1)[1].strip())
    return ids


def create_v2_drafts(owner, limit, apply=False, *, leads, client, secret=None, mx_check=None):
    """Dry-Run zählt nur; mit apply werden die Entwürfe per IMAP APPEND angelegt. Nie Versand."""
    with client._get_imap() as imap:
        existing = existing_v2_lead_ids(imap)
    selected = select_leads(leads, owner, limit, existing, mx_check=mx_check)
    result = {'owner': normalize_owner(owner), 'existing_v2': len(existing), 'selected': len(selected),
              'produktion': sum(segment_for(l) == 'produktion' for l in selected),
              'architekten': sum(segment_for(l) == 'architekten' for l in selected),
              'created': 0, 'dry_run': not apply, 'customer_emails_sent': 0}
    if apply and selected:
        results = client.create_drafts_batch(build_items(selected, owner, secret))
        result['created'] = sum(1 for r in results if r.get('ok'))
        result['failed'] = sum(1 for r in results if not r.get('ok'))
    return result
