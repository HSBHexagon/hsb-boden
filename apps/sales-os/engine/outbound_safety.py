"""One bounded customer dispatch path. Unknown acceptance is never retried.

A message the server provably did not accept (failure before DATA or an explicit rejection) is rolled
back in the CRM and ends that mailbox's tranche cleanly (SendHalted); only an unclear outcome blocks.

An IMAP CREATE lock serializes writers across devices. A crash leaves the
empty lock folder in place deliberately; reconciliation is required to unlock.
CRM SENDING readback precedes SMTP. Sent drafts are cleaned up from IMAP drafts folder after verified delivery.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import formatdate, parsedate_to_datetime
import hashlib
import imaplib
import re
import smtplib
import json
import os
from pathlib import Path
import random
import secrets
import sqlite3
import time
from zoneinfo import ZoneInfo
from hsb_core import check_eligibility, normalize_owner
from send_governance import MAX_DAILY_CAP_PER_MAILBOX

DAILY_CAP = MAX_DAILY_CAP_PER_MAILBOX
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


# Sperrordner + Inhaber-Nachricht. Die Sperre hält keine Verbindung offen: All-Inkl trennt ungenutzte Sitzungen nach
# etwa 12 Minuten, das Lösen lief deshalb in "Connection reset by peer" und liess die Sperre stehen.
LOCK_RELEASE_ATTEMPTS = 3
# Länger als jeder GitHub-Job (240 min) und jeder Mac-Versand. Bewusst nicht per Umgebung abschaltbar.
STALE_LOCK_MIN_AGE_MIN = 270
STALE_LOCK_EPOCH_MIN = 1_600_000_000   # plausibler Unix-Zeitstempel (Sept. 2020)


def _logout_quietly(imap):
    try:
        imap.logout()
    except Exception:  # noqa: BLE001 - Abmelden ist kein Datenvorgang
        pass


def _github_run():
    """Kennung genau dieses Laufs (inkl. Wiederholung) oder '' außerhalb von GitHub Actions."""
    run_id = os.environ.get('GITHUB_RUN_ID', '').strip()
    if not run_id:
        return ''
    return f"{os.environ.get('GITHUB_WORKFLOW', '').strip()}#{run_id}/{os.environ.get('GITHUB_RUN_ATTEMPT', '1').strip()}"


def _lock_marker(token, now=time.time):
    msg = EmailMessage()
    msg['Subject'] = 'HSB Sales OS dispatch lock'
    msg['From'] = 'sales-os@hsb-boden.com'
    msg['X-HSB-Lock-Token'] = token
    msg['X-HSB-Lock-Run'] = _github_run() or 'local'
    msg['X-HSB-Lock-Started'] = str(int(now()))
    msg.set_content('Interne Sperre, keine Kundenmail.')
    return msg.as_bytes()


def _read_lock_owner(imap):
    """Inhaber aus dem gerade ausgewählten Sperrordner; None, wenn keine Inhaber-Nachricht vorliegt (Altbestand)."""
    typ, data = imap.uid('search', None, 'ALL')
    uids = data[0].split() if typ == 'OK' and data and data[0] else []
    if not uids:
        return None
    typ, data = imap.uid('fetch', uids[0].decode(), '(BODY.PEEK[])')
    parts = [x[1] for x in data or [] if isinstance(x, tuple)] if typ == 'OK' else []
    if len(parts) != 1:
        return None
    msg = BytesParser(policy=policy.default).parsebytes(parts[0])
    token = str(msg.get('X-HSB-Lock-Token') or '').strip()
    if not token:
        return None
    started = str(msg.get('X-HSB-Lock-Started') or '').strip()
    return {'token': token, 'run': str(msg.get('X-HSB-Lock-Run') or '').strip(),
            'started': int(started) if started.isdigit() else 0}


class DispatchLock:
    """Eigene Sperre: frei geben und prüfen nur über die Inhaber-Kennung (Fencing gegen fremde Freigaben)."""

    def __init__(self, client, token):
        self.client, self.token = client, token

    def _current_owner(self, imap):
        typ, _ = imap.select(LOCK_FOLDER, readonly=True)
        return _read_lock_owner(imap) if typ == 'OK' else None

    def assert_held(self):
        """Direkt vor unumkehrbaren Schritten: gehört die Sperre noch uns?"""
        imap = self.client._get_imap()
        try:
            owner = self._current_owner(imap)
        finally:
            _logout_quietly(imap)
        if not owner or owner['token'] != self.token:
            raise RuntimeError('DISPATCH_LOCK_OWNERSHIP_LOST')

    def release(self):
        """Löscht nur die eigene Sperre, jeweils über eine frische Verbindung."""
        last = None
        for _ in range(LOCK_RELEASE_ATTEMPTS):
            imap = None
            try:
                imap = self.client._get_imap()
                owner = self._current_owner(imap)
                if not owner or owner['token'] != self.token:
                    raise RuntimeError('DISPATCH_LOCK_OWNERSHIP_LOST')
                # Dovecot verweigert DELETE auf dem ausgewählten Ordner nicht zuverlässig: erst abwählen.
                imap.close()
                typ, _ = imap.delete(LOCK_FOLDER)
                if typ != 'OK':
                    raise RuntimeError('DISPATCH_LOCK_RELEASE_UNVERIFIED')
                return
            except (imaplib.IMAP4.abort, OSError) as exc:
                last = exc
            finally:
                if imap is not None:
                    _logout_quietly(imap)
        raise RuntimeError('DISPATCH_LOCK_RELEASE_UNVERIFIED') from last


@contextmanager
def mailbox_dispatch_lock(client, release_on_error=False):
    """Geräteübergreifende Sperre. Beim Versand bleibt sie nach einem Fehler stehen (SMTP-Zustand unklar).
    Entwurfs-Umstellung und Dubletten-Archiv senden nichts und setzen über Audit und Live-Abgleich wieder auf:
    sie geben die Sperre auch bei Fehlern frei (release_on_error=True)."""
    token = secrets.token_hex(16)
    imap = client._get_imap()
    try:
        typ, _ = imap.create(LOCK_FOLDER)
        if typ != 'OK':
            raise RuntimeError('DISPATCH_LOCK_EXISTS: reconcile before unlocking')
        typ, _ = imap.append(LOCK_FOLDER, None, None, _lock_marker(token))
        if typ != 'OK':
            imap.delete(LOCK_FOLDER)
            raise RuntimeError('DISPATCH_LOCK_MARKER_FAILED')
    finally:
        _logout_quietly(imap)
    lock = DispatchLock(client, token)
    completed = False
    try:
        yield lock
        completed = True
    finally:
        # Ein Fehler beim Versand behält die Sperre; automatisches Lösen wäre dort unsicher.
        if completed:
            lock.release()
        elif release_on_error:
            try:
                lock.release()
            except Exception as exc:  # noqa: BLE001 - den eigentlichen Fehler nicht überdecken
                print(f'WARNUNG: Sperre nach Fehler nicht gelöst: {exc}')


def _finished_owner_reason(owner, now):
    """Warum ist der Inhaber sicher beendet? Ohne Nachweis None: die Sperre bleibt."""
    current = _github_run()
    if owner and current and owner['run'] != 'local' and owner['run'] != current:
        same_workflow = owner['run'].split('#', 1)[0] == current.split('#', 1)[0]
        if same_workflow and owner['run'].split('#', 1)[0]:
            # Workflow-Concurrency erlaubt nur einen Lauf gleichzeitig: ein fremder Lauf desselben Workflows ist beendet.
            return 'OWNER_RUN_FINISHED'
    return None


def release_stale_lock(svc, client, spreadsheet_id, apply=False, now=time.time):
    """Hängengebliebene Versandsperre nach einem hart beendeten Lauf lösen – nur ohne unklaren Versand und nur,
    wenn der Inhaber nachweislich beendet oder die Sperre älter als jeder mögliche Lauf ist.

    Ein Versand schreibt Send_Status=SENDING vor SMTP und erst nach Sent-Readback 'sent'. Steht irgendwo noch
    SENDING, ist ein Versand unklar: dann bleibt die Sperre und es braucht einen manuellen Abgleich. Fehlendes
    SENDING allein beweist nichts, denn ein aktiver Versand steht zwischen zwei Empfängern ohne SENDING da.
    """
    rows = svc.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='ALL_LEADS!A1:BU6425').execute().get('values', [])
    if not rows or 'Send_Status' not in rows[0]:
        raise RuntimeError('CRM_HEADER_UNREADABLE')
    col = rows[0].index('Send_Status')
    sending = sum(1 for r in rows[1:] if len(r) > col and str(r[col]).strip().upper() == 'SENDING')
    if sending:
        raise RuntimeError(f'STALE_LOCK_KEPT_SEND_UNCERTAIN:{sending}')
    imap = client._get_imap()
    try:
        typ, _ = imap.select(LOCK_FOLDER, readonly=True)
        if typ != 'OK':
            return {'lock': 'NONE', 'released': False}
        validity = imap.response('UIDVALIDITY')[1]
        owner = _read_lock_owner(imap)
        imap.close()
        reason = _finished_owner_reason(owner, now)
        if not reason:
            # Inhaber-Zeit, sonst Altbestand: Dovecot vergibt UIDVALIDITY als Anlage-Zeitstempel.
            created = owner['started'] if owner and owner['started'] else 0
            if not created and validity and validity[0] and str(validity[0], 'ascii', 'ignore').isdigit():
                created = int(validity[0])
            if not (STALE_LOCK_EPOCH_MIN <= created <= now()):
                raise RuntimeError('STALE_LOCK_AGE_UNKNOWN: reconcile manually')
            age_min = (now() - created) / 60
            if age_min < STALE_LOCK_MIN_AGE_MIN:
                raise RuntimeError(f'STALE_LOCK_TOO_YOUNG:{int(age_min)}min')
            reason = 'OLDER_THAN_ANY_RUN'
        if not apply:
            return {'lock': 'PRESENT', 'released': False, 'reason': reason}
        typ, _ = imap.delete(LOCK_FOLDER)
        if typ != 'OK':
            raise RuntimeError('DISPATCH_LOCK_RELEASE_UNVERIFIED')
        return {'lock': 'PRESENT', 'released': True, 'reason': reason}
    finally:
        _logout_quietly(imap)


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


def assert_row_lead(svc, spreadsheet_id, row, lead_id):
    """Vor jedem Versand-Write: steht in dieser Zeile noch derselbe Lead? Sonst kein Write (Sortierung o. Ä.)."""
    got=svc.spreadsheets().values().get(spreadsheetId=spreadsheet_id,range=f'ALL_LEADS!A{row}').execute().get('values',[[""]])
    if str((got[0] or [""])[0]).strip()!=str(lead_id).strip():
        raise RuntimeError('CRM_ROW_MOVED: Zeile gehört nicht mehr zu diesem Lead')


_ACTIVE_BINDINGS = {}


def prepare_lead_binding(svc, spreadsheet_id, lead_id):
    """Bindung für genau diesen Lead anlegen und als eindeutig bestätigen – vor journal.reserve(),
    damit ein Bindungsfehler keinen RESERVED-Rest hinterlässt, der jeden Folgeversand sperrt."""
    import crm_bindings
    result=crm_bindings.ensure_bindings(svc, spreadsheet_id, apply=True, sleep=lambda s: None, only={lead_id})
    if any(result.get(k) for k in ('conflicts','skipped_duplicate','skipped_invalid')):
        raise RuntimeError('CRM_LEAD_BINDING_NOT_CREATED')
    binding = require_stable_crm_binding(svc, spreadsheet_id, lead_id)
    _ACTIVE_BINDINGS[(id(svc), spreadsheet_id, lead_id)] = binding
    return binding


def _send_write(svc, spreadsheet_id, headers, row, lead_id, fields):
    """Versand-Writes nur über die vorab angelegte Lead-Bindung (Developer-Metadaten), nie per Zeilennummer.
    headers/row bleiben für Test-Attrappen."""
    binding = _ACTIVE_BINDINGS.get((id(svc), spreadsheet_id, lead_id))
    if binding is not None:
        try:
            crm_write_lead_readback(svc, spreadsheet_id, lead_id, fields, binding=binding, headers=headers)
            return
        except TypeError:
            pass
    crm_write_lead_readback(svc, spreadsheet_id, lead_id, fields)


def _release_binding(svc, spreadsheet_id, lead_id):
    """Bindung nach Abschluss entfernen (Metadaten-Kapazität); Fehler hier blockieren den Versand nicht."""
    _ACTIVE_BINDINGS.pop((id(svc), spreadsheet_id, lead_id), None)
    try:
        import crm_bindings
        crm_bindings.remove_binding(svc, spreadsheet_id, lead_id)
    except Exception as exc:  # noqa: BLE001 - nur Aufräumen
        print(f'WARNUNG: Bindung {lead_id} nicht entfernt: {exc}')


class SendHalted(RuntimeError):
    """Der Versand dieses Postfachs endet geordnet: die Nachricht wurde nachweislich nicht angenommen,
    der CRM-Vorgang ist zurückgerollt, es bleibt weder SENDING noch eine offene Reservierung stehen."""

    def __init__(self, owner, reason):
        self.owner, self.reason = owner, reason
        super().__init__(f'SEND_HALTED:{owner}:{reason}')


_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_KNOWN_UNKNOWN_MARKERS = (b'previously reported as unknown', b'relay access denied')
SENT_COPY_ATTEMPTS = 3


def _transient_backend_error(exc):
    """Netzwerkfehler oder vorübergehende Antwort der Sheets-API; ein Wiederholen des Writes ist idempotent."""
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, TimeoutError, OSError)):
        return True
    return getattr(getattr(exc, 'resp', None), 'status', None) in _RETRYABLE_HTTP


def complete_delivery(client, journal, svc, spreadsheet_id, headers, row, item, raw, mid, cap):
    """Commit intent before SMTP. Only a provably unaccepted message is rolled back; an unclear SMTP
    outcome leaves a non-retryable attempt. Returns True (sent), False (recipient permanently refused)
    or raises SendHalted (not accepted, rolled back, stop this mailbox for now)."""
    from com_mailbox_manager import SmtpNotAccepted
    em=item['email']
    if os.environ.get('HSB_CRM_BINDINGS_VERIFIED')!='yes':
        raise RuntimeError('CRM_STABLE_BINDING_CANARY_REQUIRED')

    def _call(action):
        nonlocal svc
        for attempt in range(4):
            try:
                return action(svc)
            except Exception as exc:  # noqa: BLE001 - nur vorübergehende Fehler werden wiederholt
                if attempt == 3 or not _transient_backend_error(exc):
                    raise
                time.sleep(1.5 * (attempt + 1))
                try:
                    from sync_to_google_sheet import get_sheets_service
                    svc = get_sheets_service()
                except Exception:
                    pass

    _call(lambda s: assert_row_lead(s, spreadsheet_id, row, item['lead_id']))
    _call(lambda s: prepare_lead_binding(s, spreadsheet_id, item['lead_id']))
    journal.reserve(item['owner'],item['lead_id'],em,mid,cap)
    now=datetime.now(timezone.utc).isoformat()
    _call(lambda s: _send_write(s,spreadsheet_id,headers,row,item['lead_id'],{'Send_Status':'SENDING','Last_Send_Attempt_At':now,'Outbound_ID':mid,'Sender_Account':client.cfg['email']}))
    journal.transition(em,'SMTP_UNKNOWN')

    def _forget_attempt(fields):
        _call(lambda s: _send_write(s, spreadsheet_id, headers, row, item['lead_id'], fields))
        _call(lambda s: _release_binding(s, spreadsheet_id, item['lead_id']))
        journal.db.execute('DELETE FROM attempts WHERE email=?', (em.lower(),))

    def _hard_bounce(reason, note):
        _forget_attempt({'Send_Status': 'failed', 'Bounce_Status': 'hard_bounce', 'Suppressed': 'yes',
                         'Suppression_Reason': reason, 'Versandfreigabe': 'no', 'Last_Send_Attempt_At': now})
        print(f"HARD_BOUNCE {item['lead_id']}: {note}")
        return False

    def _rollback_and_halt(reason):
        # Nichts wurde angenommen: Vorzustand wiederherstellen, damit der Lead später regulär versendet wird
        # und der Versuch nicht auf das Tageslimit zählt.
        prior = item.get('prior') or {}
        _forget_attempt({'Send_Status': prior['Send_Status'] if 'Send_Status' in prior else 'drafted', 'Last_Send_Attempt_At': '',
                         'Outbound_ID': prior.get('Outbound_ID') or '', 'Sender_Account': prior.get('Sender_Account') or ''})
        print(f"NOT_ACCEPTED {item['lead_id']}: {reason} - zurückgerollt, Postfach {item['owner']} pausiert für diesen Lauf")
        raise SendHalted(item['owner'], reason)

    try:
        client.deliver_verified_bytes(raw,em,journal=journal)
    except SmtpNotAccepted as exc:
        if exc.stage == 'rcpt' and exc.permanent:
            return _hard_bounce('RECIPIENT_REFUSED', f'Recipient refused ({exc.code})')
        if exc.stage == 'data' and exc.code == 554 and any(m in exc.detail.lower() for m in _KNOWN_UNKNOWN_MARKERS):
            return _hard_bounce('PROVIDER_KNOWN_UNKNOWN', 'Provider reported recipient unknown (554 5.7.1)')
        _rollback_and_halt(exc.reason)
    except smtplib.SMTPDataError as exc:
        # Ausdrückliche Antwort des Servers auf DATA: nicht angenommen.
        if exc.smtp_code == 554 and any(m in (exc.smtp_error or b'').lower() for m in _KNOWN_UNKNOWN_MARKERS):
            return _hard_bounce('PROVIDER_KNOWN_UNKNOWN', 'Provider reported recipient unknown (554 5.7.1)')
        _rollback_and_halt(f'DATA_{exc.smtp_code}')
    except smtplib.SMTPRecipientsRefused as exc:
        codes = [code for code, _ in (exc.recipients or {}).values()]
        if codes and all(500 <= code < 600 for code in codes):
            return _hard_bounce('RECIPIENT_REFUSED', f'Recipient refused ({codes[0]})')
        # 4xx ist eine vorübergehende Ablehnung (Drosselung, Greylisting): niemals dauerhaft sperren.
        _rollback_and_halt(f'RCPT_{codes[0] if codes else "REFUSED"}')
    journal.transition(em,'SMTP_ACCEPTED')
    msg=BytesParser(policy=policy.default).parsebytes(raw)
    final_fields={'Send_Status':'sent','Send_Datum':now,'Batch_Status':'SENT_COM_VERIFIED','Internet_Message_ID':mid}
    tmpl=str(msg.get('X-HSB-Template-ID') or '').strip()
    if tmpl:
        if 'Email_Template_ID' in headers:
            final_fields['Email_Template_ID']=tmpl
        parts=tmpl.split('-')
        seg=parts[1] if len(parts)>=2 and parts[1] in ('produktion','architekten') else item.get('segment')
        if seg and 'Segment' in headers:
            final_fields['Segment']=seg
    # Die Annahme steht fest. Der Nachweis im Gesendet-Ordner ist idempotent (Suche vor Ablage) und wird über
    # frische Verbindungen wiederholt. Scheitert er endgültig, hält das CRM trotzdem die Wahrheit "gesendet" fest
    # (sonst bliebe SENDING stehen und sperrte jeden Folgelauf); der Lauf endet dann mit dem Fehler.
    copy_error=None
    for attempt in range(1, SENT_COPY_ATTEMPTS + 1):
        try:
            sent_copy_readback(client,mid,raw,em)
            copy_error=None
            break
        except Exception as exc:  # noqa: BLE001 - nach den Versuchen unverändert weitergereicht
            copy_error=exc
            if attempt < SENT_COPY_ATTEMPTS:
                time.sleep(attempt)
    if copy_error is not None:
        _call(lambda s: _send_write(s,spreadsheet_id,headers,row,item['lead_id'],dict(final_fields,Batch_Status='SENT_COM_COPY_UNVERIFIED')))
        _call(lambda s: _release_binding(s,spreadsheet_id,item['lead_id']))
        # Zustand ist vollständig bekannt (gesendet, Kopie fehlt): kein offener Versuch, der Folgeläufe sperrt.
        journal.transition(em,'VERIFIED')
        print(f"SENT_COPY_UNVERIFIED {item['lead_id']}: zugestellt, Kopie im Gesendet-Ordner nicht bestätigt")
        raise copy_error
    journal.transition(em,'SENT_COPY_VERIFIED')
    _call(lambda s: _send_write(s,spreadsheet_id,headers,row,item['lead_id'],final_fields))
    _call(lambda s: _release_binding(s,spreadsheet_id,item['lead_id']))
    if tmpl.endswith('-s1'):
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
    return True


_GERMAN_MONTHS = {name: i for i, name in enumerate(('januar', 'februar', 'märz', 'april', 'mai', 'juni', 'juli', 'august',
                                                    'september', 'oktober', 'november', 'dezember'), 1)}
_GERMAN_STAMP = re.compile(r'^\w+, (\d{1,2})\. (\w+) (\d{4}) um (\d{2}):(\d{2}):(\d{2})$')


def _parse_send_stamp(stamp):
    """ISO, Mail-Datum oder deutsches Langformat aus Altbeständen; alles andere stoppt die Tageszählung."""
    try:
        return datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    except ValueError:
        pass
    german = _GERMAN_STAMP.match(stamp)
    month = _GERMAN_MONTHS.get(german[2].lower()) if german else None
    if month:
        return datetime(int(german[3]), month, int(german[1]), int(german[4]), int(german[5]), int(german[6]))
    try:
        return parsedate_to_datetime(stamp)
    except (TypeError, ValueError):
        raise RuntimeError('CRM_SEND_DATE_INVALID') from None


def count_owner_attempts_today(leads, owner, today):
    senders={'JOEL':'j-cherino@hsb-boden.com','JORDI':'j-post@hsb-boden.com'}
    known=set(senders.values())|{'j-cherino@hsb-boden.de','j-post@hsb-boden.de'}
    count=0
    for other in leads:
        stamp=str(other.get('Last_Send_Attempt_At') or other.get('Send_Datum') or '').strip()
        if not stamp:continue
        dt=_parse_send_stamp(stamp)
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
    from canonical_template_factory import optout_mailto
    msg['List-Unsubscribe']=f'<{optout_mailto(SENDER_BY_OWNER[owner],lead_id)}>'
    return msg


SEGMENT_CODES={'p':'produktion','a':'architekten'}


def draft_segment(draft):
    """Segment eines v2-Entwurfs aus X-HSB-Template-ID, sonst aus dem Klick-Link (?s=p / ?s=a); None, wenn nicht bestimmbar."""
    from urllib.parse import urlsplit, parse_qs
    # Reparatur-Entwürfe tragen keinen Klick-Token mehr; die Vorlagen-ID nennt das Segment.
    m = re.match(r'v2-(produktion|architekten)-', str(draft.get('template_id') or ''))
    if m:
        return m.group(1)
    for url in draft.get('links') or []:
        parts=urlsplit(url)
        if parts.netloc.lower()=='www.hsb-boden.de' and parts.path.startswith('/r/'):
            code=(parse_qs(parts.query).get('s') or [''])[0]
            return SEGMENT_CODES.get(code)
    return None


def select_queue(queue, drafts, owners, count_per_owner, segments=None, variant=None):
    """Reihenfolge der Warteschlange beibehalten; optional nur Leads, deren versandbereiter Entwurf zu `segments`
    gehört und (variant='reparatur') die Reparatur-Variante trägt.
    Filtert zuerst nach Owner/Segment/Variante und dedupliziert danach Firmendomains unter den berechtigten Kandidaten."""
    if variant not in (None, 'reparatur'):
        raise ValueError('INVALID_VARIANT')
    from dedupe_guards import corporate_domain_of
    seg_by_lead={}; tid_by_lead={}; recips_by_lead={}
    for d in drafts or []:
        if d.get('sendable'):
            lid = d.get('lead_id')
            if segments or variant:
                seg_by_lead.setdefault(lid, draft_segment(d))
                tid_by_lead.setdefault(lid, str(d.get('template_id') or ''))
            if d.get('recipients'):
                recips_by_lead.setdefault(lid, d['recipients'][0])
    selected=[]; used={o:0 for o in owners}; seen_domains=set()
    for item in queue:
        o=item['owner']
        if o not in owners or used[o]>=count_per_owner:
            continue
        if segments and seg_by_lead.get(item['lead_id']) not in segments:
            continue
        if variant and f'-{variant}-' not in tid_by_lead.get(item['lead_id'], ''):
            continue
        addr = item.get('email') or recips_by_lead.get(item.get('lead_id'), '')
        dom = corporate_domain_of(addr)
        if dom:
            if dom in seen_domains:
                continue
            seen_domains.add(dom)
        selected.append(item); used[o]+=1
    return selected, used


def cleanup_sent_draft(client, folder, uid, *, lead_id='', message_id='', recipient=''):
    """Löscht den gesendeten Entwurf (und eventuelle Duplikat-Kopien) nach verifizierter Zustellung.
    Verhindert, dass Mail-Clients wie Outlook den gesendeten Thread als [Entwurf] markieren."""
    if not client or not folder:
        return
    try:
        if uid and hasattr(client, 'delete_draft_by_uid'):
            deleted = client.delete_draft_by_uid(uid, folder)
            if deleted is False:
                print(f"WARN: cleanup_sent_draft({folder}, {uid}) delete_draft_by_uid gab False zurück")
        elif uid and hasattr(client, '_get_imap'):
            with client._get_imap() as imap:
                typ, _ = imap.select(folder)
                if typ == 'OK':
                    if hasattr(imap, 'uid'):
                        res = imap.uid('store', str(uid), '+FLAGS', r'(\Deleted)')
                        if isinstance(res, tuple) and res and res[0] != 'OK':
                            print(f"WARN: cleanup_sent_draft({folder}, {uid}) STORE fehlgeschlagen: {res}")
                    if hasattr(imap, 'expunge'):
                        imap.expunge()
        if any((lead_id, message_id, recipient)) and hasattr(type(client), 'purge_drafts_by_identity'):
            client.purge_drafts_by_identity(
                lead_id=lead_id,
                message_id=message_id,
                recipient=recipient,
                folder=folder,
            )
    except Exception as exc:
        print(f"WARN: cleanup_sent_draft({folder}, {uid}) ignoriert: {exc}")


class DraftUnavailable(RuntimeError):
    """Der im Audit geprüfte Entwurf liegt nicht mehr unverändert vor."""


def _read_audited_draft(client, draft):
    """Rohfassung des geprüften Entwurfs; ein Verbindungsabbruch wird einmal über eine frische Sitzung wiederholt."""
    for attempt in range(2):
        try:
            with client._get_imap() as imap:
                typ,_=imap.select(draft['folder'],readonly=True)
                validity=imap.response('UIDVALIDITY')[1]
                if typ!='OK' or not validity or validity[0].decode()!=draft['uidvalidity']:
                    raise DraftUnavailable('DRAFT_UIDVALIDITY_CHANGED')
                typ,data=imap.uid('fetch',draft['uid'],'(BODY.PEEK[])')
                parts=[x[1] for x in data or [] if isinstance(x,tuple)] if typ=='OK' else []
            break
        except (imaplib.IMAP4.abort, OSError):
            if attempt:
                raise
            time.sleep(2)
    if len(parts)!=1 or hashlib.sha256(parts[0]).hexdigest()!=draft['sha256']:
        raise DraftUnavailable('DRAFT_CHANGED')
    return parts[0]


def dispatch_verified(count_per_owner=25, owners=('JOEL','JORDI'), dry_run=True, cap=35, jitter_min=45, jitter_max=90, segments=None, variant=None, include_de_inbound=True):
    """include_de_inbound=False nur für Läufe ohne Azure-Zugang (GitHub Actions): .de-Antwortende sind über
    .de-Forensik und CRM-Versandstatus bereits gesperrt; neue .com-Antworten werden weiterhin synchronisiert."""
    from com_mailbox_manager import ComMailboxClient, inbound_message_cache
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    from sales_reconciliation import run_audit, assess_message, has_unreviewed_legacy_variant
    min_allowed_jitter = int(os.environ.get('HSB_MIN_ALLOWED_JITTER', 0))
    effective_daily_cap = int(os.environ.get('HSB_MAX_DAILY_CAP', DAILY_CAP))
    if not 1 <= count_per_owner <= cap <= effective_daily_cap or not min_allowed_jitter <= jitter_min <= jitter_max:
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
    # Die Gesundheitsprüfung vor jeder Mail lädt innerhalb der Tranche nur neue Eingangsnachrichten nach.
    with inbound_message_cache(), (preview_lock() if dry_run else mailbox_dispatch_lock(clients['JOEL'])) as lock:
        if not dry_run:
            from closed_loop_crm import sync_inbounds
            sync_inbounds(apply=True,include_de=include_de_inbound)
        output=state/'reconciliation'
        run_audit(output)
        queue=json.loads((output/'queue.json').read_text())
        drafts=json.loads((output/'drafts.json').read_text())
        # Do not spend send slots on DNS-blocked or otherwise ineligible leads.
        # Live sends can inspect the full reconciled queue but still stop at count_per_owner actual deliveries.
        selected,used=select_queue(queue,drafts,owners,count_per_owner if dry_run else len(queue),segments,variant)
        if dry_run: return {'status':'DRY_RUN_COMPLETED','selected':used,'sent_counts':{o:0 for o in owners},'customer_emails_sent':0}
        svc=get_sheets_service(); journal=SendJournal(state/'outbound.sqlite3')
        sent_counts={o:0 for o in owners}
        capped=set()  # Owner am Tageslimit: restliche Einträge ohne Sheet-/IMAP-Abfragen überspringen.
        halted={}     # Owner, dessen SMTP eine Nachricht nachweislich nicht annahm: Rest dieses Laufs überspringen.
        skipped={}    # Grund -> Anzahl; ein einzelner Lead stoppt die Tranche nie, gesendet wird er dann nicht.
        def skip(lead_id, reason):
            skipped[reason]=skipped.get(reason,0)+1
            print(f"SKIP {lead_id}: {reason}")
        # CRM-Snapshot einmal je Tranche laden; Einzelbindungen verifizieren jede Zeile live beim Schreiben.
        rows=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute().get('values', [])
        headers=rows[0] if rows else []
        leads_list=[dict(zip(headers,r)) for r in rows[1:] if r]
        leads_by_id={l.get('Lead-ID'): (i, l) for i, l in enumerate(leads_list, 2)}
        from dedupe_guards import corporate_domain_of
        from sales_reconciliation import addresses
        session_contacted_emails = set()
        session_contacted_domains = set()
        for _row_idx, _l in leads_by_id.values():
            _st = str(_l.get('Send_Status') or '').strip().lower()
            _em = str(_l.get('E-Mail') or '').strip().lower()
            if not _em:
                continue
            if (
                _st in {'sent', 'gesendet', 'sending'}
                or str(_l.get('Send_Datum') or '').strip()
                or str(_l.get('Last_Send_Attempt_At') or '').strip()
            ):
                session_contacted_emails.add(_em)
                _dom = corporate_domain_of(_em)
                if _dom:
                    session_contacted_domains.add(_dom)
        mb_file = output / 'mailboxes.json'
        if mb_file.is_file():
            try:
                mb_data = json.loads(mb_file.read_text())
                for _mb in (mb_data.values() if isinstance(mb_data, dict) else []):
                    for _smsg in (_mb.get('sent') or []):
                        for _raw_to in (_smsg.get('to'), _smsg.get('recipients')):
                            for _addr in addresses(_raw_to if not isinstance(_raw_to, list) else ','.join(str(x) for x in _raw_to)):
                                session_contacted_emails.add(_addr)
                                _dom = corporate_domain_of(_addr)
                                if _dom:
                                    session_contacted_domains.add(_dom)
            except Exception:
                pass
        last_svc_refresh=time.monotonic()
        mx_cache={}
        sendable_draft_by_lead={}
        for _d in drafts:
            if _d.get('sendable') and _d.get('lead_id') not in sendable_draft_by_lead:
                sendable_draft_by_lead[_d['lead_id']] = _d
        try:
            for item in selected:
                if sent_counts[item['owner']] >= count_per_owner:
                    continue
                if item['owner'] in capped or item['owner'] in halted:
                    continue
                if time.monotonic()-last_svc_refresh > 1800:
                    try:
                        from sync_to_google_sheet import get_sheets_service
                        svc=get_sheets_service()
                        last_svc_refresh=time.monotonic()
                    except Exception as exc:
                        print(f"WARNUNG: Prophylaktischer Sheets-Service-Refresh: {exc}")
                match=leads_by_id.get(item['lead_id'])
                if not match:
                    skip(item['lead_id'],'LEAD_CHANGED_OR_AMBIGUOUS'); continue
                row,lead=match
                # Zurückgestellt (CRM-Tier Z) ist kein Fehler, sondern "nie senden": überspringen, Lauf läuft weiter.
                if str(lead.get('Tier') or '').strip().upper()=='Z':
                    print(f"SKIP {item['lead_id']}: TIER_Z"); continue
                from send_governance import enforce_domain_health, MailboxHealthStore, record_verified_send
                from lead_quality import deliverability_flags
                lead['Deliverability_Flags']=deliverability_flags(lead,mx_cache,set())
                verdict=check_eligibility(lead)
                # Ein einzelner gesperrter oder nicht zustellbarer Lead stoppt die Tranche nicht; gesendet wird er nie.
                if not verdict.eligible:
                    skip(item['lead_id'],','.join(r.split('(')[0].strip() for r in verdict.reasons)); continue
                if normalize_owner(lead['Verantwortlicher'])!=item['owner'] or lead['E-Mail'].strip().lower()!=item['email']:
                    skip(item['lead_id'],'LIVE_IDENTITY_CHANGED'); continue
                item_email = str(item['email'] or '').strip().lower()
                item_dom = corporate_domain_of(item_email)
                if item_email in session_contacted_emails:
                    skip(item['lead_id'], 'CORPORATE_DOMAIN_ALREADY_CONTACTED' if item_dom else 'EMAIL_ALREADY_CONTACTED'); continue
                if item_dom and item_dom in session_contacted_domains:
                    skip(item['lead_id'], 'CORPORATE_DOMAIN_ALREADY_CONTACTED'); continue
                # Domainweite Gesundheit und Hygiene unmittelbar vor jeder Reservierung.
                effective_cap=min(cap,enforce_domain_health(state, datetime.now(ZoneInfo('Europe/Berlin')).date(), MailboxHealthStore(clients['JOEL'])))
                today=datetime.now(ZoneInfo('Europe/Berlin')).date()
                used_today=count_owner_attempts_today(leads_list,item['owner'],today)
                day_str=today.isoformat()
                journal_today=journal.db.execute('SELECT count(*) FROM attempts WHERE owner=? AND day=?',(item['owner'],day_str)).fetchone()[0]
                if used_today>=effective_cap or journal_today>=effective_cap:
                    capped.add(item['owner']); continue
                d=sendable_draft_by_lead.get(item['lead_id'])
                if d is None:
                    skip(item['lead_id'],'NO_SENDABLE_DRAFT'); continue
                client=clients[item['owner']]
                # Der Entwurf kann seit dem Audit im Postfach bearbeitet, verschoben oder gelöscht worden sein.
                # Das betrifft nur diesen Empfänger: er wird übersprungen, die übrige Tranche läuft weiter.
                try:
                    rawdraft=_read_audited_draft(client,d)
                except DraftUnavailable as exc:
                    skip(item['lead_id'],str(exc)); continue
                if assess_message(rawdraft,item['owner'],[lead])['issues']:
                    skip(item['lead_id'],'DRAFT_REVALIDATION_FAILED'); continue
                msg=BytesParser(policy=policy.default).parsebytes(rawdraft)
                # Historical variants need explicit reconciliation; only current standard is sent.
                if has_unreviewed_legacy_variant(msg,item['owner']):
                    skip(item['lead_id'],'HISTORICAL_VARIANT_REQUIRES_REVIEW'); continue
                if 'X-Unsent' in msg: del msg['X-Unsent']
                if 'Date' in msg: del msg['Date']
                msg['Date']=formatdate(localtime=False)
                add_list_unsubscribe(msg,item['owner'],item['lead_id'])
                # Lange ASCII-Header (List-Unsubscribe) nicht in RFC-2047-Wörter zerlegen, sonst erkennt kein Mailprogramm den Link.
                raw=msg.as_bytes(policy=SMTP_POLICY); mid=str(msg['Message-ID']); em=item['email']
                # Fencing: wurde die Sperre inzwischen fremd gelöst, nichts mehr senden.
                if lock:
                    lock.assert_held()
                attempt=dict(item,prior={k:str(lead.get(k) or '') for k in ('Send_Status','Outbound_ID','Sender_Account')})
                try:
                    delivered = complete_delivery(client,journal,svc,SPREADSHEET_ID,headers,row,attempt,raw,mid,effective_cap)
                except SendHalted as halt:
                    halted[halt.owner]=halt.reason
                    continue
                if delivered is not False:
                    sent_counts[item['owner']]+=1
                    lead['Send_Status']='sent'
                    session_contacted_emails.add(item_email)
                    if item_dom:
                        session_contacted_domains.add(item_dom)
                    if not dry_run:
                        record_verified_send(state)
                    lead['Send_Datum']=datetime.now(timezone.utc).isoformat()
                    lead['Sender_Account']=getattr(client, 'cfg', {}).get('email') or ('j-cherino@hsb-boden.com' if item['owner']=='JOEL' else 'j-post@hsb-boden.com')
                    cleanup_sent_draft(
                        client,
                        d.get('folder'),
                        d.get('uid'),
                        lead_id=item['lead_id'],
                        message_id=d.get('message_id') or lead.get('Internet_Message_ID') or '',
                        recipient=item_email,
                    )
                    if item is not selected[-1]: time.sleep(random.uniform(jitter_min,jitter_max))
                else:
                    lead['Send_Status']='failed'
        finally: journal.close()
        return {'status':'COMPLETED','sent_counts':sent_counts,'skipped':skipped,'halted':halted}


_SHEET_IDS = {}


def _all_leads_sheet_ids(svc, spreadsheet_id):
    """sheetId von ALL_LEADS je Dienst und Tabelle einmal lesen; sie ändert sich nur beim Neuanlegen des Tabs."""
    key = (id(svc), spreadsheet_id)
    if key not in _SHEET_IDS:
        sheets = svc.spreadsheets().get(spreadsheetId=spreadsheet_id, fields='sheets.properties').execute().get('sheets', [])
        _SHEET_IDS[key] = [s['properties']['sheetId'] for s in sheets if s['properties']['title'] == 'ALL_LEADS']
    return _SHEET_IDS[key]


def require_stable_crm_binding(svc, spreadsheet_id, lead_id):
    """Vor Produktiv-Apply muss ein Sortier-Canary die stabilen Zeilenbindungen bestätigen."""
    if os.environ.get('HSB_CRM_BINDINGS_VERIFIED') != 'yes':
        raise RuntimeError('CRM_STABLE_BINDING_CANARY_REQUIRED')
    found=svc.spreadsheets().developerMetadata().search(spreadsheetId=spreadsheet_id,
        body={'dataFilters':[{'developerMetadataLookup':{'metadataKey':'hsb.lead_id',
              'metadataValue':lead_id,'locationType':'ROW','visibility':'DOCUMENT'}}]}).execute()
    entries=found.get('matchedDeveloperMetadata',[])
    if len(entries)!=1:raise RuntimeError('CRM_STABLE_LEAD_BINDING_REQUIRED')
    meta=entries[0]['developerMetadata']
    ids=_all_leads_sheet_ids(svc,spreadsheet_id)
    if len(ids)!=1 or meta.get('location',{}).get('dimensionRange',{}).get('sheetId')!=ids[0]:
        raise RuntimeError('CRM_BINDING_WRONG_SHEET')
    return {'developerMetadataLookup':{'metadataId':meta['metadataId']}}


def crm_write_lead_readback(svc, spreadsheet_id, lead_id, expected, *, binding=None, headers=None):
    """Schreibt über eine geprüfte Zeilenbindung; niemals per zwischengespeicherter Zeilennummer.

    binding/headers dürfen aus einer unmittelbar vorher geprüften Bindung bzw. dem CRM-Stand derselben Tranche
    stammen; die Identität der Zeile wird vor und nach dem Schreiben trotzdem live zurückgelesen."""
    binding=binding or require_stable_crm_binding(svc,spreadsheet_id,lead_id)
    api=svc.spreadsheets().values()
    headers=headers or api.get(spreadsheetId=spreadsheet_id,range='ALL_LEADS!A1:BU1').execute()['values'][0]
    def bound_row():
        values=api.batchGetByDataFilter(spreadsheetId=spreadsheet_id,
            body={'dataFilters':[binding],'majorDimension':'ROWS'}).execute().get('valueRanges',[])
        if len(values)!=1:raise RuntimeError('CRM_BINDING_NOT_UNIQUE')
        rows=values[0].get('valueRange',{}).get('values',[])
        if len(rows)!=1 or not rows[0] or rows[0][0]!=lead_id:
            raise RuntimeError('CRM_IDENTITY_BINDING_MISMATCH')
        return rows[0]
    bound_row()
    matrix=[None]*len(headers)
    for key,value in expected.items():matrix[headers.index(key)]=value
    result=api.batchUpdateByDataFilter(spreadsheetId=spreadsheet_id,
        body={'valueInputOption':'RAW','includeValuesInResponse':True,'data':[
            {'dataFilter':binding,'majorDimension':'ROWS','values':[matrix]}]}).execute()
    responses=result.get('responses',[])
    if len(responses)!=1 or responses[0].get('updatedRows')!=1:
        raise RuntimeError('CRM_STABLE_WRITE_NOT_UNIQUE')
    actual=bound_row()
    # Die API lässt leere Zellen am Zeilenende weg: eine fehlende Zelle ist ein leerer Wert.
    if any((actual[headers.index(k)] if headers.index(k)<len(actual) else '')!=v for k,v in expected.items()):
        raise RuntimeError('CRM_READBACK_MISMATCH')
