"""Doppelte .com-Entwürfe bereinigen. Ohne --apply ausschließlich lesend.

Grundlage ist ein frischer Audit-Snapshot von sales_reconciliation.py (drafts.json,
crm-original.json). Pro Empfänger bleibt genau ein Entwurf im Entwurfsordner; jede
weitere Kopie wird per UID MOVE nach 'Entwürfe-Archiv-v1' verschoben. Es gibt kein
DELETE und kein EXPUNGE, die Originale liegen zusätzlich als .eml im Audit-Ordner.

Geschützt und unberührt bleiben alle Gruppen, deren Empfänger bereits kontaktiert ist
(.de-Forensik, .com-Gesendet, CRM-Versandstatus), deren Domain bereits angeschrieben
wurde, die eine Antwort/Abmeldung offen haben oder deren CRM-Zuordnung nicht eindeutig ist.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import sqlite3
from pathlib import Path

from draft_upgrade import ARCHIVE, _find, _raw, _select, mailbox_arg
from hsb_core import normalize_owner

# Diese Befunde sperren eine Empfängergruppe vollständig gegen jede Änderung.
PROTECTED_ISSUES = frozenset({'ALREADY_CONTACTED', 'ALREADY_CONTACTED_DOMAIN', 'INBOUND_REQUIRES_REVIEW',
                              'CRM_RECIPIENT_AMBIGUOUS', 'CRM_LEAD_ID_AMBIGUOUS', 'LEAD_ID_CONFLICT'})


def _is_current(record):
    return '-reparatur-' in str(record.get('template_id') or '') and 'OUTDATED_REPAIR_COPY' not in record.get('issues', [])


def plan_dedupe(records, leads):
    """Liefert für jede Empfängergruppe mit mehr als einem Entwurf: behalten / archivieren / geschützt."""
    by_email = defaultdict(list)
    for lead in leads:
        by_email[str(lead.get('E-Mail') or lead.get('Email') or '').strip().lower()].append(lead)
    groups = defaultdict(list)
    for rec in records:
        if rec.get('internal_test') or len(rec.get('recipients') or []) != 1:
            continue
        groups[rec['recipients'][0]].append(rec)
    plan = {'keep': [], 'archive': [], 'protected_groups': [], 'ambiguous_groups': [],
            'groups_with_duplicates': 0, 'reasons': Counter()}
    for email, recs in sorted(groups.items()):
        if len(recs) < 2:
            continue
        plan['groups_with_duplicates'] += 1
        issues = {i for r in recs for i in r.get('issues', [])}
        if issues & PROTECTED_ISSUES:
            plan['protected_groups'].append(email)
            plan['reasons']['PROTECTED_' + sorted(issues & PROTECTED_ISSUES)[0]] += 1
            continue
        matches = by_email.get(email, [])
        if len(matches) != 1:
            plan['ambiguous_groups'].append(email)
            plan['reasons']['CRM_NOT_UNIQUE'] += 1
            continue
        lead = matches[0]
        owner = normalize_owner(lead.get('Verantwortlicher') or lead.get('Owner'))
        own = [r for r in recs if r.get('owner') == owner]
        if not own:
            plan['ambiguous_groups'].append(email)
            plan['reasons']['NO_DRAFT_IN_CRM_OWNER_MAILBOX'] += 1
            continue
        bound = [r for r in own if r.get('message_id') and r.get('message_id') == lead.get('Draft_ID')]
        if len(bound) == 1:
            keeper = bound[0]
            plan['reasons']['KEEP_CRM_BOUND'] += 1
        else:
            # Ohne CRM-Bindung: aktuelle Reparatur-Fassung vor älteren Fassungen, dann die jüngste UID.
            keeper = max(own, key=lambda r: (_is_current(r), int(r.get('uid') or 0)))
            plan['reasons']['KEEP_NEWEST' if not _is_current(keeper) else 'KEEP_CURRENT_COPY'] += 1
        plan['keep'].append(keeper)
        plan['archive'].extend(r for r in recs if r is not keeper)
    plan['archive_count'] = len(plan['archive'])
    plan['archive_by_owner'] = dict(Counter(r['owner'] for r in plan['archive']))
    return plan


def apply_dedupe(plan, clients, journal_path):
    """Verschiebt die Dubletten. Jeder Schritt wird gegen den Audit-Hash geprüft und im Journal festgehalten."""
    journal_path = Path(journal_path)
    journal_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(journal_path, isolation_level=None)
    journal_path.chmod(0o600)
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS dedupe(key TEXT PRIMARY KEY, mid TEXT, state TEXT)')
    result = {'archived': 0, 'skipped': Counter(), 'customer_emails_sent': 0}
    by_owner = defaultdict(list)
    for rec in plan['archive']:
        by_owner[rec['owner']].append(rec)
    try:
        for owner, recs in by_owner.items():
            with clients[owner]._get_imap() as imap:
                archive = mailbox_arg(ARCHIVE)
                typ, _ = imap.select(archive, readonly=True)
                if typ != 'OK':
                    typ, _ = imap.create(archive)
                    if typ != 'OK':
                        raise RuntimeError('ARCHIVE_CREATE_FAILED')
                capabilities = {x.decode().upper() if isinstance(x, bytes) else str(x).upper() for x in imap.capabilities}
                if 'MOVE' not in capabilities:
                    raise RuntimeError('UID_MOVE_REQUIRED_ORIGINAL_RETAINED')
                for rec in recs:
                    key = '|'.join(str(rec[k]) for k in ('owner', 'uidvalidity', 'uid', 'sha256'))
                    row = db.execute('SELECT state FROM dedupe WHERE key=?', (key,)).fetchone()
                    if row and row[0] == 'DONE':
                        result['skipped']['ALREADY_DONE'] += 1
                        continue
                    if row and row[0] == 'MOVE_UNKNOWN':
                        raise RuntimeError('UNCERTAIN_MOVE_REQUIRES_RECONCILIATION')
                    _select(imap, rec['folder'], rec['uidvalidity'], readonly=False)
                    try:
                        raw = _raw(imap, rec['uid'])
                    except RuntimeError:
                        result['skipped']['DRAFT_GONE'] += 1
                        continue
                    if hashlib.sha256(raw).hexdigest() != rec['sha256']:
                        result['skipped']['CHANGED_SINCE_AUDIT'] += 1
                        continue
                    mid = rec.get('message_id') or ''
                    if not mid:
                        result['skipped']['MESSAGE_ID_MISSING'] += 1
                        continue
                    db.execute('INSERT OR REPLACE INTO dedupe VALUES(?,?,?)', (key, mid, 'MOVE_UNKNOWN'))
                    typ, _ = imap.uid('MOVE', rec['uid'], archive)
                    if typ != 'OK':
                        raise RuntimeError('ARCHIVE_MOVE_FAILED')
                    _select(imap, archive)
                    if not any(_raw(imap, u.decode()) == raw for u in _find(imap, mid)):
                        raise RuntimeError('ARCHIVE_READBACK_MISMATCH')
                    db.execute("UPDATE dedupe SET state='DONE' WHERE key=?", (key,))
                    result['archived'] += 1
    finally:
        db.close()
    result['originals_retained'] = True
    return result
