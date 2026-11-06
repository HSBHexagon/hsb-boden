"""'Entwürfe-Archiv-v1' und nicht endgültige Entwürfe leeren (Owner-Entscheidung 06.11.2026). Ohne --apply nur lesend.

Gelöscht heißt hier wie in graph_aufraeumen.py: per UID MOVE in den Server-Papierkorb des jeweiligen Postfachs.
Es gibt kein STORE, DELETE oder EXPUNGE; endgültig weg ist erst, was der Papierkorb selbst leert. Der Archivname
ist fest. Aus dem Entwurfsordner geht nur, was die Tiefenprüfung nicht als OK einstuft und einem CRM-Lead gehört;
Gesendet und Eingang werden nie berührt. Ausgegeben werden nur Zahlen, Codes und Ordnernamen.
"""
from __future__ import annotations

from collections import Counter
from email import policy
from email.parser import BytesParser
import hashlib
from pathlib import Path
import re

from draft_upgrade import ARCHIVE, mailbox_arg, modified_utf7
from sales_reconciliation import SENDERS, addresses

FIELDS = 'MESSAGE-ID FROM TO X-HSB-LEAD-ID'
FETCH_CHUNK = 500
# Der Socket-Timeout liegt bei 25 s; Moves sind teurer als Lesen.
MOVE_CHUNK = 200
# Nur falls der Server keinen \Trash-Marker liefert; Treffer müssen eindeutig sein.
TRASH_NAMES = {'trash', 'papierkorb', 'deleted', 'deleted items', 'deleted messages', 'gel&apy-schte elemente'}
# Schutz gegen einen Fehlalarm der Prüfung: Mehr als dieser Anteil je Postfach wird nicht bewegt.
MAX_NONFINAL_SHARE = 0.10
_LIST_LINE = re.compile(r'^\((?P<flags>[^)]*)\) (?:"[^"]*"|NIL) (?P<name>.+)$')


def _is_trash_name(name):
    """Nur oberste Ebene oder INBOX.<Name>; ein Unterordner 'Kunden.Mueller.Trash' ist kein Papierkorb."""
    parts = re.split(r'[./]', name.lower())
    return parts[-1] in TRASH_NAMES and (len(parts) == 1 or (len(parts) == 2 and parts[0] == 'inbox'))


def find_trash(imap, cfg):
    """Papierkorb per \\Trash-Marker bestimmen, sonst eindeutig per Name. Ohne Treffer wird nichts bewegt."""
    typ, lines = imap.list()
    if typ != 'OK':
        raise RuntimeError('TRASH_LIST_FAILED')
    forbidden = {modified_utf7(ARCHIVE).lower()}
    # Die Konfiguration führt Ordner in Anführungszeichen, LIST-Namen sind hier schon ohne.
    forbidden |= {str(cfg.get(k) or '').strip().strip('"').lower() for k in ('drafts_folder', 'sent_folder', 'inbox_folder')}
    flagged, named = [], []
    for line in lines or []:
        if not isinstance(line, bytes):
            continue
        match = _LIST_LINE.match(line.decode('ascii', 'replace'))
        if not match:
            continue
        name = match['name'].strip().strip('"')
        if name.lower() in forbidden or '\\noselect' in match['flags'].lower():
            continue
        if '\\trash' in match['flags'].lower():
            flagged.append(name)
        elif _is_trash_name(name):
            named.append(name)
    hits = flagged or named
    if not hits:
        raise RuntimeError('TRASH_NOT_FOUND')
    if len(hits) > 1:
        raise RuntimeError('TRASH_AMBIGUOUS')
    return hits[0]


def _validity(imap):
    data = imap.response('UIDVALIDITY')[1]
    if not data or not data[0]:
        raise RuntimeError('MAILBOX_UIDVALIDITY_MISSING')
    return data[0].decode() if isinstance(data[0], bytes) else str(data[0])


def _select(imap, folder, readonly=True):
    """Liefert False, wenn der Ordner nicht existiert."""
    return imap.select(folder, readonly=readonly)[0] == 'OK'


def _uids(imap):
    typ, data = imap.uid('SEARCH', None, 'ALL')
    if typ != 'OK' or len(data or []) != 1 or not isinstance(data[0], bytes):
        raise RuntimeError('ARCHIVE_SEARCH_FAILED')
    return [u.decode() for u in data[0].split()]


def _headers(imap, uids):
    """Kopfzeilen der aktuell gewählten Ablage; bricht bei unvollständiger Antwort ab."""
    records = {}
    for start in range(0, len(uids), FETCH_CHUNK):
        chunk = uids[start:start + FETCH_CHUNK]
        typ, data = imap.uid('FETCH', ','.join(chunk), f'(UID BODY.PEEK[HEADER.FIELDS ({FIELDS})])')
        if typ != 'OK':
            raise RuntimeError('ARCHIVE_FETCH_FAILED')
        for item in data or []:
            if not isinstance(item, tuple):
                continue
            match = re.search(rb'\bUID (\d+)\b', item[0])
            if not match:
                raise RuntimeError('ARCHIVE_FETCH_FAILED')
            msg = BytesParser(policy=policy.default).parsebytes(item[1])
            records[match[1].decode()] = {
                'mid': str(msg.get('Message-ID') or '').strip(),
                'lead': str(msg.get('X-HSB-Lead-ID') or '').strip(),
                'to': addresses(msg.get('To')),
                'from': addresses(msg.get('From')),
            }
        if not set(chunk) <= set(records):
            raise RuntimeError('ARCHIVE_FETCH_INCOMPLETE')
    return records


def _survey(imap, cfg, owner, archive):
    """Manifest in Zahlen: was liegt im Archiv und wofür gäbe es keinen aktuellen Entwurf mehr?"""
    report = {'archive_total': 0, 'unique_message_ids': 0, 'without_lead_id': 0, 'foreign_sender': 0, 'only_copy': 0}
    if not _select(imap, archive):
        return report, []
    uids = _uids(imap)
    records = _headers(imap, uids)
    if not _select(imap, cfg['drafts_folder']):
        raise RuntimeError('DRAFTS_FOLDER_UNAVAILABLE')
    drafts = _headers(imap, _uids(imap)).values()
    mids = {d['mid'] for d in drafts if d['mid']}
    leads = {d['lead'] for d in drafts if d['lead']}
    recipients = {a for d in drafts for a in d['to']}
    seen = {}
    for rec in records.values():
        seen[rec['mid'] or id(rec)] = rec
        report['without_lead_id'] += not rec['lead']
        report['foreign_sender'] += rec['from'] != [SENDERS[owner]]
    report['archive_total'] = len(records)
    report['unique_message_ids'] = len(seen)
    report['only_copy'] = sum(not (r['mid'] in mids or r['lead'] in leads or set(r['to']) & recipients)
                              for r in seen.values())
    return report, uids


def _count(imap, folder):
    if not _select(imap, folder):
        raise RuntimeError('TRASH_UNAVAILABLE')
    return len(_uids(imap))


def _quoted(name):
    return '"' + name.replace('\\', '\\\\').replace('"', '\\"') + '"'


def purge_owner(owner, client, apply):
    archive = mailbox_arg(ARCHIVE)
    with client._get_imap() as imap:
        trash_name = find_trash(imap, client.cfg)
        trash = _quoted(trash_name)
        report, uids = _survey(imap, client.cfg, owner, archive)
        report.update(trash_folder=trash_name, moved=0, trash_before=_count(imap, trash))
        report.update(archive_after=report['archive_total'], trash_after=report['trash_before'])
        if not apply or not uids:
            return report
        if not _select(imap, archive, readonly=False):
            raise RuntimeError('ARCHIVE_UNAVAILABLE')
        validity = _validity(imap)
        for start in range(0, len(uids), MOVE_CHUNK):
            chunk = uids[start:start + MOVE_CHUNK]
            if imap.uid('MOVE', ','.join(chunk), trash)[0] != 'OK':
                raise RuntimeError('ARCHIVE_MOVE_FAILED')
            report['moved'] += len(chunk)
        if not _select(imap, archive) or _validity(imap) != validity:
            raise RuntimeError('ARCHIVE_CHANGED_DURING_PURGE')
        report['archive_after'] = len(_uids(imap))
        report['trash_after'] = _count(imap, trash)
        if report['archive_after']:
            raise RuntimeError('ARCHIVE_NOT_EMPTY')
        # Größer ist erlaubt (parallel gelöschte Mails), kleiner hieße: Mails sind nicht angekommen.
        if report['trash_after'] - report['trash_before'] < report['moved']:
            raise RuntimeError('TRASH_READBACK_MISMATCH')
    return report


def purge_archive(owners, clients, apply=False):
    return {'dry_run': not apply, 'customer_emails_sent': 0, 'crm_writes': 0,
            'per_owner': {owner: purge_owner(owner, clients[owner], apply) for owner in owners}}


def nonfinal_plan(audit_dir):
    """Teilt das Audit in endgültig, zu löschen und unberührt (Testmails und Entwürfe ohne CRM-Lead)."""
    from draft_verify import _load_json, _load_leads, _read_raw, classify
    audit_dir = Path(audit_dir)
    drafts = _load_json(audit_dir / 'drafts.json', 'DRAFTS_UNREADABLE')
    leads = _load_leads(audit_dir)
    plan = {}
    for record in drafts:
        entry = plan.setdefault(record['owner'], {'final': 0, 'kept_not_crm': 0, 'reasons': Counter(), 'records': []})
        lead = leads.get(str(record.get('lead_id') or ''))
        bucket, reason = classify(record, lead, _read_raw(record))
        if bucket == 'OK':
            entry['final'] += 1
        elif not lead or record.get('internal_test'):
            entry['kept_not_crm'] += 1
        else:
            entry['reasons'][reason] += 1
            entry['records'].append(record)
    return plan


def _move_nonfinal(imap, cfg, records):
    trash_name = find_trash(imap, cfg)
    trash = _quoted(trash_name)
    before = _count(imap, trash)
    moved = changed = 0
    for folder in sorted({r['folder'] for r in records}):
        if not _select(imap, folder, readonly=False):
            raise RuntimeError('DRAFTS_FOLDER_UNAVAILABLE')
        validity = _validity(imap)
        for record in (r for r in records if r['folder'] == folder):
            if str(record['uidvalidity']) != validity:
                raise RuntimeError('DRAFT_UIDVALIDITY_CHANGED')
            typ, data = imap.uid('FETCH', str(record['uid']), '(BODY.PEEK[])')
            parts = [x[1] for x in data or [] if isinstance(x, tuple)] if typ == 'OK' else []
            # Seit dem Audit geändert oder schon weg: nicht anfassen.
            if len(parts) != 1 or hashlib.sha256(parts[0]).hexdigest() != record['sha256']:
                changed += 1
                continue
            if imap.uid('MOVE', str(record['uid']), trash)[0] != 'OK':
                raise RuntimeError('DRAFT_MOVE_FAILED')
            moved += 1
    after = _count(imap, trash)
    if after - before < moved:
        raise RuntimeError('TRASH_READBACK_MISMATCH')
    return {'trash_folder': trash_name, 'moved': moved, 'changed_since_audit': changed}


def purge_nonfinal(audit_dir, owners, clients, apply=False):
    plan = nonfinal_plan(audit_dir)
    result = {}
    for owner in owners:
        entry = plan.get(owner) or {'final': 0, 'kept_not_crm': 0, 'reasons': Counter(), 'records': []}
        selected, scanned = len(entry['records']), entry['final'] + entry['kept_not_crm'] + len(entry['records'])
        if selected > scanned * MAX_NONFINAL_SHARE:
            raise RuntimeError('NONFINAL_PLAN_TOO_LARGE')
        report = {'final': entry['final'], 'selected': selected, 'reasons': dict(entry['reasons']),
                  'kept_not_crm': entry['kept_not_crm'], 'moved': 0, 'changed_since_audit': 0}
        if apply and selected:
            with clients[owner]._get_imap() as imap:
                report.update(_move_nonfinal(imap, clients[owner].cfg, entry['records']))
        result[owner] = report
    return {'dry_run': not apply, 'customer_emails_sent': 0, 'crm_writes': 0, 'per_owner': result}
