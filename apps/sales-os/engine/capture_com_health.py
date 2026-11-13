"""Read-only verified .com snapshot. Encrypts the report before it leaves the runner."""
import base64
import datetime as dt
import email
import hashlib
import imaplib
import json
import os
import re
import secrets
import sys
from collections import Counter
from email import policy
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from com_mailbox_manager import ComMailboxClient
from inbound_classifier import classify_inbound_message
from lead_quality import delivery_bounce_status

UTC = dt.timezone.utc
NOW = dt.datetime.now(UTC)
START = NOW - dt.timedelta(hours=24)

def extracted_records(client, folder, full=False, history=False):
    with client._get_imap() as imap:
        typ, _ = imap.select(folder, readonly=True)
        if typ != 'OK':
            if folder == 'Unzustellbar':
                listed, boxes = imap.list('', folder)
                if listed == 'OK' and not any(boxes or []):
                    return  # A provably nonexistent archive is empty, not an IMAP failure.
            raise RuntimeError('MAILBOX_FOLDER_UNREADABLE')
        criterion = 'ALL' if full or history else 'SINCE'
        query = [criterion] if full or history else [criterion, (START-dt.timedelta(days=1)).strftime('%d-%b-%Y')]
        typ, found = imap.uid('search', None, *query)
        if typ != 'OK' or not found:
            raise RuntimeError('MAILBOX_UID_SEARCH_UNAVAILABLE')
        uids = found[0].split() if found[0] else []
        for uid in uids:
            typ, entries = imap.uid('fetch',uid,'(INTERNALDATE BODY.PEEK[])' if full else
                                    '(INTERNALDATE BODY.PEEK[HEADER.FIELDS (DATE FROM TO SUBJECT MESSAGE-ID)])')
            chunks = [
                (entry[0], entry[1])
                for entry in (entries or []) if isinstance(entry, tuple)
                and len(entry) == 2
                and isinstance(entry[0], bytes) and isinstance(entry[1], bytes)
            ] if typ == 'OK' else []
            if len(chunks) != 1:
                raise RuntimeError('MAILBOX_UID_FETCH_INCOMPLETE')
            meta, raw = chunks[0]
            match = re.search(rb'INTERNALDATE "([^"]+)"', meta)
            if not match:
                raise RuntimeError('MAILBOX_INTERNALDATE_MISSING')
            stored = dt.datetime.strptime(match.group(1).decode('ascii'),'%d-%b-%Y %H:%M:%S %z').astimezone(UTC)
            yield stored, email.message_from_bytes(raw, policy=policy.default)

def msg_body(msg):
    out=[]
    for part in msg.walk():
        kind=part.get_content_type()
        if kind=='message/delivery-status':
            out.append(str(part))
        elif kind=='text/plain':
            try:
                out.append(str(part.get_content()))
            except (UnicodeError,LookupError,ValueError):
                raise RuntimeError('MAILBOX_BODY_DECODE_FAILED')
    return '\n'.join(out)

def policy_bounce_diagnostic(msg, body, owner, stored, outcome):
    """Keep only bounded, email-redacted DSN evidence inside the encrypted artifact."""
    def scrub(value):
        return re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '[EMAIL]', str(value))[:2800]

    dsn_blocks = []
    for part in msg.walk():
        if part.get_content_type() != 'message/delivery-status':
            continue
        for block in part.get_payload() if isinstance(part.get_payload(), list) else []:
            if not hasattr(block, 'get'):
                continue
            entry = {}
            for key in ('Action', 'Status', 'Diagnostic-Code', 'Remote-MTA',
                        'Reporting-MTA', 'Final-Recipient', 'Original-Recipient'):
                value = block.get(key)
                if value:
                    entry[key.lower().replace('-', '_')] = scrub(value)[:900]
            if entry:
                dsn_blocks.append(entry)
    return {
        'owner': owner, 'imap_internaldate': stored.isoformat(),
        'classification': outcome,
        'dsn_blocks': dsn_blocks[:6],
        'sanitized_body_excerpt': scrub(body),
    }

def check_snapshot():
    seen=set()
    counts=Counter()
    latest_sent=[]
    pilot_dates=[]
    proof={}
    bounce_diagnostics=[]
    for owner in ('JOEL','JORDI'):
        client=ComMailboxClient(owner)
        inbound=list(client.fetch_inbound_messages(limit=0))
        inbound.extend(client.fetch_inbound_messages(limit=0, folder='Unzustellbar'))
        for item in inbound:
            # Use the same priority as collect_all_inbounds(), otherwise every
            # historical message with Message-ID looks newly received on send.
            mid=item.get('internet_message_id') or item.get('id')
            if not isinstance(mid,str) or not mid.strip():
                raise RuntimeError('INBOUND_CURSOR_MISSING')
            seen.add(mid.strip())
        recent_in=0
        observed_recent=set()
        for folder in (client.cfg['inbox_folder'], 'Unzustellbar'):
            for stored, msg in extracted_records(client,folder,full=True):
                if not START <= stored <= NOW:
                    continue
                # UID is folder-scoped: avoid counting a copied NDR in both folders.
                mid=str(msg.get('Message-ID') or '').strip()
                unique_id=(owner, mid or hashlib.sha256(msg.as_bytes(policy=policy.default)).hexdigest())
                if unique_id in observed_recent:
                    continue
                observed_recent.add(unique_id)
                recent_in += 1
                body=msg_body(msg)
                subject=str(msg.get('Subject',''))
                sender=str(msg.get('From',''))
                cls=classify_inbound_message(sender,subject,body)
                if cls.category=='BOUNCE':
                    outcome=delivery_bounce_status(body,cls.extracted_email)
                    kind={'hard_bounce':'hard_bounces','deferred':'deferrals_today',
                          'policy_block':'policy_bounces'}.get(outcome,'review_bounces')
                    counts[kind]+=1
                    if len(bounce_diagnostics) < 12:
                        bounce_diagnostics.append(policy_bounce_diagnostic(msg,body,owner,stored,outcome))
                if re.search(r'feedback[- ]type:\s*abuse|feedback report|spam complaint',subject+'\n'+body,re.I):
                    counts['spam_reports']+=1
        # Read the server's authoritative INTERNALDATE, never an untrusted MIME Date header.
        historic=[]
        sample=0
        for stored, msg in extracted_records(client,client.cfg['sent_folder'],history=True):
            recipients=[a.lower() for _,a in getaddresses([str(msg.get('To',''))]) if a]
            external=[a for a in recipients if a != 'cherinojoel@gmail.com'
                      and not a.endswith('@hsb-boden.com') and not a.endswith('@hsb-boden.de')]
            if not external or stored > NOW:
                continue
            historic.append(stored)
            if START <= stored <= NOW:
                sample+=1
        if not historic:
            raise RuntimeError('NO_CONFIRMED_EXTERNAL_SENT_FOR_'+owner)
        earliest=min(historic)
        pilot_dates.append(earliest.date().isoformat())
        latest_sent.append(sample)
        proof[owner]={'inbound_total':len({(it.get('internet_message_id') or it.get('id')) for it in inbound}), 'inbound_24h':recent_in,
                      'sent_24h':sample,'first_external_sent':earliest.isoformat()}
    if sum(latest_sent) > 100:
        raise RuntimeError('HEALTH_SAMPLE_OVER_100_REQUIRES_SCOPE')
    from send_governance import MailboxHealthStore
    shared_pause=MailboxHealthStore(ComMailboxClient('JOEL')).read()
    output={'checked_at':NOW.isoformat(),'first_send_date':max(pilot_dates),
            'seen_inbound_ids':sorted(seen),'sample_sent':sum(latest_sent),
            'hard_bounces':counts['hard_bounces'],'policy_bounces':counts['policy_bounces'],
            'deferrals_today':counts['deferrals_today'],'spam_reports':counts['spam_reports'],
            'review_bounces':counts['review_bounces'],
            'bounce_diagnostics':bounce_diagnostics,
            'shared_pause':shared_pause,
            'seed_dkim_pass':False,'mailboxes':proof,
            'measurement_scope':'last 24h, genuine IMAP INTERNALDATE; Inbox and Unzustellbar deduplicated; sent folder scanned'}
    return output

def encrypt(payload, pub_b64, output_path):
    pub=serialization.load_der_public_key(base64.b64decode(pub_b64,validate=True))
    if not isinstance(pub,rsa.RSAPublicKey) or pub.key_size < 2048:
        raise RuntimeError('INVALID_HEALTH_RECEIVER_PUBLIC_KEY')
    key=AESGCM.generate_key(bit_length=256)
    nonce=secrets.token_bytes(12)
    encrypted=AESGCM(key).encrypt(nonce,json.dumps(payload,sort_keys=True).encode(),None)
    wrapped=pub.encrypt(key,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                         algorithm=hashes.SHA256(),label=None))
    bundle={'v':1,'key':base64.b64encode(wrapped).decode(),
            'nonce':base64.b64encode(nonce).decode(),
            'data':base64.b64encode(encrypted).decode()}
    p=Path(output_path)
    p.write_text(json.dumps(bundle),encoding='utf-8')
    p.chmod(0o600)

if __name__=='__main__':
    data=check_snapshot()
    encrypt(data,os.environ['HSB_HEALTH_RECEIVER_PUBLIC_KEY'],sys.argv[1])
    print('COM_HEALTH_ENCRYPTED; mailbox_count=2; data retained only in encrypted artifact')
