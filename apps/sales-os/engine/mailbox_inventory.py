"""Read-only header inventory for draft ownership and distribution; never SMTP.

Unlike the full MIME audit this downloads no bodies or attachments. Private
records stay in the runtime; only aggregate counts are printed in Actions.
"""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from email import policy
from email.parser import BytesParser
import json
import os
from pathlib import Path
import re
import time

from hsb_core import normalize_owner
from lead_quality import segment_for
from sales_reconciliation import SENDERS, addresses

FIELDS = 'MESSAGE-ID FROM TO X-HSB-LEAD-ID X-HSB-TEMPLATE-ID X-HSB-COPY-REV'


def _validity(imap):
    data = imap.response('UIDVALIDITY')[1]
    if not data or not data[0]:
        raise RuntimeError('INVENTORY_UIDVALIDITY_MISSING')
    return data[0].decode() if isinstance(data[0], bytes) else str(data[0])


def _uids(imap):
    typ, data = imap.uid('SEARCH', None, 'ALL')
    if typ != 'OK':
        raise RuntimeError('INVENTORY_SEARCH_FAILED')
    if len(data or []) != 1 or not isinstance(data[0], bytes):
        raise RuntimeError('INVENTORY_SEARCH_INCOMPLETE')
    uids = data[0].split()
    if any(not uid.isdigit() for uid in uids) or len(set(uids)) != len(uids):
        raise RuntimeError('INVENTORY_SEARCH_INCOMPLETE')
    return uids


def _revision_bucket(value):
    if not value:
        return '(missing)'
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) and date.fromisoformat(value):
            return value
    except ValueError:
        pass
    return '(unrecognized)'


def scan_headers(owner, client):
    result = {}
    with client._get_imap() as imap:
        for kind in ('drafts', 'sent', 'inbox'):
            folder = client.cfg[kind + '_folder']
            typ, _ = imap.select(folder, readonly=True)
            if typ != 'OK':
                raise RuntimeError('INVENTORY_FOLDER_UNAVAILABLE')
            validity, uids = _validity(imap), _uids(imap)
            records = []
            for start in range(0, len(uids), 500):
                chunk = uids[start:start + 500]
                typ, data = imap.uid('FETCH', b','.join(chunk), f'(UID BODY.PEEK[HEADER.FIELDS ({FIELDS})])')
                if typ != 'OK':
                    raise RuntimeError('INVENTORY_FETCH_FAILED')
                seen = set()
                for item in data or []:
                    if not isinstance(item, tuple):
                        continue
                    match = re.search(rb'\bUID (\d+)\b', item[0])
                    if not match or match[1] in seen:
                        raise RuntimeError('INVENTORY_UID_AMBIGUOUS')
                    uid = match[1]
                    seen.add(uid)
                    msg = BytesParser(policy=policy.default).parsebytes(item[1])
                    records.append({
                        'owner': owner, 'folder': folder, 'uidvalidity': validity, 'uid': uid.decode(),
                        'message_id': str(msg.get('Message-ID') or '').strip(),
                        'recipients': addresses(msg.get('To')), 'senders': addresses(msg.get('From')),
                        'lead_id': str(msg.get('X-HSB-Lead-ID') or '').strip(),
                        'template_id': str(msg.get('X-HSB-Template-ID') or '').strip(),
                        'copy_rev': str(msg.get('X-HSB-Copy-Rev') or '').strip(),
                    })
                if seen != set(chunk):
                    raise RuntimeError('INVENTORY_FETCH_INCOMPLETE')
            if _uids(imap) != uids:
                raise RuntimeError('MAILBOX_CHANGED_DURING_INVENTORY')
            # imaplib.response consumes the SELECT response; select again for
            # a fresh UIDVALIDITY instead of reading the consumed response twice.
            typ, _ = imap.select(folder, readonly=True)
            if typ != 'OK' or _validity(imap) != validity:
                raise RuntimeError('MAILBOX_CHANGED_DURING_INVENTORY')
            result[kind] = records
    return result


def summarize(leads, mailboxes):
    by_id, by_email = defaultdict(list), defaultdict(list)
    for lead in leads:
        by_id[str(lead.get('Lead-ID') or '')].append(lead)
        by_email[str(lead.get('E-Mail') or '').strip().lower()].append(lead)
    all_drafts = [d for box in mailboxes.values() for d in box['drafts']]
    recipient_counts = Counter(a for d in all_drafts for a in d['recipients'])
    report = {'crm_total': len(leads), 'owners': {}, 'crm_distribution': {}, 'customer_emails_sent': 0}
    for owner in SENDERS:
        owned = [l for l in leads if normalize_owner(l.get('Verantwortlicher')) == owner]
        report['crm_distribution'][owner] = {
            'total': len(owned), 'segments': dict(Counter(segment_for(l) for l in owned)),
            'drafted': sum(str(l.get('Send_Status') or '').lower() == 'drafted' for l in owned),
        }
        box = mailboxes[owner]
        counts = {'drafts': len(box['drafts']), 'sent': len(box['sent']), 'inbox': len(box['inbox']),
                  'crm_unique': 0, 'wrong_crm_owner': 0, 'wrong_from': 0,
                  'identity_ambiguous': 0, 'duplicate_recipients': 0,
                  'segments': Counter(), 'copy_revisions': Counter()}
        # Exact Message-ID intersection diagnoses the Outlook draft badge without
        # exposing recipients or changing server messages.
        sent_ids = {item.get('message_id') for item in box['sent'] if item.get('message_id')}
        counts['sent_message_still_in_drafts'] = sum(
            bool(draft.get('message_id')) and draft['message_id'] in sent_ids
            for draft in box['drafts']
        )
        for draft in box['drafts']:
            candidates = by_id[draft['lead_id']] if draft['lead_id'] else (
                by_email[draft['recipients'][0]] if len(draft['recipients']) == 1 else [])
            if (len(candidates) != 1 or draft['recipients'] != [
                    str(candidates[0].get('E-Mail') or '').strip().lower()]):
                counts['identity_ambiguous'] += 1
                continue
            lead = candidates[0]
            counts['crm_unique'] += 1
            counts['wrong_crm_owner'] += normalize_owner(lead.get('Verantwortlicher')) != owner
            counts['wrong_from'] += draft['senders'] != [SENDERS[owner]]
            counts['duplicate_recipients'] += recipient_counts[draft['recipients'][0]] > 1
            counts['segments'][segment_for(lead)] += 1
            counts['copy_revisions'][_revision_bucket(draft['copy_rev'])] += 1
        report['owners'][owner] = counts
    return report


def run_inventory(output):
    from com_mailbox_manager import ComMailboxClient
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    os.umask(0o077)
    started = time.monotonic()
    rows = get_sheets_service().spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='ALL_LEADS!A1:BU6425').execute().get('values', [])
    if not rows or rows[0][0] != 'Lead-ID' or len(rows) != 6425:
        raise RuntimeError('INVENTORY_CRM_SHAPE_CHANGED')
    leads = [dict(zip(rows[0], row)) for row in rows[1:]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        boxes = dict(zip(SENDERS, pool.map(lambda o: scan_headers(o, ComMailboxClient(o, timeout=60)), SENDERS)))
    report = summarize(leads, boxes)
    report.update(checked_at=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=round(time.monotonic() - started, 2),
                  body_validation='NOT_PERFORMED_HEADERS_ONLY')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    (output / 'inventory-private.json').write_text(json.dumps(boxes, ensure_ascii=False))
    (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run_inventory(parser.parse_args().output)
