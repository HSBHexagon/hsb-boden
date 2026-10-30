"""Neue v2-Entwürfe direkt aus dem CRM erzeugen: Lead → Text → Entwurf.

Kein Austausch alter Entwürfe, keine Zeilenbindungen. Der Versand (`dispatch_verified`) prüft jeden
Entwurf vor dem Senden erneut gegen das CRM. Auswahl: nur sendefähige Leads des Owners (nie CRM-Tier Z) ohne
vorhandenen Entwurf, Produktion vor Architekten (80/20), innerhalb des Segments Tier A → B → C.
"""
import fcntl
import os
import subprocess
from contextlib import contextmanager
from email.utils import getaddresses
from pathlib import Path

from canonical_template_factory import render_email_v2
from click_sync import click_url
from hsb_core import check_eligibility, normalize_owner
from lead_quality import deliverability_flags, fit_score, segment_for

PRODUCTION_SHARE = 0.8
MAX_DRAFTS_PER_MAILBOX = 6000
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


def select_leads(leads, owner, limit, existing_ids, mx_check=None, draft_recipients=()):
    """Sendefähige Leads des Owners ohne bestehenden Entwurf (v2 per Lead-ID, jeder andere per Empfänger),
    nie CRM-Tier Z, 80 % Produktion, Tier A → B → C."""
    owner = normalize_owner(owner)
    draft_recipients = {str(r).strip().lower() for r in draft_recipients}
    mx_cache = {}
    # Sperren gelten je Empfänger: eine Adresse in mehreren CRM-Zeilen wird nie angeschrieben.
    counts = {}
    for row in leads:
        email = str(row.get('E-Mail') or '').strip().lower()
        counts[email] = counts.get(email, 0) + 1
    buckets = {'produktion': [], 'architekten': []}
    for lead in leads:
        lid = str(lead.get('Lead-ID') or '').strip()
        if not lid or lid in existing_ids or normalize_owner(lead.get('Verantwortlicher')) != owner:
            continue
        if counts.get(str(lead.get('E-Mail') or '').strip().lower(), 0) != 1:
            continue
        if str(lead.get('E-Mail') or '').strip().lower() in draft_recipients:
            continue
        # Zurückgestellt (Website-Signale oder Operator): die Neuberechnung ohne Signale darf das nicht aufheben.
        if str(lead.get('Tier') or '').strip().upper() == 'Z':
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


def existing_draft_recipients(imap, folder='"Entw&APw-rfe"'):
    """Empfängeradressen aller Entwürfe im Ordner, auch alter v1-/Hand-Entwürfe ohne X-HSB-Lead-ID."""
    imap.select(folder, readonly=True)
    typ, data = imap.uid('SEARCH', None, 'ALL')
    if typ != 'OK' or not data or not data[0]:
        return set()
    typ, msg = imap.uid('FETCH', '1:*', '(BODY.PEEK[HEADER.FIELDS (TO)])')
    headers = [part[1].decode('utf-8', 'replace') for part in msg or [] if isinstance(part, tuple)]
    values = [line.split(':', 1)[1] for h in headers for line in h.splitlines() if line.lower().startswith('to:')]
    return {addr.strip().lower() for _, addr in getaddresses(values) if addr}


def has_draft_for(imap, recipient):
    """Gleiche Suche wie ComMailboxManager._assert_draft_capacity – ein Treffer dort bricht den ganzen Batch ab."""
    typ, data = imap.uid('search', None, 'HEADER', 'To', f'"{recipient.strip().lower()}"')
    return typ != 'OK' or bool(data and data[0])


@contextmanager
def owner_lock(owner, state_dir=None):
    """Exklusive Sperre je Postfach über Bestandsprüfung und APPEND (parallele Läufe warten nicht, sie brechen ab)."""
    base = Path(state_dir or os.environ.get('HSB_SALES_STATE_DIR', str(Path.home() / '.local/state/hsb-sales-os')))
    base.mkdir(parents=True, exist_ok=True)
    with open(base / f'create-v2-{normalize_owner(owner)}.lock', 'w') as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('CREATE_V2_ALREADY_RUNNING')
        yield


def create_v2_drafts(owner, limit, apply=False, *, leads, client, secret=None, mx_check=None, state_dir=None):
    """Dry-Run zählt nur; mit apply werden die Entwürfe per IMAP APPEND angelegt. Nie Versand."""
    with owner_lock(owner, state_dir):
        return _create(owner, limit, apply, leads, client, secret, mx_check)


def _create(owner, limit, apply, leads, client, secret, mx_check):
    with client._get_imap() as imap:
        existing = existing_v2_lead_ids(imap)
        recipients = existing_draft_recipients(imap)
        selected = select_leads(leads, owner, limit, existing, mx_check=mx_check, draft_recipients=recipients)
        # Rest-Absicherung: IMAP sucht To als Teilstring; was dort trifft, wird übersprungen statt den Batch abzubrechen.
        selected = [l for l in selected if not has_draft_for(imap, str(l['E-Mail']))]
    result = {'owner': normalize_owner(owner), 'existing_v2': len(existing),
              'existing_draft_recipients': len(recipients), 'selected': len(selected),
              'produktion': sum(segment_for(l) == 'produktion' for l in selected),
              'architekten': sum(segment_for(l) == 'architekten' for l in selected),
              'created': 0, 'dry_run': not apply, 'customer_emails_sent': 0}
    if apply and selected:
        if not secret:
            raise RuntimeError('CLICK_SECRET_MISSING: ohne Klick-Token keine Entwürfe (Messung wäre unvollständig)')
        results = client.create_drafts_batch(build_items(selected, owner, secret), max_existing=MAX_DRAFTS_PER_MAILBOX)
        result['created'] = sum(1 for r in results if r.get('ok'))
        result['failed'] = sum(1 for r in results if not r.get('ok'))
    return result
