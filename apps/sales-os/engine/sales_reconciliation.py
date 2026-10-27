"""Read-only SSOT/IMAP reconciliation. No SMTP, STORE, APPEND or EXPUNGE.

Full original MIME files are saved privately before any later remediation.
The report is evidence, never an automatic legal authorization.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs, unquote
from urllib.request import Request
from hsb_core import check_eligibility, normalize_owner, sanitize_company_name

SENDERS = {'JOEL': 'j-cherino@hsb-boden.com', 'JORDI': 'j-post@hsb-boden.com'}


def addresses(value):
    return [a.lower().strip() for _, a in getaddresses([str(value or '')]) if a]


def has_unreviewed_legacy_variant(msg, owner):
    # Same-address Reply-To in an already reconciled original changes no route.
    # New messages still omit Reply-To. Attachments and other routes stay held.
    # Every Reply-To header counts: a second header would add an unchecked reply route.
    replies = msg.get_all('Reply-To') or []
    return bool(len(replies) > 1
                or (replies and addresses(replies[0]) != [SENDERS[owner]])
                or any(p.get_content_disposition() == 'attachment' for p in msg.walk()))


def assess_message(raw, owner, leads):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    recipients = addresses(msg.get('To'))
    issues, warnings, bodies, links = [], [], [], []
    for part in msg.walk():
        if part.get_content_type() in ('text/plain', 'text/html'):
            try:
                bodies.append(part.get_content())
            except (LookupError, UnicodeError):
                issues.append('BODY_DECODE_ERROR')
        if part.defects:
            issues.append('MIME_DEFECT')
    body = html.unescape('\n'.join(str(b) for b in bodies))
    links = list(dict.fromkeys(re.findall(r'https?://[^\s<>"\x27]+', body)))
    mid = str(msg.get('Message-ID') or '').strip()
    subject = str(msg.get('Subject') or '')
    if len(recipients) != 1 or msg.get('Cc') or msg.get('Bcc'):
        issues.append('RECIPIENT_COUNT')
    matching = [l for l in leads if (l.get('E-Mail') or l.get('Email') or '').strip().lower() in recipients]
    if len(matching) != 1:
        issues.append('CRM_RECIPIENT_AMBIGUOUS' if matching else 'CRM_RECIPIENT_MISSING')
    lead = matching[0] if len(matching) == 1 else {}
    lead_id = str(lead.get('Lead-ID') or lead.get('Lead_ID') or '')
    explicit = set(re.findall(r'HSB-\d{8}-\d+', str(msg.get('X-HSB-Lead-ID') or '') + body))
    for url in links:
        query = parse_qs(urlsplit(url).query)
        explicit.update(query.get('lead', []))
        explicit.update(query.get('lid', []))
    crm_ids = {str(lead.get(k) or '') for k in ('Draft_ID', 'Internet_Message_ID', 'Outlook_Message_ID')}
    if explicit and explicit != {lead_id}:
        issues.append('LEAD_ID_CONFLICT')
    if not explicit and (not mid or mid not in crm_ids):
        issues.append('LEAD_ID_INFERRED_ONLY')
    if lead and normalize_owner(lead.get('Verantwortlicher') or lead.get('Owner')) != owner:
        issues.append('WRONG_OWNER')
    if addresses(msg.get('From')) != [SENDERS[owner]]:
        issues.append('WRONG_SENDER')
    if not mid or not re.fullmatch(r'<[^<>\s]+@[^<>\s]+>', mid):
        issues.append('MESSAGE_ID_INVALID')
    template_id = str(msg.get('X-HSB-Template-ID') or '').strip()
    is_v2 = template_id.startswith('v2-')
    company = str(lead.get('Firma') or lead.get('Company') or '').strip()
    contact = str(lead.get('Ansprechpartner') or lead.get('Contact') or '').strip()
    if not company or sanitize_company_name(company, recipients[0] if recipients else '') == 'Ihr Unternehmen':
        issues.append('COMPANY_UNVERIFIED')
    if is_v2:
        # Folgemails antworten im Thread: das Re:/AW:-Praefix zaehlt nicht zur 50-Zeichen-Grenze.
        if not subject or len(re.sub(r'^(?:re|aw):\s*', '', subject, flags=re.I)) > 50:
            issues.append('SUBJECT_TOO_LONG')
    elif not subject or (company and company.casefold() not in subject.casefold()):
        issues.append('SUBJECT_NOT_COMPANY_SPECIFIC')
    body_names = [company]
    if is_v2:
        from canonical_template_factory import short_company
        body_names.append(short_company(company))
    if not (any(n and n.casefold() in body.casefold() for n in body_names) or (len(contact) > 3 and contact.casefold() in body.casefold())):
        issues.append('BODY_NOT_COMPANY_OR_CONTACT_SPECIFIC')
    if re.search(r'\{\{|\[FIRMA\]|\[NAME\]|undefined|Sehr geehrte/r', body, re.I):
        issues.append('UNRESOLVED_PLACEHOLDER')
    flyer_links = [u for u in links if urlsplit(u).netloc.lower() in {'www.hsb-boden.de', 'hsb-boden.de'} and ('flyer' in urlsplit(u).path.lower() or urlsplit(u).path.lower().endswith('.pdf'))]
    optout_links = [u for u in links if urlsplit(u).netloc.lower() == 'www.hsb-boden.de' and urlsplit(u).path.rstrip('/') == '/abmelden']
    if is_v2:
        if template_id.endswith('-s1'):
            surname = contact.split()[-1].casefold() if len(contact.split()) > 1 else ''
            forbidden = ['@', *(r.casefold() for r in recipients)]
            forbidden += [t for t in [*(r.split('@')[0].casefold() for r in recipients), surname] if len(t) >= 3]

            def _v2_link_ok(u):
                parts = urlsplit(u)
                decoded = unquote(u).casefold()
                # Statische Host- und Kampagnennamen sind keine Empfängerdaten.
                # Personenbezogene Query-Werte prüfen, nicht 'Boden' im eigenen Hostnamen.
                query_values = [v.casefold() for key, vals in parse_qs(parts.query).items()
                                if key not in {'utm_source','utm_medium','utm_campaign','utm_content','s'} for v in vals]
                if '@' in decoded or any(t in val for t in forbidden[1:] for val in query_values):
                    return False
                if any(key not in {'utm_source','utm_medium','utm_campaign','utm_content','s'} for key in parse_qs(parts.query)):
                    return False
                return parts.netloc.lower() == 'www.hsb-boden.de' and (
                    parts.path.rstrip('/') == '/flyer' or re.fullmatch(r'/r/[A-Za-z0-9_\-.~]+', parts.path))
            if len(links) > 1 or not all(_v2_link_ok(u) for u in links):
                issues.append('V2_LINK_INVALID')
        elif links:
            issues.append('V2_LINK_INVALID')
        if not re.search(r'Abmelden', body):
            issues.append('V2_OPTOUT_LINE_MISSING')
    else:
        if not flyer_links:
            issues.append('FLYER_LINK_MISSING')
        # Persoenlich: Lead-ID im Parameter lid (ohne Adresse) oder die bisherige Adressform.
        def _personal_optout(u):
            return bool(lead_id and lead_id in parse_qs(urlsplit(u).query).get('lid', [])) or bool(
                recipients and recipients[0] in unquote(u).lower())
        if not optout_links or not any(_personal_optout(u) for u in optout_links):
            issues.append('PERSONAL_OPTOUT_LINK_MISSING')
    if has_unreviewed_legacy_variant(msg, owner):
        issues.append('HISTORICAL_VARIANT_REQUIRES_REVIEW')
    if msg.get('Reply-To'):
        warnings.append('HISTORICAL_REPLY_TO_' + ('DE' if 'hsb-boden.de' in str(msg.get('Reply-To')) else 'OTHER'))
    if 'text/plain' not in [p.get_content_type() for p in msg.walk()]:
        warnings.append('PLAIN_TEXT_MISSING')
    return {'owner': owner, 'recipients': recipients, 'lead_id': lead_id,
            'crm_unique': len(matching) == 1, 'message_id': mid, 'subject': subject,
            'issues': sorted(set(issues)), 'warnings': sorted(set(warnings)),
            'links': links, 'flyer_links': flyer_links, 'optout_links': optout_links,
            'pdf_count': sum(p.get_content_type() == 'application/pdf' for p in msg.walk()),
            'eligibility_reasons': check_eligibility(lead).reasons,
            'sha256': hashlib.sha256(raw).hexdigest()}


def scan_mailbox(owner, output):
    from com_mailbox_manager import ComMailboxClient
    client = ComMailboxClient(owner, timeout=30)
    result = {'owner': owner, 'auth': client.test_connection(), 'drafts': [], 'sent': [], 'inbound': []}
    with client._get_imap() as imap:
        for kind in ('drafts', 'sent', 'inbox'):
            folder = client.cfg[kind + '_folder']
            status, count = imap.select(folder, readonly=True)
            if status != 'OK':
                raise RuntimeError(f'{owner}: {kind} unavailable')
            validity = imap.response('UIDVALIDITY')[1]
            uidvalidity = validity[0].decode() if validity and validity[0] else ''
            typ, data = imap.uid('search', None, 'ALL')
            if typ != 'OK':
                raise RuntimeError('IMAP_SEARCH_FAILED')
            uids = data[0].split() if data and data[0] else []
            target = output / owner / kind
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
            for start in range(0, len(uids), 20):
                chunk = uids[start:start+20]
                # BODY.PEEK[] does not set Seen. SELECT is read-only too.
                typ, fetched = imap.uid('fetch', b','.join(chunk), '(UID BODY.PEEK[])')
                if typ != 'OK':
                    raise RuntimeError('IMAP_FETCH_FAILED')
                got = set()
                for item in fetched:
                    if not isinstance(item, tuple):
                        continue
                    m = re.search(rb'UID (\d+)', item[0])
                    if not m:
                        raise RuntimeError('UID_MISSING')
                    uid = m[1].decode(); got.add(uid)
                    raw = item[1]
                    path = target / f'{uidvalidity}-{uid}.eml'
                    path.write_bytes(raw); path.chmod(0o600)
                    result[{'inbox': 'inbound'}.get(kind, kind)].append({'uid': uid, 'uidvalidity': uidvalidity, 'folder': folder, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
                if got != {u.decode() for u in chunk}:
                    raise RuntimeError('IMAP_FETCH_INCOMPLETE')
                if start % 200 == 0:
                    print(f'SCAN {owner} {kind}: {min(start+20,len(uids))}/{len(uids)}', flush=True)
            # Confirm no concurrent mailbox changes invalidate this snapshot.
            typ, final = imap.uid('search', None, 'ALL')
            if typ != 'OK' or final[0].split() != uids:
                raise RuntimeError('MAILBOX_CHANGED_DURING_SCAN')
    return result


def urlopen(req, timeout=20):
    # Wiederverwendung des geprüften Openers: Redirect-Prüfung, IP-Pinning, kein Proxy/FTP.
    from bounce_rescue_agent import build_public_opener
    return build_public_opener().open(req, timeout=timeout)


def probe_url(url):
    # Never request a real recipient's unsubscribe URL: page checks use no email.
    req = Request(url, headers={'User-Agent': 'HSB-Reconciliation/1.0'})
    with urlopen(req, timeout=30) as response:
        import time
        deadline=time.monotonic()+20
        read=getattr(response,'read1',response.read)
        chunks=[];size=0
        while True:
            chunk=read(65536)
            if time.monotonic()>deadline:raise RuntimeError('LINK_READ_TIMEOUT')
            if not chunk:break
            size+=len(chunk)
            if size>10*1024*1024:raise RuntimeError('LINK_RESPONSE_TOO_LARGE')
            chunks.append(chunk)
        data=b''.join(chunks)
        reachable = response.status == 200
        valid = reachable and (data.startswith(b'%PDF-') or (b'<html' in data.lower() and len(data) > 500))
        result = {'status': response.status, 'final_url': response.url, 'content_type': response.headers.get('Content-Type'), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'reachable': reachable, 'valid': valid}
        if urlsplit(url).path.rstrip('/') == '/abmelden':
            class Links(HTMLParser):
                def __init__(self):
                    super().__init__(); self.hrefs = []
                def handle_starttag(self, tag, attrs):
                    if tag == 'a':
                        self.hrefs.extend(value for key, value in attrs if key == 'href' and value)
            page = data.decode('utf-8', errors='replace')
            parsed = Links(); parsed.feed(page)
            routes = [urlsplit(href) for href in parsed.hrefs]
            mailto = any(route.scheme == 'mailto' and route.path.lower() in SENDERS.values()
                         and parse_qs(route.query).get('subject', [''])[0].lower() in {'abmelden', 'abmeldung', 'unsubscribe'}
                         for route in routes)
            result.update(valid=bool(valid and mailto and 'erfolgreich abgemeldet' not in page.lower()),
                          request_route='MONITORED_COM_MAILTO' if mailto else 'MISSING',
                          crm_update_on_page_load=False)
        return result


def link_health(urls, cache=None, probe=None):
    """Jeden eindeutigen eigenen Link einmal ohne Query prüfen; fremde Ziele geschlossen halten."""
    cache = {} if cache is None else cache
    probe = probe or probe_url
    issues = []
    for url in urls:
        try:
            parsed = urlsplit(url)
            base = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
            if base not in cache:
                if parsed.scheme != 'https' or parsed.netloc.lower() not in {'www.hsb-boden.de', 'hsb-boden.de'}:
                    cache[base] = False
                else:
                    try:
                        cache[base] = bool(probe(base).get('valid'))
                    except Exception:
                        cache[base] = False
            if not cache[base]:
                issues.append(f'LINK_BROKEN:{parsed.netloc}{parsed.path}')
        except ValueError:
            issues.append('LINK_BROKEN:INVALID_URL')
    return sorted(set(issues))


def write_crm_audit(output):
    """Write only audit columns in the existing master, then verify every row."""
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    svc=get_sheets_service()
    snapshot=json.loads((output/'crm-original.json').read_text())['valueRanges'][0]['values']
    live=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute().get('values',[])
    if live!=snapshot:raise RuntimeError('CRM_CHANGED_SINCE_AUDIT: refresh snapshot before audit writeback')
    meta=svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID,fields='sheets(properties)').execute()
    sheet=next(s['properties'] for s in meta['sheets'] if s['properties']['title']=='ALL_LEADS')
    columns=['Reconciliation_Status','Reconciliation_Reasons','Reconciliation_Draft_Refs','Reconciliation_At','Reconciliation_Run']
    grid=sheet['gridProperties']
    if grid['columnCount']>65:
        existing=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!BN1:BR1').execute().get('values',[])
        if existing and existing!=[columns]:raise RuntimeError('AUDIT_COLUMN_CONFLICT')
    if grid['columnCount']<70:
        svc.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID,body={'requests':[{'updateSheetProperties':{'properties':{'sheetId':sheet['sheetId'],'gridProperties':{'columnCount':70}},'fields':'gridProperties.columnCount'}}]}).execute()
    balances=json.loads((output/'leads.json').read_text());summary=json.loads((output/'summary.json').read_text())
    runid='HSB-RECON-'+hashlib.sha256((output/'leads.json').read_bytes()).hexdigest()[:16]
    matrix=[columns]+[['READY' if b['sendable'] else 'HOLD', '; '.join(b['reasons']),json.dumps(b['draft_uids'],ensure_ascii=False,separators=(',',':')),summary['timestamp'],runid] for b in balances]
    for start in range(0,len(matrix),500):
        chunk=matrix[start:start+500];target=f'ALL_LEADS!BN{start+1}:BR{start+len(chunk)}'
        svc.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,range=target,valueInputOption='RAW',body={'values':chunk}).execute()
        back=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range=target).execute().get('values',[])
        if back!=chunk:raise RuntimeError('AUDIT_CRM_READBACK_MISMATCH')
    svc.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID,body={'requests':[
        {'updateDimensionProperties':{'range':{'sheetId':sheet['sheetId'],'dimension':'COLUMNS','startIndex':65,'endIndex':70},'properties':{'pixelSize':240},'fields':'pixelSize'}},
        {'repeatCell':{'range':{'sheetId':sheet['sheetId'],'startRowIndex':0,'endRowIndex':1,'startColumnIndex':65,'endColumnIndex':70},'cell':{'userEnteredFormat':{'textFormat':{'bold':True},'wrapStrategy':'WRAP'}},'fields':'userEnteredFormat.textFormat,userEnteredFormat.wrapStrategy'}}]}).execute()
    proof={'rows_verified':len(balances),'range':'ALL_LEADS!BN1:BR6425','run_id':runid,'customer_emails_sent':0}
    (output/'crm-writeback-proof.json').write_text(json.dumps(proof,indent=2))
    return proof


def run_audit(output, reuse_snapshot=False):
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    from inbound_classifier import classify_inbound_message
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    svc = get_sheets_service()
    ranges = ['ALL_LEADS!A1:BU6425', 'DE_VERSENDUNGEN_FORENSIK!A1:J1324', 'INBOUND_EVENTS!A1:M5126']
    snapshot = (json.loads((output/'crm-original.json').read_text()) if reuse_snapshot else
        svc.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=ranges).execute())
    if not reuse_snapshot:
        (output/'crm-original.json').write_text(json.dumps(snapshot, ensure_ascii=False))
    values = snapshot['valueRanges']; rows = values[0].get('values', [])
    leads = [dict(zip(rows[0], row), _row=i) for i, row in enumerate(rows[1:], 2)]
    forensic = values[1].get('values', [])
    col = forensic[0].index('Empfaenger_Email')
    historic = {a for row in forensic[1:] if len(row)>col for a in addresses(row[col])}
    lead_ids = Counter(str(l.get('Lead-ID') or '') for l in leads)
    emails = Counter(str(l.get('E-Mail') or '').strip().lower() for l in leads)
    owners = Counter(normalize_owner(l.get('Verantwortlicher')) for l in leads)
    if len(leads) != 6424 or owners != {'JOEL': 3212, 'JORDI': 3212}:
        raise RuntimeError(f'CRM_TOTAL_OR_OWNER_MISMATCH {len(leads)} {owners}')
    if reuse_snapshot:
        mailboxes=json.loads((output/'mailboxes.json').read_text())
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            mailboxes = dict(zip(SENDERS, pool.map(lambda o: scan_mailbox(o, output), SENDERS)))
    draft_records, contacted, inbound_records, inbound_blocked = [], set(historic), [], set()
    for owner, mailbox in mailboxes.items():
        for item in mailbox['sent']:
            msg = BytesParser(policy=policy.default).parsebytes(Path(item['path']).read_bytes())
            item['message_id'] = str(msg.get('Message-ID') or '')
            item['date'] = str(msg.get('Date') or '')
            item['recipients'] = addresses(msg.get('To'))
            contacted.update(item['recipients'])
        for item in mailbox['inbound']:
            msg = BytesParser(policy=policy.default).parsebytes(Path(item['path']).read_bytes())
            body = '\n'.join(str(p.get_content()) for p in msg.walk() if p.get_content_type() in ('text/plain','text/html'))
            cls = classify_inbound_message(str(msg.get('From') or ''), str(msg.get('Subject') or ''), body)
            targets = [cls.extracted_email.lower()] if cls.extracted_email else addresses(msg.get('From'))
            inbound_blocked.update(targets)
            inbound_records.append(dict(item, owner=owner, category=cls.category, targets=targets, message_id=str(msg.get('Message-ID') or '')))
        for item in mailbox['drafts']:
            raw=Path(item['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise RuntimeError('ORIGINAL_HASH_MISMATCH')
            record = assess_message(raw, owner, leads)
            from outbound_safety import INTERNAL_RECIPIENTS
            record['internal_test']=bool(record['recipients']) and all(a in INTERNAL_RECIPIENTS for a in record['recipients'])
            draft_records.append(dict(item, **record))
    contacted.update(str(l.get('E-Mail') or '').strip().lower() for l in leads if str(l.get('Send_Status') or '').lower() in {'sent', 'gesendet'} or l.get('Send_Datum'))
    link_cache = {}
    for draft in draft_records:
        draft['issues'].extend(link_health(draft.get('links', draft.get('flyer_links', [])), link_cache))
    counts = Counter(a for d in draft_records if not d['internal_test'] for a in d['recipients'])
    mids = Counter(d['message_id'] for d in draft_records if d['message_id'])
    bylead = defaultdict(list)
    links = {'https://www.hsb-boden.de/abmelden': probe_url('https://www.hsb-boden.de/abmelden')}
    for d in draft_records:
        for url in d['flyer_links']:
            split = urlsplit(url); base = f'{split.scheme}://{split.netloc}{split.path}'
            if base not in links:
                try: links[base] = probe_url(base)
                except Exception as exc: links[base] = {'valid':False, 'error':type(exc).__name__}
            if not links[base]['valid']: d['issues'].append('FLYER_LINK_UNREACHABLE')
        if not links['https://www.hsb-boden.de/abmelden']['valid']: d['issues'].append('OPTOUT_PAGE_NOT_FUNCTIONAL')
        for a in d['recipients']:
            if counts[a] > 1: d['issues'].append('DUPLICATE_DRAFT_RECIPIENT')
            if a in contacted: d['issues'].append('ALREADY_CONTACTED')
            if a in inbound_blocked: d['issues'].append('INBOUND_REQUIRES_REVIEW')
        if mids[d['message_id']] > 1: d['issues'].append('DUPLICATE_MESSAGE_ID')
        if lead_ids[d['lead_id']] != 1: d['issues'].append('CRM_LEAD_ID_AMBIGUOUS')
        d['technical_ready'] = not d['issues'] and not d['internal_test']
        d['sendable'] = d['technical_ready'] and not d['eligibility_reasons']
        bylead[d['lead_id']].append(d)
    balances = []
    for l in leads:
        lid = str(l.get('Lead-ID') or ''); em = str(l.get('E-Mail') or '').strip().lower()
        ds = bylead[lid]; reasons = list(check_eligibility(l).reasons)
        if em in contacted: reasons.append('ALREADY_CONTACTED')
        if em in inbound_blocked: reasons.append('INBOUND_REQUIRES_REVIEW')
        if emails[em] != 1 or lead_ids[lid] != 1: reasons.append('CRM_DUPLICATE')
        if not ds: reasons.append('NO_DRAFT')
        elif len(ds)!=1: reasons.append('DRAFT_COUNT_NOT_ONE')
        for d in ds: reasons.extend(d['issues'])
        balances.append({'lead_id':lid, 'row':l['_row'], 'email':em, 'owner':normalize_owner(l.get('Verantwortlicher')), 'draft_uids':[{'owner':d['owner'],'uidvalidity':d['uidvalidity'],'uid':d['uid'],'message_id':d['message_id']} for d in ds], 'reasons':sorted(set(reasons)), 'sendable':not reasons})
    source_at=json.loads((output/'summary.json').read_text())['timestamp'] if reuse_snapshot else datetime.now(timezone.utc).isoformat()
    summary = {'timestamp':source_at,'reassessed_at':datetime.now(timezone.utc).isoformat(), 'crm_total':len(leads), 'crm_owners':dict(owners), 'forensic_rows':len(forensic)-1, 'forensic_unique_recipients':len(historic), 'owners':{}, 'lead_reasons':dict(Counter(r.split('(')[0].strip() for b in balances for r in b['reasons'])), 'inbound_categories':dict(Counter(x['category'] for x in inbound_records)), 'links':links, 'customer_emails_sent':0, 'status':'NICHT VERSANDBEREIT'}
    for owner in SENDERS:
        ds=[d for d in draft_records if d['owner']==owner]
        summary['owners'][owner]={'scanned':len(ds),'unique_recipients':len({a for d in ds for a in d['recipients']}),'crm_unique':sum(d['crm_unique'] for d in ds),'technical_ready':sum(d['technical_ready'] for d in ds),'sendable':sum(d['sendable'] for d in ds),'issues':dict(Counter(i for d in ds for i in d['issues'])),'warnings':dict(Counter(i for d in ds for i in d['warnings'])),'sent_count':len(mailboxes[owner]['sent']),'inbound_count':len(mailboxes[owner]['inbound']),'imap_auth':mailboxes[owner]['auth']['imap'],'smtp_auth':mailboxes[owner]['auth']['smtp']}
        summary['owners'][owner]['internal_tests']=sum(d['internal_test'] for d in ds)
        summary['owners'][owner]['customer_drafts']=sum(not d['internal_test'] for d in ds)
    for name, data in [('summary',summary),('drafts',draft_records),('leads',balances),('mailboxes',mailboxes),('inbound',inbound_records),('queue',[b for b in balances if b['sendable']])]:
        (output/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reassess',action='store_true',help='Reassess saved originals without re-fetching; preserves snapshot time')
    args=p.parse_args()
    run_audit(args.output,reuse_snapshot=args.reassess)
