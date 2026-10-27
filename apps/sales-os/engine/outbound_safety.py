"""One bounded customer dispatch path. Unknown acceptance is never retried.

An IMAP CREATE lock serializes writers across devices. A crash leaves the
empty lock folder in place deliberately; reconciliation is required to unlock.
CRM SENDING readback precedes SMTP. Original drafts are never deleted.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import formatdate
import hashlib
import imaplib
from urllib.parse import quote
import re
import json
import os
from pathlib import Path
import random
import sqlite3
import time
from zoneinfo import ZoneInfo
from hsb_core import check_eligibility, normalize_owner

DAILY_CAP = 35
LOCK_FOLDER = 'HSB-SALES-OS-DISPATCH-LOCK'
INTERNAL_RECIPIENTS = {'cherinodiaz@outlook.com', 'j-cherino@hsb-boden.com', 'j-post@hsb-boden.com', 'j-cherino@hsb-boden.de', 'j-post@hsb-boden.de'}


def require_internal_test(to_email, bcc_email=None, extra_allowed=None):
    from email.utils import getaddresses
    recipients = [a.lower() for _, a in getaddresses([to_email, bcc_email or '']) if a]
    allowed = INTERNAL_RECIPIENTS | {a.lower() for a in (extra_allowed or ())}
    if not recipients or any(a not in allowed for a in recipients):
        raise PermissionError('Customer SMTP requires the verified dispatch queue')
    if os.environ.get('HSB_INTERNAL_TEST_SEND_ENABLED') != 'yes':
        raise PermissionError('Internal test sending is disabled')


class SendJournal:
    def __init__(self, path):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(p, isolation_level=None, timeout=10)
        p.chmod(0o600)
        self.db.execute('PRAGMA synchronous=FULL')
        from sequence import SEQUENCE_SCHEMA
        self.db.execute(SEQUENCE_SCHEMA)
        self.db.execute('CREATE TABLE IF NOT EXISTS attempts(email TEXT PRIMARY KEY, lead_id TEXT UNIQUE, owner TEXT, message_id TEXT UNIQUE, day TEXT, state TEXT, updated_at TEXT)')

    def reserve(self, owner, lead_id, email, message_id, cap):
        if not 1 <= cap <= DAILY_CAP:
            raise ValueError('DAILY_CAP_INVALID')
        day = datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if self.db.execute("SELECT 1 FROM attempts WHERE state != 'VERIFIED' LIMIT 1").fetchone():
                raise RuntimeError('UNRESOLVED_PRIOR_ATTEMPT')
            if self.db.execute('SELECT 1 FROM attempts WHERE email=? OR lead_id=?', (email.lower(),lead_id)).fetchone():
                raise RuntimeError('DUPLICATE_RECIPIENT_OR_LEAD')
            n = self.db.execute('SELECT count(*) FROM attempts WHERE owner=? AND day=?',(owner,day)).fetchone()[0]
            if n >= cap:
                raise RuntimeError('DAILY_CAP_REACHED')
            self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?)',(email.lower(),lead_id,owner,message_id,day,'RESERVED',datetime.now(timezone.utc).isoformat()))
            self.db.execute('COMMIT')
        except Exception:
            self.db.execute('ROLLBACK'); raise

    def transition(self, email, state):
        self.db.execute('UPDATE attempts SET state=?,updated_at=? WHERE email=?',(state,datetime.now(timezone.utc).isoformat(),email.lower()))

    def close(self):
        self.db.close()


@contextmanager
def mailbox_dispatch_lock(client):
    imap = client._get_imap()
    acquired = False
    completed = False
    try:
        typ, _ = imap.create(LOCK_FOLDER)
        if typ != 'OK':
            raise RuntimeError('DISPATCH_LOCK_EXISTS: reconcile before unlocking')
        acquired = True
        yield
        completed = True
    finally:
        # A failure retains the lock; automatic stale-lock removal is unsafe.
        if acquired and completed:
            typ, _ = imap.delete(LOCK_FOLDER)
            if typ != 'OK':
                raise RuntimeError('DISPATCH_LOCK_RELEASE_UNVERIFIED')
        imap.logout()


def col_name(index):
    out = ''
    while index:
        index, n = divmod(index-1,26); out = chr(65+n)+out
    return out


def crm_write_readback(svc, spreadsheet_id, headers, row, expected):
    updates = [{'range':f'ALL_LEADS!{col_name(headers.index(k)+1)}{row}', 'values':[[v]]} for k,v in expected.items()]
    svc.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id,body={'valueInputOption':'RAW','data':updates}).execute()
    actual = svc.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id,ranges=[u['range'] for u in updates]).execute()['valueRanges']
    if len(actual) != len(updates) or any(a.get('values') != u['values'] for a,u in zip(actual,updates)):
        raise RuntimeError('CRM_READBACK_MISMATCH')


def sent_copy_readback(client, message_id, raw, recipient):
    from sales_reconciliation import addresses
    with client._get_imap() as imap:
        typ, _ = imap.select(client.cfg['sent_folder'],readonly=True)
        if typ != 'OK': raise RuntimeError('SENT_FOLDER_UNAVAILABLE')
        def lookup():
            typ, data = imap.uid('search',None,'HEADER','Message-ID',f'"{message_id}"')
            if typ != 'OK': raise RuntimeError('SENT_SEARCH_FAILED')
            return data[0].split() if data and data[0] else []
        uids = lookup()
        if not uids:
            typ, _ = imap.append(client.cfg['sent_folder'],r'(\Seen)',imaplib.Time2Internaldate(time.time()),raw)
            if typ != 'OK': raise RuntimeError('SENT_APPEND_FAILED')
            uids = lookup()
        if len(uids) != 1: raise RuntimeError('SENT_COPY_NOT_UNIQUE')
        typ, data = imap.uid('fetch',uids[0],'(BODY.PEEK[])')
        bodies=[x[1] for x in data if isinstance(x,tuple)] if typ=='OK' else []
        if len(bodies)!=1 or hashlib.sha256(bodies[0]).digest()!=hashlib.sha256(raw).digest():
            raise RuntimeError('SENT_CONTENT_READBACK_MISMATCH')
        msg=BytesParser(policy=policy.default).parsebytes(bodies[0])
        if addresses(msg.get('To'))!=[recipient] or str(msg.get('Message-ID'))!=message_id:
            raise RuntimeError('SENT_IDENTITY_READBACK_MISMATCH')
        return uids[0].decode()


def complete_delivery(client, journal, svc, spreadsheet_id, headers, row, item, raw, mid, cap):
    """Commit intent before SMTP; any later failure leaves a non-retryable attempt."""
    em=item['email']
    journal.reserve(item['owner'],item['lead_id'],em,mid,cap)
    now=datetime.now(timezone.utc).isoformat()
    crm_write_readback(svc,spreadsheet_id,headers,row,{'Send_Status':'SENDING','Last_Send_Attempt_At':now,'Outbound_ID':mid,'Sender_Account':client.cfg['email']})
    journal.transition(em,'SMTP_UNKNOWN')
    client.deliver_verified_bytes(raw,em,journal=journal)
    journal.transition(em,'SMTP_ACCEPTED')
    sent_copy_readback(client,mid,raw,em)
    journal.transition(em,'SENT_COPY_VERIFIED')
    crm_write_readback(svc,spreadsheet_id,headers,row,{'Send_Status':'sent','Send_Datum':now,'Batch_Status':'SENT_COM_VERIFIED','Internet_Message_ID':mid})
    msg=BytesParser(policy=policy.default).parsebytes(raw)
    if str(msg.get('X-HSB-Template-ID') or '').endswith('-s1'):
        # Sequenzbeleg und finaler Versandzustand teilen sich dieselbe SQLite-Transaktion.
        journal.db.execute('BEGIN IMMEDIATE')
        try:
            journal.db.execute('INSERT INTO sequence VALUES(?,?,?,?,?,?)',
                (item['lead_id'],1,item['owner'],mid,now,'VERIFIED'))
            journal.transition(em,'VERIFIED')
            journal.db.execute('COMMIT')
        except Exception:
            journal.db.execute('ROLLBACK')
            raise
    else:
        journal.transition(em,'VERIFIED')


def count_owner_attempts_today(leads, owner, today):
    senders={'JOEL':'j-cherino@hsb-boden.com','JORDI':'j-post@hsb-boden.com'}
    known=set(senders.values())|{'j-cherino@hsb-boden.de','j-post@hsb-boden.de'}
    count=0
    for other in leads:
        stamp=str(other.get('Last_Send_Attempt_At') or other.get('Send_Datum') or '').strip()
        if not stamp:continue
        try:dt=datetime.fromisoformat(stamp.replace('Z','+00:00'))
        except ValueError:raise RuntimeError('CRM_SEND_DATE_INVALID')
        if dt.tzinfo is None:
            # Old date-only records cannot affect a much later Berlin day.
            if (today-dt.date()).days>1:continue
            raise RuntimeError('CRM_SEND_TIMEZONE_UNKNOWN')
        if dt.astimezone(ZoneInfo('Europe/Berlin')).date()!=today:continue
        sender=str(other.get('Sender_Account') or '').strip().lower()
        if sender not in known:raise RuntimeError('CRM_SENDER_HISTORY_UNKNOWN')
        if sender==senders[owner]:count+=1
    return count


SENDER_BY_OWNER={'JOEL':'j-cherino@hsb-boden.com','JORDI':'j-post@hsb-boden.com'}


SMTP_POLICY=policy.SMTP.clone(max_line_length=998)
UNSUBSCRIBE_TOKEN_RE=re.compile(r'HSB-ABMELDUNG:\s*([A-Za-z0-9._-]{1,64})')


def add_list_unsubscribe(msg, owner, lead_id):
    """Genau ein kanonischer Abmelde-Header auf der ausgehenden Kopie; der IMAP-Entwurf bleibt unverändert.
    Betreff 'Abmelden' erkennt inbound_classifier als Abmeldung; das Token im Text ordnet sie dem
    ursprünglichen Lead zu, auch wenn ein anderes Postfach der Firma antwortet."""
    for name in ('List-Unsubscribe','List-Unsubscribe-Post'):
        del msg[name]
    body=quote(f'HSB-ABMELDUNG: {lead_id}')
    msg['List-Unsubscribe']=f'<mailto:{SENDER_BY_OWNER[owner]}?subject=Abmelden&body={body}>'
    return msg


def dispatch_verified(count_per_owner=25, owners=('JOEL','JORDI'), dry_run=True, cap=35, jitter_min=45, jitter_max=90):
    from com_mailbox_manager import ComMailboxClient
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    from sales_reconciliation import run_audit, assess_message, has_unreviewed_legacy_variant
    if not 1 <= count_per_owner <= cap <= DAILY_CAP or not 45 <= jitter_min <= jitter_max:
        raise ValueError('INVALID_BATCH_LIMITS')
    owners=tuple(normalize_owner(o) for o in owners)
    if any(o not in {'JOEL','JORDI'} for o in owners): raise ValueError('INVALID_OWNER')
    # Absolute durable location shared by invocations; never an ephemeral /tmp DB.
    state=Path(os.environ.get('HSB_SALES_STATE_DIR',str(Path.home()/'.local/state/hsb-sales-os')))
    if not state.is_absolute(): raise ValueError('STATE_DIR_MUST_BE_ABSOLUTE')
    if not dry_run and os.environ.get('HSB_CUSTOMER_SEND_ENABLED')!='yes':
        raise PermissionError('Customer send activation is disabled; no SMTP attempted')
    clients={o:ComMailboxClient(o) for o in {'JOEL','JORDI'}}
    @contextmanager
    def preview_lock(): yield
    with (preview_lock() if dry_run else mailbox_dispatch_lock(clients['JOEL'])):
        if not dry_run:
            from closed_loop_crm import sync_inbounds
            sync_inbounds(apply=True,include_de=True)
        output=state/'reconciliation'
        run_audit(output)
        queue=json.loads((output/'queue.json').read_text())
        drafts=json.loads((output/'drafts.json').read_text())
        selected=[];used={o:0 for o in owners}
        for item in queue:
            o=item['owner']
            if o in owners and used[o]<count_per_owner:
                selected.append(item);used[o]+=1
        if dry_run: return {'status':'DRY_RUN_COMPLETED','selected':used,'sent_counts':{o:0 for o in owners},'customer_emails_sent':0}
        svc=get_sheets_service(); journal=SendJournal(state/'outbound.sqlite3')
        sent_counts={o:0 for o in owners}
        try:
            for item in selected:
                # Re-read all permission/suppression columns immediately before reservation.
                rows=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute()['values']
                headers=rows[0]; matches=[(i,dict(zip(headers,r))) for i,r in enumerate(rows[1:],2) if r and r[0]==item['lead_id']]
                if len(matches)!=1: raise RuntimeError('LEAD_CHANGED_OR_AMBIGUOUS')
                row,lead=matches[0]
                from send_governance import enforce_domain_health, MailboxHealthStore
                from lead_quality import deliverability_flags
                # Domainweite Gesundheit und Hygiene unmittelbar vor jeder Reservierung.
                effective_cap=min(cap,enforce_domain_health(state, datetime.now(ZoneInfo('Europe/Berlin')).date(), MailboxHealthStore(clients['JOEL'])))
                lead['Deliverability_Flags']=deliverability_flags(lead,{},set())
                verdict=check_eligibility(lead)
                if not verdict.eligible: raise RuntimeError('LIVE_GATE_BLOCKED:'+','.join(verdict.reasons))
                if normalize_owner(lead['Verantwortlicher'])!=item['owner'] or lead['E-Mail'].strip().lower()!=item['email']:
                    raise RuntimeError('LIVE_IDENTITY_CHANGED')
                today=datetime.now(ZoneInfo('Europe/Berlin')).date()
                used_today=count_owner_attempts_today([dict(zip(headers,r)) for r in rows[1:]],item['owner'],today)
                if used_today>=effective_cap: raise RuntimeError('DAILY_CAP_REACHED_CRM')
                d=next(d for d in drafts if d['lead_id']==item['lead_id'] and d['sendable'])
                client=clients[item['owner']]
                with client._get_imap() as imap:
                    typ,_=imap.select(d['folder'],readonly=True)
                    validity=imap.response('UIDVALIDITY')[1]
                    if typ!='OK' or not validity or validity[0].decode()!=d['uidvalidity']: raise RuntimeError('DRAFT_UIDVALIDITY_CHANGED')
                    typ,data=imap.uid('fetch',d['uid'],'(BODY.PEEK[])')
                    rawparts=[x[1] for x in data if isinstance(x,tuple)] if typ=='OK' else []
                if len(rawparts)!=1 or hashlib.sha256(rawparts[0]).hexdigest()!=d['sha256']: raise RuntimeError('DRAFT_CHANGED')
                if assess_message(rawparts[0],item['owner'],[lead])['issues']: raise RuntimeError('DRAFT_REVALIDATION_FAILED')
                msg=BytesParser(policy=policy.default).parsebytes(rawparts[0])
                # Historical variants need explicit reconciliation; only current standard is sent.
                if has_unreviewed_legacy_variant(msg,item['owner']): raise RuntimeError('HISTORICAL_VARIANT_REQUIRES_REVIEW')
                if 'X-Unsent' in msg: del msg['X-Unsent']
                if 'Date' in msg: del msg['Date']
                msg['Date']=formatdate(localtime=False)
                add_list_unsubscribe(msg,item['owner'],item['lead_id'])
                # Lange ASCII-Header (List-Unsubscribe) nicht in RFC-2047-Wörter zerlegen, sonst erkennt kein Mailprogramm den Link.
                raw=msg.as_bytes(policy=SMTP_POLICY); mid=str(msg['Message-ID']); em=item['email']
                complete_delivery(client,journal,svc,SPREADSHEET_ID,headers,row,item,raw,mid,effective_cap)
                sent_counts[item['owner']]+=1
                if item is not selected[-1]: time.sleep(random.uniform(jitter_min,jitter_max))
        finally: journal.close()
        return {'status':'COMPLETED','sent_counts':sent_counts}
