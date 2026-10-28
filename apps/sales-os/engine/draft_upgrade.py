"""Wiederaufnehmbarer Entwurfsaustausch. Ohne --apply ausschließlich lesend.

Ein dauerhaftes Journal hält Message-ID und Ersatz-MIME vor APPEND fest.
Unklarer APPEND-Ausgang wird niemals automatisch wiederholt. Originale
werden lokal gesichert und per UID MOVE archiviert; es gibt keinen EXPUNGE.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import make_msgid
import base64
import hashlib
import imaplib
import json
import os
from pathlib import Path
import sqlite3
import time

ARCHIVE = 'Entwürfe-Archiv-v1'
REPAIRABLE = {'BODY_NOT_COMPANY_OR_CONTACT_SPECIFIC', 'SUBJECT_NOT_COMPANY_SPECIFIC',
              'UNRESOLVED_PLACEHOLDER', 'FLYER_LINK_MISSING', 'PERSONAL_OPTOUT_LINK_MISSING',
              'HISTORICAL_VARIANT_REQUIRES_REVIEW', 'PLAIN_TEXT_MISSING'}


def modified_utf7(value):
    result = []; pending = []
    def flush():
        if pending:
            raw = ''.join(pending).encode('utf-16-be')
            result.append('&' + base64.b64encode(raw).decode().rstrip('=').replace('/', ',') + '-')
            pending.clear()
    for char in value:
        if ' ' <= char <= '~':
            flush(); result.append('&-' if char == '&' else char)
        else:
            pending.append(char)
    flush()
    return ''.join(result)


def mailbox_arg(value):
    return '"' + modified_utf7(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _select(imap, folder, validity=None, readonly=True):
    typ, _ = imap.select(folder, readonly=readonly)
    got = imap.response('UIDVALIDITY')[1]
    if typ != 'OK' or not got or not got[0]:
        raise RuntimeError('MAILBOX_UIDVALIDITY_MISSING')
    current = got[0].decode() if isinstance(got[0], bytes) else str(got[0])
    if validity is not None and str(validity) != current:
        raise RuntimeError('DRAFT_UIDVALIDITY_CHANGED')
    return current


def _raw(imap, uid):
    typ, data = imap.uid('fetch', str(uid), '(BODY.PEEK[])')
    parts = [x[1] for x in data or [] if isinstance(x, tuple)] if typ == 'OK' else []
    if len(parts) != 1:
        raise RuntimeError('DRAFT_READBACK_FAILED')
    return parts[0]


def _find(imap, mid):
    typ, data = imap.uid('search', None, 'HEADER', 'Message-ID', '"' + mid + '"')
    if typ != 'OK':
        raise RuntimeError('MESSAGE_SEARCH_FAILED')
    return data[0].split() if data and data[0] else []


def upgrade_drafts(owner, limit=5, cohort='pilot', apply=False, journal_path=None, *,
                   records=None, leads=None, client=None, svc=None, mx_check=None, signals=None, lock_client=None):
    """Nur erste v2-Nachricht; Folgekontakte brauchen später das verifizierte Sequenzjournal."""
    from canonical_template_factory import render_email_v2
    from click_sync import click_url
    from hsb_core import check_eligibility, normalize_owner
    from lead_quality import deliverability_flags, fit_score, segment_for
    from outbound_safety import crm_write_lead_readback, require_stable_crm_binding
    from sales_reconciliation import assess_message
    from hsb_config import CANONICAL_SPREADSHEET_ID

    owner = normalize_owner(owner)
    if owner not in ('JOEL', 'JORDI') or type(limit) is not int or not 1 <= limit <= 100 or cohort not in ('pilot', 'all'):
        raise ValueError('INVALID_UPGRADE_SELECTION')
    if records is None or leads is None:
        raise ValueError('FRESH_AUDIT_AND_CRM_REQUIRED')
    result = {'selected': 0, 'appended': 0, 'archived': 0, 'crm_updated': 0,
              'skipped_reasons': Counter(), 'customer_emails_sent': 0, 'dry_run': not apply}
    byid = {}
    for lead in leads:
        byid.setdefault(str(lead.get('Lead-ID') or ''), []).append(lead)
    counts = Counter((r.get('owner'), r.get('lead_id')) for r in records)
    done=set()
    if journal_path and Path(journal_path).is_file():
        prior=sqlite3.connect(Path(journal_path).resolve().as_uri()+'?mode=ro',uri=True)
        try:
            done={r[0] for r in prior.execute("SELECT key FROM upgrades WHERE state='DONE'")}
        finally:
            prior.close()
    cache = {}; selected = []
    # Erst Fit, dann Netzwerkprüfungen: knappe Pilotplätze nicht nach IMAP-Reihenfolge vergeben.
    def rank(record):
        matches = byid.get(str(record.get('lead_id')), [])
        if len(matches) != 1:
            return -1
        return fit_score(matches[0], (signals or {}).get(record.get('lead_id')))[0]
    quotas = {'produktion': limit - round(limit * .2), 'architekten': round(limit * .2)}
    chosen = Counter()
    for record in sorted(records, key=rank, reverse=True):
        if record.get('owner') != owner or record.get('internal_test'):
            continue
        record_key='|'.join(str(record.get(k,'')) for k in ('owner','uidvalidity','uid','sha256'))
        if record_key in done:
            result['skipped_reasons']['ALREADY_DONE']+=1
            continue
        matches = byid.get(str(record.get('lead_id')), [])
        reason = None
        if len(matches) != 1 or counts[(owner, record.get('lead_id'))] != 1:
            reason = 'AMBIGUOUS_LEAD_OR_DRAFT'
        elif set(record.get('issues', [])) - REPAIRABLE:
            reason = 'IDENTITY_OR_HISTORY_ISSUE'
        else:
            lead = dict(matches[0])
            if str(lead.get('Email_Template_ID') or '').startswith('v2-'):
                result['skipped_reasons']['ALREADY_V2'] += 1
                continue
            if str(lead.get('Tier') or '').strip().upper()=='Z':
                result['skipped_reasons']['TIER_Z']+=1
                continue
            segment = segment_for(lead)
            if cohort == 'pilot' and chosen[segment] >= quotas[segment]:
                result['skipped_reasons']['PILOT_SEGMENT_QUOTA'] += 1
                continue
            lead['Deliverability_Flags'] = deliverability_flags(lead, cache, set(), mx_check=mx_check)
            _, tier, _ = fit_score(lead, (signals or {}).get(lead.get('Lead-ID')))
            if tier == 'Z' or not check_eligibility(lead).eligible:
                reason = 'INELIGIBLE_OR_TIER_Z'
        if reason:
            result['skipped_reasons'][reason] += 1
            continue
        selected.append((record, lead))
        chosen[segment_for(lead)] += 1
        if len(selected) >= limit:
            break
    result['selected'] = len(selected)
    result['selected_lead_ids'] = [str(lead.get('Lead-ID') or '') for _, lead in selected]
    if not apply:
        return result
    if client is None or svc is None or journal_path is None:
        raise ValueError('APPLY_REQUIRES_CLIENT_CRM_AND_JOURNAL')
    if os.environ.get('HSB_CRM_BINDINGS_VERIFIED') != 'yes':
        raise RuntimeError('CRM_STABLE_BINDING_CANARY_REQUIRED')
    # Prüfung vor dem ersten externen Schreibzugriff.
    if any(not l.get('_row') for _, l in selected):
        raise ValueError('CRM_ROW_MISSING')
    from outbound_safety import mailbox_dispatch_lock
    if lock_client is None:
        from com_mailbox_manager import ComMailboxClient
        lock_client = ComMailboxClient('JOEL')
    # Derselbe JOEL-Lock wie im Versand; schützt beide Postfächer und alle Geräte.
    with mailbox_dispatch_lock(lock_client):
        journal_path = Path(journal_path)
        journal_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(journal_path, isolation_level=None)
        journal_path.chmod(0o600)
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS upgrades(key TEXT PRIMARY KEY, mid TEXT, raw BLOB, state TEXT, old_raw BLOB)')
        try:
            with client._get_imap() as imap:
                for rec, lead in selected:
                    current_rows = svc.spreadsheets().values().get(spreadsheetId=CANONICAL_SPREADSHEET_ID,
                        range='ALL_LEADS!A1:BU6425').execute().get('values', [])
                    current_matches = [(idx, dict(zip(current_rows[0], r))) for idx, r in enumerate(current_rows[1:], 2)
                        if r and r[0] == lead['Lead-ID']]
                    if len(current_matches) != 1:
                        raise RuntimeError('LIVE_LEAD_NOT_UNIQUE')
                    current_row, current = current_matches[0]
                    current['Deliverability_Flags'] = deliverability_flags(current, {}, set(), mx_check=mx_check)
                    if str(current.get('Tier') or '').strip().upper() == 'Z' or not check_eligibility(current).eligible or normalize_owner(current.get('Verantwortlicher')) != owner:
                        raise RuntimeError('LIVE_LEAD_GATE_BLOCKED')
                    if current.get('E-Mail') != lead.get('E-Mail'):
                        raise RuntimeError('LIVE_RECIPIENT_CHANGED')
                    lead = dict(current, _row=current_row)
                    # Vor APPEND/MOVE die stabile CRM-Bindung prüfen, nicht erst nach dem Archivieren.
                    require_stable_crm_binding(svc,CANONICAL_SPREADSHEET_ID,lead['Lead-ID'])
                    key = '|'.join(str(rec[k]) for k in ('owner', 'uidvalidity', 'uid', 'sha256'))
                    _select(imap, rec['folder'], rec['uidvalidity'])
                    row = db.execute('SELECT mid,raw,state,old_raw FROM upgrades WHERE key=?', (key,)).fetchone()
                    if row and row[2] == 'DONE':
                        continue
                    old = row[3] if row and row[2] in ('MOVE_UNKNOWN', 'ARCHIVED') else _raw(imap, rec['uid'])
                    if hashlib.sha256(old).hexdigest() != rec['sha256']:
                        result['skipped_reasons']['CHANGED_V1_HASH'] += 1
                        continue
                    row = db.execute('SELECT mid,raw,state,old_raw FROM upgrades WHERE key=?', (key,)).fetchone()
                    if row is None:
                        rendered = render_email_v2(lead, owner, click_url=click_url(lead['Lead-ID'], segment_for(lead), os.environ.get('HSB_CLICK_SECRET')))
                        mid = make_msgid(domain='hsb-boden.com')
                        raw, _ = client.build_draft_message(rendered['to_email'], rendered['subject'], body_text=rendered['body_text'],
                                template_id=rendered['template_id'], lead_id=lead['Lead-ID'], custom_message_id=mid)
                        # imaplib.append normalisiert CRLF; Readback und Journal speichern dieselben Bytes.
                        raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n').replace(b'\n', b'\r\n')
                        if assess_message(raw, owner, [lead])['issues']:
                            raise RuntimeError('V2_REVALIDATION_FAILED')
                        db.execute('INSERT INTO upgrades VALUES(?,?,?,?,?)', (key, mid, raw, 'PREPARED', old))
                        row = (mid, raw, 'PREPARED', old)
                    mid, raw, state, saved_old = row
                    if saved_old != old:
                        raise RuntimeError('ORIGINAL_BACKUP_MISMATCH')
                    if state == 'DONE':
                        continue
                    matches = _find(imap, mid)
                    if len(matches) > 1:
                        raise RuntimeError('REPLACEMENT_NOT_UNIQUE')
                    if not matches:
                        if state != 'PREPARED':
                            raise RuntimeError('UNCERTAIN_APPEND_REQUIRES_RECONCILIATION')
                        db.execute("UPDATE upgrades SET state='APPEND_UNKNOWN' WHERE key=?", (key,))
                        typ, _ = imap.append(rec['folder'], r'(\Draft)', imaplib.Time2Internaldate(time.time()), raw)
                        if typ != 'OK':
                            raise RuntimeError('REPLACEMENT_APPEND_FAILED')
                        result['appended'] += 1
                        matches = _find(imap, mid)
                    if len(matches) != 1 or _raw(imap, matches[0].decode()) != raw:
                        raise RuntimeError('REPLACEMENT_READBACK_MISMATCH')
                    archive = mailbox_arg(ARCHIVE)
                    typ, _ = imap.select(archive, readonly=True)
                    if typ != 'OK':
                        typ, _ = imap.create(archive)
                        if typ != 'OK':
                            raise RuntimeError('ARCHIVE_CREATE_FAILED')
                        _select(imap, archive)
                    original_mid = str(BytesParser(policy=policy.default).parsebytes(old).get('Message-ID') or '')
                    if not original_mid:
                        raise RuntimeError('ORIGINAL_MESSAGE_ID_MISSING')
                    archived = _find(imap, original_mid)
                    if not archived:
                        capabilities = {x.decode().upper() if isinstance(x, bytes) else str(x).upper() for x in imap.capabilities}
                        if 'MOVE' not in capabilities:
                            raise RuntimeError('UID_MOVE_REQUIRED_ORIGINAL_RETAINED')
                        if state in ('MOVE_UNKNOWN', 'ARCHIVED'):
                            raise RuntimeError('UNCERTAIN_MOVE_REQUIRES_RECONCILIATION')
                        _select(imap, rec['folder'], rec['uidvalidity'], readonly=False)
                        # Vor MOVE noch einmal gegen das gesicherte Original vergleichen.
                        if _raw(imap, rec['uid']) != old:
                            raise RuntimeError('ORIGINAL_CHANGED_BEFORE_MOVE')
                        db.execute("UPDATE upgrades SET state='MOVE_UNKNOWN' WHERE key=?", (key,))
                        typ, _ = imap.uid('MOVE', rec['uid'], archive)
                        if typ != 'OK':
                            raise RuntimeError('ARCHIVE_MOVE_FAILED')
                        _select(imap, archive)
                        archived = _find(imap, original_mid)
                    if len(archived) != 1 or _raw(imap, archived[0].decode()) != old:
                        raise RuntimeError('ARCHIVE_READBACK_MISMATCH')
                    result['archived'] += 1
                    db.execute("UPDATE upgrades SET state='ARCHIVED' WHERE key=?", (key,))
                    _select(imap, rec['folder'], rec['uidvalidity'])
                    if _find(imap, original_mid):
                        raise RuntimeError('ORIGINAL_STILL_IN_DRAFTS')
                    # Spaltenreihenfolge immer vom aktuellen CRM-Header, nicht aus einem veränderten dict.
                    headers = svc.spreadsheets().values().get(spreadsheetId=CANONICAL_SPREADSHEET_ID,
                        range='ALL_LEADS!A1:BU1').execute()['values'][0]
                    crm_write_lead_readback(svc, CANONICAL_SPREADSHEET_ID, lead['Lead-ID'],
                        {'Draft_ID': mid, 'Email_Template_ID': rendered_id(raw), 'Drafted_At': datetime.now(timezone.utc).isoformat()})
                    result['crm_updated'] += 1
                    db.execute("UPDATE upgrades SET state='DONE' WHERE key=?", (key,))
        finally:
            db.close()
        result['originals_retained'] = True
        return result


def rendered_id(raw):
    return str(BytesParser(policy=policy.default).parsebytes(raw)['X-HSB-Template-ID'])
