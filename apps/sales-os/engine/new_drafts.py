"""Neue v2-Entwürfe direkt aus dem CRM erzeugen: Lead → Text → Entwurf.

Kein Austausch alter Entwürfe, keine Zeilenbindungen. Der Versand (`dispatch_verified`) prüft jeden
Entwurf vor dem Senden erneut gegen das CRM. Auswahl: nur sendefähige Leads des Owners (nie CRM-Tier Z) ohne
vorhandenen Entwurf, Produktion vor Architekten (80/20), innerhalb des Segments Tier A → B → C.
"""
try:
    import fcntl
except ImportError:
    fcntl = None
try:
    import msvcrt
except ImportError:
    msvcrt = None

import os
import subprocess
from contextlib import contextmanager
from email.utils import getaddresses
from pathlib import Path

from canonical_template_factory import render_email_v2
from click_sync import click_url
from hsb_core import check_eligibility, normalize_owner
import lead_quality
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
        segment = segment_for(lead)
        if segment == 'architekten' and not lead_quality.planner_outreach_allowed(lead):
            continue
        lead = dict(lead)
        lead['Deliverability_Flags'] = deliverability_flags(lead, mx_cache, set(), mx_check=mx_check)
        if not check_eligibility(lead).eligible:
            continue
        score, tier, _ = fit_score(lead, {'positive': [], 'negative': [], 'quotes': []})
        if tier not in TIER_ORDER:
            continue
        buckets[segment].append((TIER_ORDER[tier], -score, lid, lead))
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
        # Owner-Entscheidung 2026-11-04: neue .com-Entwürfe nur noch in der Reparatur-Fassung,
        # mit lesbarem Reparatur-Link statt Klick-Token.
        mail = render_email_v2(lead, owner, step=1, click_url=click_url(lid, seg, secret), variant='reparatur')
        items.append({'to_email': mail['to_email'], 'subject': mail['subject'], 'body_text': mail['body_text'], 'body_html': mail['body_html'],
                      'template_id': mail['template_id'], 'lead_id': lid, 'copy_rev': mail['copy_rev']})
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
    lock_path = base / f'create-v2-{normalize_owner(owner)}.lock'
    with open(lock_path, 'a+') as fh:
        if fcntl:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('CREATE_V2_ALREADY_RUNNING')
            try:
                yield
            finally:
                try:
                    fcntl.flock(fh, fcntl.LOCK_UN)
                except Exception:
                    pass
        elif msvcrt:
            fh.seek(0)
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except (OSError, PermissionError):
                raise RuntimeError('CREATE_V2_ALREADY_RUNNING')
            try:
                yield
            finally:
                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
        else:
            yield


def create_v2_drafts(owner, limit, apply=False, *, leads, client, secret=None, mx_check=None, state_dir=None,
                     lock_client=None):
    """Dry-Run zählt nur; mit apply werden die Entwürfe per IMAP APPEND angelegt. Nie Versand.
    Apply hält zusätzlich die gemeinsame JOEL-Versandsperre: ein APPEND während eines Versand-Scans
    würde MAILBOX_CHANGED_DURING_SCAN auslösen und den Versand bis zur manuellen Klärung sperren."""
    with owner_lock(owner, state_dir):
        if not apply:
            return _create(owner, limit, apply, leads, client, secret, mx_check)
        # Vorbedingung vor der Sperre: sie bleibt bei jedem Fehler stehen und würde sonst den Versand blockieren.
        if not secret:
            raise RuntimeError('CLICK_SECRET_MISSING: ohne Klick-Token keine Entwürfe (Messung wäre unvollständig)')
        from outbound_safety import mailbox_dispatch_lock
        if lock_client is None:
            from com_mailbox_manager import ComMailboxClient
            lock_client = ComMailboxClient('JOEL')
        with mailbox_dispatch_lock(lock_client):
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


def write_crm_draft_bindings(svc, spreadsheet_id, headers, updates, chunk=100):
    """Schreibt Draft_ID, Email_Template_ID (und optional Drafted_At) blockweise mit Zeilenidentität und Readback.
    chunk=100 hält die batchGet-URL sicher unter Googles 16-KB-GFE-Limit.
    updates: [(row, lead_id, draft_id, template_id, drafted_at)]."""
    if not updates:
        return 0
    from signature_refresh import _col_letter
    col_draft = _col_letter(headers.index('Draft_ID'))
    col_tmpl = _col_letter(headers.index('Email_Template_ID'))
    col_at = _col_letter(headers.index('Drafted_At')) if 'Drafted_At' in headers else None
    api = svc.spreadsheets().values()

    def read_check(rows):
        ranges = ([f'ALL_LEADS!A{r}' for r in rows]
                  + [f'ALL_LEADS!{col_draft}{r}' for r in rows]
                  + [f'ALL_LEADS!{col_tmpl}{r}' for r in rows])
        got = api.batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute().get('valueRanges', [])
        vals = [((g.get('values') or [['']])[0] or [''])[0] for g in got]
        n = len(rows)
        return vals[:n], vals[n:2 * n], vals[2 * n:3 * n]

    written = 0
    for i in range(0, len(updates), chunk):
        part = updates[i:i + chunk]
        rows = [r for r, *_ in part]
        ids, _, _ = read_check(rows)
        if ids != [lid for _, lid, *_ in part]:
            raise RuntimeError('CRM_ROW_IDENTITY_CHANGED')
        data = []
        for r, _, mid, tmpl, stamped in part:
            data.append({'range': f'ALL_LEADS!{col_draft}{r}', 'values': [[mid]]})
            data.append({'range': f'ALL_LEADS!{col_tmpl}{r}', 'values': [[tmpl]]})
            if col_at:
                data.append({'range': f'ALL_LEADS!{col_at}{r}', 'values': [[stamped]]})
        api.batchUpdate(spreadsheetId=spreadsheet_id, body={'valueInputOption': 'RAW', 'data': data}).execute()
        ids, drafts_back, tmpls_back = read_check(rows)
        if (ids != [lid for _, lid, *_ in part]
                or drafts_back != [mid for _, _, mid, *_ in part]
                or tmpls_back != [tmpl for _, _, _, tmpl, _ in part]):
            raise RuntimeError('CRM_READBACK_MISMATCH')
        written += len(part)
    return written


def _recover_unlinked_v2_draft(imap, folder, lead, owner, target_template, assess_message, deep_check):
    """Findet einen bereits im Postfach liegenden gültigen Reparatur-Erstkontakt dieses Leads ohne neuen APPEND."""
    from draft_upgrade import _raw, _select
    from email import policy
    from email.parser import BytesParser
    _select(imap, folder, readonly=True)
    typ, data = imap.uid('SEARCH', None, 'HEADER', 'X-HSB-Lead-ID', f'"{lead["Lead-ID"]}"')
    if typ != 'OK' or not data or not data[0]:
        return None
    uids = [u.decode() for u in data[0].split()]
    if len(uids) != 1:
        return None
    raw = _raw(imap, uids[0])
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    mid = str(msg.get('Message-ID') or '').strip()
    if not mid:
        return None
    if set(assess_message(raw, owner, [lead])['issues']) - {'COMPANY_UNVERIFIED'}:
        return None
    if deep_check(raw, dict(lead, Draft_ID=mid, Email_Template_ID=target_template), owner):
        return None
    return mid


def fill_missing_drafts(owners, balances, drafts, leads, apply=False, *, make_client=None, lock_client=None,
                        assess_message=None, svc=None, spreadsheet_id=None, headers=None, connections=3):
    """Erzeugt Reparatur-Erstkontakte für alle sendefähigen Leads ohne Entwurf (balances mit Grund ['NO_DRAFT'])
    und bindet Draft_ID sowie Email_Template_ID im CRM. Versendet niemals."""
    from collections import Counter
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    from email.utils import make_msgid
    import imaplib
    import threading
    import time
    from draft_upgrade import _find, _raw, _select
    import draft_verify as dv
    from sales_reconciliation import queue_block_reasons
    from signature_refresh import _crlf

    if assess_message is None:
        from sales_reconciliation import assess_message
    if make_client is None:
        from com_mailbox_manager import ComMailboxClient
        make_client = ComMailboxClient

    byid = {}
    for row in leads:
        byid.setdefault(str(row.get('Lead-ID') or ''), []).append(row)
    draft_lids = {str(d.get('lead_id') or '') for d in drafts}
    draft_emails = {str(a).strip().lower() for d in drafts for a in (d.get('recipients') or [])}

    plan = {}
    result = {'dry_run': not apply, 'customer_emails_sent': 0, 'crm_writes': 0, 'per_owner': {}}
    for raw_owner in owners:
        owner = normalize_owner(raw_owner)
        skipped = Counter()
        chosen = []
        for bal in balances:
            if normalize_owner(bal.get('owner')) != owner or bal.get('reasons') != ['NO_DRAFT']:
                continue
            lid = str(bal.get('lead_id') or '').strip()
            matches = byid.get(lid, [])
            if len(matches) != 1:
                skipped['AMBIGUOUS_LEAD'] += 1
                continue
            lead = dict(matches[0])
            email = str(lead.get('E-Mail') or '').strip().lower()
            if lid in draft_lids or email in draft_emails:
                skipped['ALREADY_IN_AUDIT_DRAFTS'] += 1
                continue
            if normalize_owner(lead.get('Verantwortlicher')) != owner or queue_block_reasons(lead):
                skipped['INELIGIBLE'] += 1
                continue
            if segment_for(lead) == 'architekten' and not lead_quality.planner_outreach_allowed(lead):
                skipped['PLANNING_PROJECT_UNVERIFIED'] += 1
                continue
            chosen.append(lead)
        plan[owner] = chosen
        result['per_owner'][owner] = {'selected': len(chosen), 'created': 0, 'recovered': 0, 'skipped': dict(skipped)}

    if not apply or not any(plan.values()):
        return result
    if svc is None or spreadsheet_id is None or not headers:
        raise ValueError('CRM_SERVICE_REQUIRED_FOR_DRAFT_BINDING')
    if 'Draft_ID' not in headers or 'Email_Template_ID' not in headers:
        raise ValueError('CRM_DRAFT_COLUMNS_MISSING')
    if any(not l.get('_row') for chosen in plan.values() for l in chosen):
        raise ValueError('CRM_ROW_MISSING')

    from outbound_safety import mailbox_dispatch_lock
    if lock_client is None:
        lock_client = make_client('JOEL')

    done_updates = []
    lock = threading.Lock()
    with mailbox_dispatch_lock(lock_client, release_on_error=True):
        live_rows = svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range='ALL_LEADS!A1:BU6425').execute().get('values', [])
        if not live_rows:
            raise RuntimeError('CRM_LIVE_EMPTY')
        live_headers = live_rows[0]

        work = {}
        for owner, chosen in plan.items():
            if not chosen:
                continue
            stats = Counter(result['per_owner'][owner]['skipped'])
            live_checked = []
            for lead in chosen:
                row_idx = lead['_row']
                raw_row = live_rows[row_idx - 1] if 1 < row_idx <= len(live_rows) else []
                live_lead = dict(zip(live_headers, raw_row), _row=row_idx)
                if str(live_lead.get('Lead-ID') or '') != str(lead['Lead-ID']):
                    raise RuntimeError('CRM_ROW_IDENTITY_CHANGED')
                if (normalize_owner(live_lead.get('Verantwortlicher')) != owner
                        or str(live_lead.get('E-Mail') or '').strip().lower() != str(lead.get('E-Mail') or '').strip().lower()
                        or queue_block_reasons(live_lead)):
                    stats['LIVE_BLOCKED'] += 1
                    continue
                live_checked.append(live_lead)

            client0 = make_client(owner)
            folder = client0.cfg['drafts_folder']
            with client0._get_imap() as imap:
                validity = _select(imap, folder, readonly=True)
                existing_ids = existing_v2_lead_ids(imap, folder)
                existing_rcpts = existing_draft_recipients(imap, folder)
                to_append = []
                for lead in live_checked:
                    lid = str(lead['Lead-ID']).strip()
                    email = str(lead['E-Mail']).strip().lower()
                    target_tmpl = f"v2-{segment_for(lead)}-reparatur-s1"
                    if lid in existing_ids or email in existing_rcpts:
                        recovered_mid = _recover_unlinked_v2_draft(
                            imap, folder, lead, owner, target_tmpl, assess_message, dv.deep_check)
                        if recovered_mid:
                            result['per_owner'][owner]['recovered'] += 1
                            done_updates.append((lead['_row'], lid, recovered_mid, target_tmpl,
                                                 datetime.now(timezone.utc).isoformat()))
                        else:
                            stats['ALREADY_HAS_DRAFT'] += 1
                    else:
                        to_append.append(lead)
            result['per_owner'][owner]['skipped'] = dict(stats)
            if to_append:
                work[owner] = (folder, validity, to_append)

        def append_batch(owner, folder, validity, batch):
            client = make_client(owner)
            imap = None
            try:
                for lead in batch:
                    lid = str(lead['Lead-ID']).strip()
                    mail = render_email_v2(lead, owner, step=1, variant='reparatur')
                    mid = make_msgid(domain='hsb-boden.com')
                    raw, _ = client.build_draft_message(
                        mail['to_email'], mail['subject'], body_text=mail['body_text'],
                        body_html=mail['body_html'], template_id=mail['template_id'],
                        lead_id=lid, custom_message_id=mid, copy_rev=mail['copy_rev'])
                    raw = _crlf(raw)
                    if set(assess_message(raw, owner, [lead])['issues']) - {'COMPANY_UNVERIFIED'}:
                        raise RuntimeError('NEW_DRAFT_REVALIDATION_FAILED')
                    if dv.deep_check(raw, dict(lead, Draft_ID=mid, Email_Template_ID=mail['template_id']), owner):
                        raise RuntimeError('NEW_DRAFT_DEEP_CHECK_FAILED')
                    for attempt in range(3):
                        try:
                            if imap is None:
                                imap = client._get_imap()
                                _select(imap, folder, validity, readonly=False)
                            break
                        except (imaplib.IMAP4.abort, OSError):
                            imap = None
                            if attempt == 2:
                                raise
                    try:
                        typ, _ = imap.append(folder, r'(\Draft)', imaplib.Time2Internaldate(time.time()), raw)
                    except (imaplib.IMAP4.abort, OSError) as exc:
                        raise RuntimeError('UNCERTAIN_APPEND_REQUIRES_RECONCILIATION') from exc
                    if typ != 'OK':
                        raise RuntimeError('NEW_DRAFT_APPEND_FAILED')
                    found = [m.decode() for m in _find(imap, mid)]
                    if len(found) != 1 or _raw(imap, found[0]) != raw:
                        raise RuntimeError('NEW_DRAFT_READBACK_MISMATCH')
                    with lock:
                        result['per_owner'][owner]['created'] += 1
                        done_updates.append((lead['_row'], lid, mid, mail['template_id'],
                                             datetime.now(timezone.utc).isoformat()))
            finally:
                if imap is not None:
                    try:
                        imap.logout()
                    except (imaplib.IMAP4.error, OSError):
                        pass

        errors = []
        if work:
            n_conn = max(1, connections)
            jobs = []
            with ThreadPoolExecutor(max_workers=n_conn * len(work)) as pool:
                for owner, (folder, validity, items) in work.items():
                    for i in range(n_conn):
                        part = items[i::n_conn]
                        if part:
                            jobs.append(pool.submit(append_batch, owner, folder, validity, part))
                errors = [j.exception() for j in jobs if j.exception()]

        # Auch nach einem Fehler: jeden bereits per APPEND bestätigten Entwurf im CRM binden.
        if done_updates:
            done_updates.sort(key=lambda u: u[0])
            result['crm_writes'] = write_crm_draft_bindings(svc, spreadsheet_id, live_headers, done_updates)
        if errors:
            raise RuntimeError(f'FILL_MISSING_DRAFTS_FAILED: {errors[0]}')
    return result
