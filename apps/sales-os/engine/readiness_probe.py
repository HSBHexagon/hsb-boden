"""Read-only live readiness sample while the existing writer continues. No SMTP."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
import json
import re
from canonical_template_factory import REPARATUR_COPY_REV
from com_mailbox_manager import ComMailboxClient
from hsb_core import normalize_owner
from sales_reconciliation import assess_message
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

def search(imap, *query):
    status, data = imap.uid('search', None, *query)
    if status != 'OK':
        raise RuntimeError('PROBE_SEARCH_FAILED')
    return data[0].split() if data and data[0] else []

def inspect_owner(owner, by_id):
    client = ComMailboxClient(owner, timeout=60)
    counts = Counter(checked=0, ready=0, blocked=0, content_issues=0, binding_issues=0, changed=0)
    with client._get_imap() as imap:
        status, _ = imap.select(client.cfg['drafts_folder'], readonly=True)
        if status != 'OK':
            raise RuntimeError('PROBE_DRAFTS_UNAVAILABLE')
        total = search(imap, 'ALL')
        current = search(imap, 'HEADER', 'X-HSB-Copy-Rev', '"' + REPARATUR_COPY_REV + '"')
        for start in range(0, min(len(current), 500), 20):
            chunk = current[start:start + 20]
            status, data = imap.uid('fetch', b','.join(chunk), '(UID BODY.PEEK[])')
            if status != 'OK':
                raise RuntimeError('PROBE_FETCH_FAILED')
            for item in data or []:
                if not isinstance(item, tuple):
                    continue
                uid_match = re.search(rb'UID (\d+)', item[0])
                if not uid_match:
                    raise RuntimeError('PROBE_UID_MISSING')
                raw = item[1]
                message = BytesParser(policy=policy.default).parsebytes(raw)
                matches = by_id.get(str(message.get('X-HSB-Lead-ID') or '').strip(), [])
                counts['checked'] += 1
                if len(matches) != 1:
                    counts['binding_issues'] += 1
                    continue
                lead = matches[0]
                record = assess_message(raw, owner, [lead])
                if record['issues']:
                    counts['content_issues'] += 1
                    continue
                if record['eligibility_reasons']:
                    counts['blocked'] += 1
                    continue
                if (normalize_owner(lead.get('Verantwortlicher')) != owner
                        or lead.get('Draft_ID') != str(message.get('Message-ID') or '')
                        or str(message.get('X-HSB-Copy-Rev') or '') != REPARATUR_COPY_REV):
                    counts['binding_issues'] += 1
                    continue
                mid = str(message.get('Message-ID') or '')
                live_uids = search(imap, 'HEADER', 'Message-ID', '"' + mid + '"')
                if live_uids != [uid_match[1]]:
                    counts['changed'] += 1
                    continue
                counts['ready'] += 1
                if counts['ready'] >= 50:
                    break
            if counts['ready'] >= 50:
                break
        return dict(counts, total_observed=len(total), current_revision_observed=len(current),
                    revision=REPARATUR_COPY_REV, checked_at=datetime.now(timezone.utc).isoformat(),
                    verification='BODY_AND_CRM_SAMPLE_ONLY', full_inventory_stability='NOT_CLAIMED')

def main():
    rows = get_sheets_service().spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='ALL_LEADS!A1:BU6425').execute().get('values', [])
    if not rows or len(rows) != 6425 or rows[0][0] != 'Lead-ID':
        raise RuntimeError('PROBE_CRM_SHAPE_CHANGED')
    by_id = defaultdict(list)
    for row in rows[1:]:
        lead = dict(zip(rows[0], row))
        by_id[str(lead.get('Lead-ID') or '')].append(lead)
    owners = ('JOEL', 'JORDI')
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = dict(zip(owners, pool.map(lambda owner: inspect_owner(owner, by_id), owners)))
    print(json.dumps({'readiness_probe': result, 'customer_emails_sent': 0}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
