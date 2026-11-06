"""Schneller Austausch veralteter Erstkontakte in place (gleiche Message-ID). Ohne --apply nur lesend.

Empfänger und Message-ID bleiben gleich; das CRM bindet den Entwurf über Draft_ID = Message-ID. Ändert sich die
Vorlage (v2-<segment>-s1 -> v2-<segment>-reparatur-s1), wird nur Email_Template_ID in Sammelaufrufen mit
Identitätsprüfung und Readback nachgezogen. Beide Postfächer parallel mit mehreren IMAP-Verbindungen.

Ablauf je Entwurf: Original lesen und Hash prüfen -> Ersatz mit derselben Message-ID rendern und prüfen ->
APPEND -> Ersatz zurücklesen -> Original per UID MOVE ins Archiv (kein EXPUNGE). Ein Abbruch zwischen APPEND
und MOVE hinterlässt zwei Entwürfe mit derselben Message-ID; der nächste Lauf erkennt das und verschiebt nur
das Original. Die Versandsperre wird während des gesamten Austauschs gehalten.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesParser
import hashlib
import imaplib
import threading
import time

from draft_upgrade import ARCHIVE, _find, _raw, _select, mailbox_arg
from sales_reconciliation import OUTDATED_PLANNER_COPY, OUTDATED_REPAIR_COPY

# Nur veraltete Fassungen derselben Vorlage: gleicher Lead, gleiche Vorlage, neuer Text bzw. neue Gestaltung.
REFRESHABLE = {OUTDATED_REPAIR_COPY, OUTDATED_PLANNER_COPY}
DEEP_DEFECT_CAP = 50

CONNECTIONS_PER_MAILBOX = 3
IMAP_RETRIES = 3


def _crlf(raw):
    return raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n').replace(b'\n', b'\r\n')


def select_candidates(owner, records, leads, planner_outreach_allowed=None, check_eligibility=None, *,
                      deep_defects=frozenset(), allow_mass_refresh=False):
    """Erstkontakte, die das CRM über Draft_ID exakt bindet und die in place auf die aktuelle Reparatur-Fassung
    gebracht werden können: veraltete Reparatur-Fassung, veralteter Planer-Text, die ältere Vorlage
    v2-<segment>-s1 desselben Segments oder ein vom Tiefenprüfer gemeldeter Mangel (gedeckelt auf 50 je Postfach).
    Ein bereits aktueller Entwurf mit veralteter Vorlage im CRM wird nur im CRM nachgezogen (mailbox=False).
    Rückgabe: [(rec, lead, mailbox)], Überspringgründe."""
    if planner_outreach_allowed is None:
        from lead_quality import planner_outreach_allowed
    if check_eligibility is None:
        from hsb_core import check_eligibility
    from lead_quality import segment_for
    deep_defects = frozenset(deep_defects or ())
    owner_deep = {k for k in deep_defects if k.startswith(f'{owner}|')}
    if len(owner_deep) > DEEP_DEFECT_CAP and not allow_mass_refresh:
        raise RuntimeError('DEEP_DEFECT_CAP_EXCEEDED')
    byid = {}
    for lead in leads:
        byid.setdefault(str(lead.get('Lead-ID') or ''), []).append(lead)
    mids = Counter(r.get('message_id') for r in records if r.get('owner') == owner)
    chosen, skipped = [], Counter()
    for rec in records:
        if rec.get('owner') != owner or rec.get('internal_test'):
            continue
        issues = set(rec.get('issues') or [])
        rec_key = '|'.join(str(rec.get(k, '')) for k in ('owner', 'uidvalidity', 'uid', 'sha256'))
        is_deep = rec_key in deep_defects
        matches = byid.get(str(rec.get('lead_id') or ''), [])
        tmpl = str(rec.get('template_id') or '')
        if not (issues & REFRESHABLE) and not is_deep:
            # Nur CRM nachziehen: Entwurf aktuell und fehlerfrei, CRM nennt noch die alte Vorlage.
            if (not issues and len(matches) == 1 and mids[rec.get('message_id')] == 1
                    and tmpl.startswith('v2-') and tmpl.endswith('-reparatur-s1')
                    and matches[0].get('Draft_ID') == rec.get('message_id')
                    and str(matches[0].get('Email_Template_ID') or '') != tmpl
                    and tmpl == f"v2-{segment_for(matches[0])}-reparatur-s1"):
                chosen.append((rec, dict(matches[0]), False))
            continue
        target = f"v2-{segment_for(matches[0])}-reparatur-s1" if len(matches) == 1 else ''
        if issues - REFRESHABLE:
            skipped['OTHER_ISSUES'] += 1
        elif len(matches) != 1 or mids[rec.get('message_id')] != 1:
            skipped['AMBIGUOUS_LEAD_OR_DRAFT'] += 1
        elif not (tmpl.startswith('v2-') and tmpl.endswith('-s1')):
            skipped['NOT_FIRST_CONTACT'] += 1
        elif tmpl not in (target, target.replace('-reparatur-s1', '-s1')):
            skipped['SEGMENT_CHANGED'] += 1
        elif matches[0].get('Draft_ID') != rec.get('message_id'):
            skipped['CRM_BINDING_DIFFERS'] += 1
        elif segment_for(matches[0]) == 'architekten' and not planner_outreach_allowed(matches[0]):
            skipped['PLANNING_PROJECT_UNVERIFIED'] += 1
        elif str(matches[0].get('Tier') or '').strip().upper() == 'Z' or not check_eligibility(matches[0]).eligible:
            skipped['INELIGIBLE'] += 1
        else:
            chosen.append((rec, dict(matches[0]), True))
    return chosen, skipped


def _col_letter(index):
    letters = ''
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def write_crm_templates(svc, spreadsheet_id, headers, updates, chunk=100):
    """Setzt Email_Template_ID für bereits erneuerte Entwürfe. Je Block: Zeilenidentität live lesen, schreiben,
    zurücklesen. chunk=100 hält die batchGet-URL sicher unter Googles 16-KB-Limit. updates: [(row, lead_id, template)]."""
    if not updates:
        return 0
    col = _col_letter(headers.index('Email_Template_ID'))
    api = svc.spreadsheets().values()

    def read(rows):
        ranges = [f'ALL_LEADS!A{r}' for r in rows] + [f'ALL_LEADS!{col}{r}' for r in rows]
        got = api.batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute().get('valueRanges', [])
        vals = [((g.get('values') or [['']])[0] or [''])[0] for g in got]
        return vals[:len(rows)], vals[len(rows):]

    written = 0
    for i in range(0, len(updates), chunk):
        part = updates[i:i + chunk]
        rows = [r for r, _, _ in part]
        ids, _ = read(rows)
        if ids != [lid for _, lid, _ in part]:
            raise RuntimeError('CRM_ROW_IDENTITY_CHANGED')
        api.batchUpdate(spreadsheetId=spreadsheet_id, body={'valueInputOption': 'RAW', 'data': [
            {'range': f'ALL_LEADS!{col}{r}', 'values': [[t]]} for r, _, t in part]}).execute()
        ids, tmpls = read(rows)
        if ids != [lid for _, lid, _ in part] or tmpls != [t for _, _, t in part]:
            raise RuntimeError('CRM_READBACK_MISMATCH')
        written += len(part)
    return written


def build_replacement(client, owner, lead, mid):
    from canonical_template_factory import render_email_v2
    r = render_email_v2(lead, owner, step=1, variant='reparatur')
    raw, _ = client.build_draft_message(r['to_email'], r['subject'], body_text=r['body_text'],
                                        body_html=r['body_html'], template_id=r['template_id'],
                                        lead_id=lead['Lead-ID'], custom_message_id=mid, copy_rev=r['copy_rev'])
    return _crlf(raw), r['template_id']


def refresh_one(imap, client, owner, rec, lead, assess_message):
    """Gibt 'REFRESHED', 'RECOVERED' oder einen Überspringgrund zurück. Wirft bei unklarem Zustand."""
    from lead_quality import segment_for
    target = f"v2-{segment_for(lead)}-reparatur-s1"
    mid = rec['message_id']
    matches = [m.decode() for m in _find(imap, mid)]
    orig_uid = str(rec['uid'])
    others = [u for u in matches if u != orig_uid]
    if orig_uid not in matches:
        return 'ORIGINAL_GONE'
    old = _raw(imap, orig_uid)
    if hashlib.sha256(old).hexdigest() != rec['sha256']:
        return 'CHANGED_ORIGINAL_HASH'
    if len(others) > 1:
        raise RuntimeError('REPLACEMENT_NOT_UNIQUE')
    recovered = False
    if others:
        # Abbruch nach APPEND: der vorhandene Zwilling muss ein gültiger, aktueller Ersatz sein.
        new_uid = others[0]
        new_raw = _raw(imap, new_uid)
        if assess_message(new_raw, owner, [lead])['issues']:
            raise RuntimeError('TWIN_DRAFT_INVALID')
        recovered = True
    else:
        new_raw, template_id = build_replacement(client, owner, lead, mid)
        if template_id != target:
            return 'TEMPLATE_CHANGED'
        if assess_message(new_raw, owner, [lead])['issues']:
            raise RuntimeError('REPLACEMENT_REVALIDATION_FAILED')
        try:
            typ, _ = imap.append(rec['folder'], r'(\Draft)', imaplib.Time2Internaldate(time.time()), new_raw)
        except (imaplib.IMAP4.abort, OSError) as exc:
            # The server may have accepted the literal even when its response was lost.
            # Do not enter the reconnect loop with permission to APPEND again.
            raise RuntimeError('UNCERTAIN_APPEND_REQUIRES_RECONCILIATION') from exc
        if typ != 'OK':
            raise RuntimeError('REPLACEMENT_APPEND_FAILED')
        found = [m.decode() for m in _find(imap, mid) if m.decode() != orig_uid]
        if len(found) != 1 or _raw(imap, found[0]) != new_raw:
            raise RuntimeError('REPLACEMENT_READBACK_MISMATCH')
    try:
        typ, _ = imap.uid('move', orig_uid, mailbox_arg(ARCHIVE))
    except (imaplib.IMAP4.abort, OSError) as exc:
        raise RuntimeError('UNCERTAIN_MOVE_REQUIRES_RECONCILIATION') from exc
    if typ != 'OK':
        raise RuntimeError('ORIGINAL_MOVE_FAILED')
    return 'RECOVERED' if recovered else 'REFRESHED'


def _worker(make_client, owner, folder, validity, batch, assess_message, result, lock, done):
    client = make_client()
    imap = None
    for rec, lead in batch:
        for attempt in range(IMAP_RETRIES):
            try:
                if imap is None:
                    imap = client._get_imap()
                    _select(imap, folder, validity, readonly=False)
                outcome = refresh_one(imap, client, owner, rec, lead, assess_message)
                break
            except (imaplib.IMAP4.abort, OSError):
                imap = None
                if attempt == IMAP_RETRIES - 1:
                    raise
        with lock:
            result['outcomes'][outcome] += 1
            if outcome in ('REFRESHED', 'RECOVERED'):
                done.append(lead)
    if imap is not None:
        try:
            imap.logout()
        except (imaplib.IMAP4.error, OSError):
            pass


def refresh_signatures(owners, records, leads, apply=False, *, make_client=None, lock_client=None,
                       assess_message=None, connections=CONNECTIONS_PER_MAILBOX, svc=None, spreadsheet_id=None,
                       headers=None, deep_defects=frozenset(), allow_mass_refresh=False):
    from lead_quality import segment_for
    if assess_message is None:
        from sales_reconciliation import assess_message
    if make_client is None:
        from com_mailbox_manager import ComMailboxClient
        make_client = ComMailboxClient
    result = {'dry_run': not apply, 'customer_emails_sent': 0, 'crm_writes': 0, 'per_owner': {}}
    plan, crm_only = {}, {}
    for owner in owners:
        chosen, skipped = select_candidates(owner, records, leads, deep_defects=deep_defects,
                                            allow_mass_refresh=allow_mass_refresh)
        plan[owner] = [(r, l) for r, l, mailbox in chosen if mailbox]
        crm_only[owner] = [l for _, l, mailbox in chosen if not mailbox]
        result['per_owner'][owner] = {'selected': len(plan[owner]), 'crm_only': len(crm_only[owner]),
                                      'skipped': dict(skipped)}
    if not apply or not (any(plan.values()) or any(crm_only.values())):
        return result
    needs_crm = any(crm_only.values()) or any(
        str(l.get('Email_Template_ID') or '') != f"v2-{segment_for(l)}-reparatur-s1"
        for chosen in plan.values() for _, l in chosen)
    if needs_crm and (svc is None or spreadsheet_id is None or not headers):
        raise ValueError('CRM_SERVICE_REQUIRED_FOR_TEMPLATE_UPDATE')
    for owner, chosen in plan.items():
        if len({(r['folder'], str(r['uidvalidity'])) for r, _ in chosen}) > 1:
            raise RuntimeError('MULTIPLE_DRAFT_FOLDERS')
    from outbound_safety import mailbox_dispatch_lock
    if lock_client is None:
        lock_client = make_client('JOEL')
    done = {owner: list(crm_only[owner]) for owner in plan}
    errors = []
    with mailbox_dispatch_lock(lock_client, release_on_error=True):
        for owner, chosen in plan.items():
            if not chosen:
                continue
            imap = make_client(owner)._get_imap()
            try:
                typ, _ = imap.select(mailbox_arg(ARCHIVE), readonly=True)
                if typ != 'OK' and imap.create(mailbox_arg(ARCHIVE))[0] != 'OK':
                    raise RuntimeError('ARCHIVE_CREATE_FAILED')
                caps = {c.decode().upper() if isinstance(c, bytes) else str(c).upper() for c in imap.capabilities}
                if 'MOVE' not in caps:
                    raise RuntimeError('UID_MOVE_REQUIRED')
            finally:
                imap.logout()
        lock = threading.Lock()
        jobs = []
        with ThreadPoolExecutor(max_workers=max(1, connections) * len(plan)) as pool:
            for owner, chosen in plan.items():
                if not chosen:
                    continue
                stats = result['per_owner'][owner]
                stats['outcomes'] = Counter()
                folder, validity = chosen[0][0]['folder'], str(chosen[0][0]['uidvalidity'])
                for i in range(max(1, connections)):
                    batch = chosen[i::max(1, connections)]
                    if batch:
                        jobs.append(pool.submit(_worker, lambda o=owner: make_client(o), owner, folder, validity,
                                                batch, assess_message, stats, lock, done[owner]))
            errors = [j.exception() for j in jobs if j.exception()]
        for owner in plan:
            out = result['per_owner'][owner].get('outcomes')
            if out is not None:
                result['per_owner'][owner]['outcomes'] = dict(out)
        # Auch nach einem Fehler: für jeden schon erneuerten Entwurf die Vorlage im CRM nachziehen.
        updates = []
        for owner in plan:
            for lead in done[owner]:
                target = f"v2-{segment_for(lead)}-reparatur-s1"
                if str(lead.get('Email_Template_ID') or '') != target:
                    updates.append((lead['_row'], lead['Lead-ID'], target))
        if updates:
            result['crm_writes'] = write_crm_templates(svc, spreadsheet_id, headers, updates)
        if errors:
            raise RuntimeError(f'SIGNATURE_REFRESH_FAILED: {errors[0]}')
    return result
