"""Versand-Robustheit: Nur ein unklarer SMTP-Ausgang darf den Versand sperren.

Nachweislich nicht angenommene Nachrichten (Fehler vor DATA, ausdrückliche Ablehnung) werden zurückgerollt,
ein einzelner veränderter Entwurf stoppt keine Tranche, und nach bestätigter Annahme bleibt im CRM nie SENDING stehen.
"""
import hashlib
import json
import smtplib
import sys
from contextlib import nullcontext
from email.message import EmailMessage
from types import SimpleNamespace

import pytest

import com_mailbox_manager as mail
import outbound_safety as out
from com_mailbox_manager import ComMailboxClient, SmtpNotAccepted
from outbound_safety import SendHalted, SendJournal, complete_delivery

HEADERS = ['Lead-ID', 'Send_Status', 'Last_Send_Attempt_At', 'Outbound_ID', 'Sender_Account', 'Send_Datum',
           'Batch_Status', 'Internet_Message_ID', 'Bounce_Status', 'Suppressed', 'Suppression_Reason', 'Versandfreigabe']
MID = '<resilience@hsb-boden.com>'
RECIPIENT = 'einkauf@firma.invalid'


def _raw():
    msg = EmailMessage()
    msg['To'] = RECIPIENT
    msg['From'] = 'j-cherino@hsb-boden.com'
    msg['Subject'] = 'Bodenreparatur'
    msg['Message-ID'] = MID
    msg.set_content('Guten Tag')
    return msg.as_bytes()


# --------------------------------------------------------------------------- SMTP-Transaktion

class FakeSMTP:
    """Skriptbare SMTP-Sitzung: `script` legt je Schritt Antwort oder Ausnahme fest."""
    script = {}
    connects = 0
    timeouts = []
    sent = []

    def __init__(self, host, port, context=None, timeout=None):
        type(self).connects += 1
        type(self).timeouts.append(timeout)
        self._step('connect', None)
        self.does_esmtp = True

    def _step(self, name, default):
        value = type(self).script.get(name, default)
        if isinstance(value, list):
            value = value.pop(0) if value else default
        if isinstance(value, BaseException):
            raise value
        return value

    def __enter__(self): return self
    def __exit__(self, *a): self._step('quit', None)
    def login(self, user, password): self._step('login', None)
    def ehlo_or_helo_if_needed(self): pass
    def has_extn(self, name): return name == 'size'
    def mail(self, sender, options=()): return self._step('mail', (250, b'ok'))
    def rcpt(self, recipient): return self._step('rcpt', (250, b'ok'))

    def data(self, raw):
        reply = self._step('data', (250, b'queued'))
        if reply[0] == 250:
            type(self).sent.append(raw)
        return reply


@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.script, FakeSMTP.connects, FakeSMTP.timeouts, FakeSMTP.sent = {}, 0, [], []
    monkeypatch.setattr(smtplib, 'SMTP_SSL', FakeSMTP)
    monkeypatch.setattr(mail.time, 'sleep', lambda *a: None)
    monkeypatch.setenv('HSB_CUSTOMER_SEND_ENABLED', 'yes')
    return FakeSMTP


@pytest.fixture
def reserved(tmp_path):
    journal = SendJournal(tmp_path / 'outbound.sqlite3')
    journal.reserve('JOEL', 'L1', RECIPIENT, MID, 10)
    journal.transition(RECIPIENT, 'SMTP_UNKNOWN')
    yield journal
    journal.close()


def test_accepted_message_is_sent_once_with_generous_timeout(smtp, reserved):
    ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert len(smtp.sent) == 1 and smtp.connects == 1
    assert smtp.timeouts == [mail.SMTP_SEND_TIMEOUT_SECONDS] and mail.SMTP_SEND_TIMEOUT_SECONDS >= 60


def test_connection_failure_is_retried_before_anything_was_transmitted(smtp, reserved):
    smtp.script = {'connect': [ConnectionResetError('reset'), TimeoutError('slow')]}
    ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert smtp.connects == 3 and len(smtp.sent) == 1


def test_unreachable_server_is_reported_as_not_accepted(smtp, reserved):
    smtp.script = {'connect': OSError('down')}
    with pytest.raises(SmtpNotAccepted) as err:
        ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert err.value.stage == 'connect' and not err.value.permanent
    assert smtp.connects == mail.SMTP_CONNECT_ATTEMPTS and not smtp.sent


@pytest.mark.parametrize('step,failure,stage,code,permanent', [
    ('login', smtplib.SMTPAuthenticationError(535, b'auth failed'), 'login', 535, True),
    ('login', smtplib.SMTPServerDisconnected('closed'), 'login', 0, False),
    ('mail', (450, b'4.7.1 rate limit'), 'mail', 450, False),
    ('rcpt', (550, b'5.1.1 user unknown'), 'rcpt', 550, True),
    ('rcpt', (451, b'4.7.1 try later'), 'rcpt', 451, False),
    ('data', smtplib.SMTPDataError(421, b'4.3.2 not now'), 'data', 421, False),
    ('data', (554, b'5.7.1 rejected'), 'data', 554, True),
])
def test_server_rejections_are_definitive_and_never_retried(smtp, reserved, step, failure, stage, code, permanent):
    smtp.script = {step: failure}
    with pytest.raises(SmtpNotAccepted) as err:
        ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert (err.value.stage, err.value.code, err.value.permanent) == (stage, code, permanent)
    assert smtp.connects == 1 and not smtp.sent
    assert RECIPIENT not in str(err.value)


def test_abort_during_content_transfer_stays_unclear(smtp, reserved):
    # Nach Beginn der Inhaltsübertragung ohne Antwort: Annahme möglich, also kein Rollback und kein zweiter Versuch.
    smtp.script = {'data': TimeoutError('no reply after DATA')}
    with pytest.raises(TimeoutError):
        ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert smtp.connects == 1


def test_failure_while_logging_out_does_not_undo_an_accepted_message(smtp, reserved):
    smtp.script = {'quit': TimeoutError('quit timed out')}
    ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert len(smtp.sent) == 1


def test_rejection_survives_a_failing_logout(smtp, reserved):
    smtp.script = {'mail': (452, b'4.5.3 too many'), 'quit': OSError('gone')}
    with pytest.raises(SmtpNotAccepted) as err:
        ComMailboxClient('JOEL').deliver_verified_bytes(_raw(), RECIPIENT, journal=reserved)
    assert (err.value.stage, err.value.code) == ('mail', 452)


# --------------------------------------------------------------------------- CRM-Vorgang um den Versand

class Sheet:
    """Zeilenbasierte Attrappe (conftest leitet Versand-Writes auf crm_write_readback um)."""

    def __init__(self):
        self.cells, self.batches, self.fail_next = {}, [], []

    def spreadsheets(self): return self
    def values(self): return self

    def batchUpdate(self, spreadsheetId, body):
        if self.fail_next:
            raise self.fail_next.pop(0)
        self.batches.append({u['range']: u['values'][0][0] for u in body['data']})
        for update in body['data']:
            self.cells[update['range']] = update['values']
        return self

    def batchGet(self, spreadsheetId, ranges):
        return SimpleNamespace(execute=lambda: {'valueRanges': [{'range': r, 'values': self.cells.get(r, [['']])} for r in ranges]})

    def execute(self): return {}

    def value(self, column, row=2):
        return self.cells[f'ALL_LEADS!{out.col_name(HEADERS.index(column) + 1)}{row}'][0][0]


def _client(failure=None):
    def deliver(raw, recipient, journal=None):
        if failure is not None:
            raise failure
    return SimpleNamespace(cfg={'email': 'j-cherino@hsb-boden.com', 'sent_folder': 'Sent'}, deliver_verified_bytes=deliver)


def _deliver(tmp_path, client, sheet, prior=None):
    journal = SendJournal(tmp_path / 'outbound.sqlite3')
    item = {'owner': 'JOEL', 'lead_id': 'L1', 'email': RECIPIENT}
    if prior is not None:
        item['prior'] = prior
    try:
        return complete_delivery(client, journal, sheet, 'sheet', HEADERS, 2, item, _raw(), MID, 10), journal
    except BaseException as exc:
        exc.journal = journal
        raise


def _attempts(journal):
    return journal.db.execute('SELECT email,state FROM attempts').fetchall()


@pytest.mark.parametrize('failure,reason', [
    (SmtpNotAccepted('connect'), 'CONNECT_UNREACHABLE'),
    (SmtpNotAccepted('login', 535, b'auth'), 'LOGIN_535'),
    (SmtpNotAccepted('mail', 450, b'rate limit'), 'MAIL_450'),
    (SmtpNotAccepted('rcpt', 451, b'try later'), 'RCPT_451'),
    (SmtpNotAccepted('data', 552, b'5.3.4 too big'), 'DATA_552'),
    (smtplib.SMTPDataError(451, b'4.7.1 deferred'), 'DATA_451'),
    (smtplib.SMTPRecipientsRefused({RECIPIENT: (450, b'greylisted')}), 'RCPT_450'),
])
def test_unaccepted_message_is_rolled_back_and_halts_the_mailbox(tmp_path, monkeypatch, failure, reason):
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    sheet = Sheet()
    prior = {'Send_Status': 'drafted', 'Outbound_ID': '<draft@hsb-boden.com>', 'Sender_Account': ''}
    with pytest.raises(SendHalted) as err:
        _deliver(tmp_path, _client(failure), sheet, prior)
    assert (err.value.owner, err.value.reason) == ('JOEL', reason)
    # Der Lead ist wieder regulär versendbar: kein SENDING, kein Versuchsdatum, keine Sperre, kein Tageszähler.
    assert sheet.value('Send_Status') == 'drafted' and sheet.value('Last_Send_Attempt_At') == ''
    assert sheet.value('Outbound_ID') == '<draft@hsb-boden.com>' and sheet.value('Sender_Account') == ''
    assert not any('Suppressed' in ' '.join(batch) or 'J2' in ' '.join(batch) for batch in sheet.batches)
    assert _attempts(err.value.journal) == []


@pytest.mark.parametrize('failure,suppression', [
    (SmtpNotAccepted('rcpt', 550, b'5.1.1 unknown user'), 'RECIPIENT_REFUSED'),
    (smtplib.SMTPRecipientsRefused({RECIPIENT: (550, b'unknown')}), 'RECIPIENT_REFUSED'),
    (SmtpNotAccepted('data', 554, b'5.7.1 recipients were previously reported as unknown'), 'PROVIDER_KNOWN_UNKNOWN'),
    (smtplib.SMTPDataError(554, b'5.7.1 Relay access denied'), 'PROVIDER_KNOWN_UNKNOWN'),
])
def test_permanent_recipient_rejection_suppresses_only_that_lead(tmp_path, failure, suppression):
    sheet = Sheet()
    delivered, journal = _deliver(tmp_path, _client(failure), sheet)
    assert delivered is False
    assert sheet.value('Send_Status') == 'failed' and sheet.value('Bounce_Status') == 'hard_bounce'
    assert sheet.value('Suppression_Reason') == suppression and sheet.value('Versandfreigabe') == 'no'
    assert _attempts(journal) == []


def test_unclear_smtp_outcome_still_blocks(tmp_path):
    sheet = Sheet()
    with pytest.raises(TimeoutError) as err:
        _deliver(tmp_path, _client(TimeoutError('possibly accepted')), sheet)
    assert sheet.value('Send_Status') == 'SENDING'
    assert _attempts(err.value.journal) == [(RECIPIENT, 'SMTP_UNKNOWN')]


def test_sent_copy_readback_is_retried_on_a_fresh_connection(tmp_path, monkeypatch):
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    calls = []
    def readback(*a):
        calls.append(1)
        if len(calls) < 3:
            raise OSError('connection reset by peer')
    monkeypatch.setattr(out, 'sent_copy_readback', readback)
    sheet = Sheet()
    delivered, journal = _deliver(tmp_path, _client(), sheet)
    assert delivered is True and len(calls) == 3
    assert sheet.value('Send_Status') == 'sent' and sheet.value('Batch_Status') == 'SENT_COM_VERIFIED'
    assert _attempts(journal) == [(RECIPIENT, 'VERIFIED')]


def test_accepted_message_never_leaves_sending_when_the_sent_copy_cannot_be_confirmed(tmp_path, monkeypatch):
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    def readback(*a): raise RuntimeError('SENT_APPEND_FAILED')
    monkeypatch.setattr(out, 'sent_copy_readback', readback)
    sheet = Sheet()
    with pytest.raises(RuntimeError, match='SENT_APPEND_FAILED') as err:
        _deliver(tmp_path, _client(), sheet)
    # Die Mail ist zugestellt: das CRM sperrt den Empfänger als gesendet, der Lauf endet trotzdem rot.
    assert sheet.value('Send_Status') == 'sent' and sheet.value('Batch_Status') == 'SENT_COM_COPY_UNVERIFIED'
    assert sheet.value('Internet_Message_ID') == MID and sheet.value('Send_Datum')
    assert _attempts(err.value.journal) == [(RECIPIENT, 'VERIFIED')]


def test_transient_sheets_api_error_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    monkeypatch.setattr(out, 'sent_copy_readback', lambda *a: '1')
    class HttpError(Exception):
        resp = SimpleNamespace(status=503)
    sheet = Sheet()
    monkeypatch.setattr('sync_to_google_sheet.get_sheets_service', lambda: sheet)
    sheet.fail_next = [HttpError('backend error')]
    delivered, _ = _deliver(tmp_path, _client(), sheet)
    assert delivered is True and sheet.value('Send_Status') == 'sent'


def test_permanent_sheets_api_error_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    class HttpError(Exception):
        resp = SimpleNamespace(status=403)
    sheet = Sheet()
    sheet.fail_next = [HttpError('forbidden'), HttpError('forbidden')]
    with pytest.raises(HttpError):
        _deliver(tmp_path, _client(), sheet)
    assert len(sheet.fail_next) == 1


def test_readback_accepts_cleared_cells_at_the_end_of_a_row():
    headers = ['Lead-ID', 'Send_Status', 'Last_Send_Attempt_At']
    stored = {'row': ['L1', 'SENDING', '2026-11-11T10:00:00+00:00']}
    class Api:
        def get(self, **k): return SimpleNamespace(execute=lambda: {'values': [headers]})
        def batchGetByDataFilter(self, **k):
            row = list(stored['row'])
            while row and row[-1] == '':
                row.pop()  # wie die Sheets-API: leere Zellen am Zeilenende fehlen in der Antwort
            return SimpleNamespace(execute=lambda: {'valueRanges': [{'valueRange': {'values': [row]}}]})
        def batchUpdateByDataFilter(self, body, **k):
            for i, value in enumerate(body['data'][0]['values'][0]):
                if value is not None:
                    stored['row'][i] = value
            return SimpleNamespace(execute=lambda: {'responses': [{'updatedRows': 1}]})
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: Api()))
    binding = {'developerMetadataLookup': {'metadataId': 1}}
    out.crm_write_lead_readback(svc, 'sheet', 'L1', {'Send_Status': 'drafted', 'Last_Send_Attempt_At': ''}, binding=binding)
    assert stored['row'] == ['L1', 'drafted', '']
    with pytest.raises(RuntimeError, match='CRM_READBACK_MISMATCH'):
        stored['row'] = ['L1', 'drafted']
        Api.batchUpdateByDataFilter = lambda self, body, **k: SimpleNamespace(execute=lambda: {'responses': [{'updatedRows': 1}]})
        out.crm_write_lead_readback(svc, 'sheet', 'L1', {'Last_Send_Attempt_At': 'x'}, binding=binding)


# --------------------------------------------------------------------------- Tranche

def _tranche(tmp_path, monkeypatch, count=3, broken=(), deliver=None):
    import closed_loop_crm as inbound
    import sales_reconciliation as recon
    import send_governance as guard
    import sync_to_google_sheet as sheets
    from test_outbound_safety_gate import _crm_lead
    leads = [_crm_lead(**{'Lead-ID': f'L{i}', 'Verantwortlicher': 'Joel Cherino Diaz', 'E-Mail': f'kontakt{i}@firma.invalid'})
             for i in range(1, count + 1)]
    headers = list(leads[0])
    raws, queue, drafts = {}, [], []
    for i, lead in enumerate(leads, 1):
        msg = EmailMessage()
        msg['To'] = lead['E-Mail']; msg['From'] = 'j-cherino@hsb-boden.com'; msg['Subject'] = 'x'
        msg['Message-ID'] = f'<{i}@hsb-boden.com>'; msg.set_content('Test')
        raws[str(i)] = msg.as_bytes()
        queue.append({'lead_id': lead['Lead-ID'], 'owner': 'JOEL', 'email': lead['E-Mail']})
        drafts.append({'lead_id': lead['Lead-ID'], 'sendable': True, 'folder': 'Drafts', 'uidvalidity': '7', 'uid': str(i),
                       'sha256': hashlib.sha256(raws[str(i)]).hexdigest()})
    for uid, kind in broken:
        if kind == 'edited':
            raws[uid] = raws[uid] + b'manuell bearbeitet'
        elif kind == 'deleted':
            raws[uid] = None

    class IMAP:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def select(self, *a, **k): return 'OK', []
        def response(self, *a): return None, [b'7']
        def uid(self, cmd, uid, *a): return 'OK', ([(b'h', raws[uid])] if raws[uid] is not None else [None])

    client = SimpleNamespace(_get_imap=lambda: IMAP(), cfg={})
    monkeypatch.setattr(mail, 'ComMailboxClient', lambda o: client)
    monkeypatch.setattr(out, 'mailbox_dispatch_lock', lambda c, **k: nullcontext())
    monkeypatch.setattr(inbound, 'sync_inbounds', lambda **k: None)

    def audit(path):
        path.mkdir(parents=True)
        (path / 'queue.json').write_text(json.dumps(queue))
        (path / 'drafts.json').write_text(json.dumps(drafts))
    monkeypatch.setattr(recon, 'run_audit', audit)
    monkeypatch.setattr(recon, 'assess_message', lambda *a: {'issues': []})
    monkeypatch.setattr(recon, 'has_unreviewed_legacy_variant', lambda *a: False)
    values = SimpleNamespace(get=lambda **k: SimpleNamespace(
        execute=lambda: {'values': [headers] + [[l.get(h, '') for h in headers] for l in leads]}))
    monkeypatch.setattr(sheets, 'get_sheets_service', lambda: SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values)))
    monkeypatch.setattr('lead_quality.deliverability_flags', lambda *a: [])
    monkeypatch.setattr(guard, 'enforce_domain_health', lambda *a: 10)
    delivered = []
    def record(*a):
        delivered.append(a[6])
        return deliver(a[6]) if deliver else True
    monkeypatch.setattr(out, 'complete_delivery', record)
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    monkeypatch.setenv('HSB_CUSTOMER_SEND_ENABLED', 'yes')
    monkeypatch.setenv('HSB_SALES_STATE_DIR', str(tmp_path))
    return out.dispatch_verified(count, owners=('JOEL',), dry_run=False), delivered


def test_edited_or_deleted_draft_skips_only_that_recipient(tmp_path, monkeypatch, capsys):
    result, delivered = _tranche(tmp_path, monkeypatch, broken=[('1', 'edited'), ('2', 'deleted')])
    assert [item['lead_id'] for item in delivered] == ['L3']
    assert result['status'] == 'COMPLETED' and result['sent_counts'] == {'JOEL': 1}
    assert result['skipped'] == {'DRAFT_CHANGED': 2} and result['halted'] == {}
    printed = capsys.readouterr().out
    assert 'SKIP L1: DRAFT_CHANGED' in printed and 'firma.invalid' not in printed


def test_delivery_receives_the_prior_crm_state_for_a_rollback(tmp_path, monkeypatch):
    _, delivered = _tranche(tmp_path, monkeypatch, count=1)
    assert set(delivered[0]['prior']) == {'Send_Status', 'Outbound_ID', 'Sender_Account'}
    assert delivered[0]['lead_id'] == 'L1' and delivered[0]['owner'] == 'JOEL'


def test_halted_mailbox_ends_the_tranche_cleanly_without_further_attempts(tmp_path, monkeypatch):
    def deliver(item):
        if item['lead_id'] == 'L2':
            raise SendHalted('JOEL', 'MAIL_450')
        return True
    result, delivered = _tranche(tmp_path, monkeypatch, deliver=deliver)
    assert [item['lead_id'] for item in delivered] == ['L1', 'L2']
    assert result == {'status': 'COMPLETED', 'sent_counts': {'JOEL': 1}, 'skipped': {}, 'halted': {'JOEL': 'MAIL_450'}}


# --------------------------------------------------------------------------- Aufrufer

def test_cli_signals_a_halted_mailbox_with_its_own_exit_code(monkeypatch, capsys):
    import types
    import hsb_cli
    fake = types.ModuleType('outbound_safety')
    fake.dispatch_verified = lambda **kw: {'status': 'COMPLETED', 'sent_counts': {'JOEL': 2}, 'halted': {'JOEL': 'MAIL_450'}}
    monkeypatch.setitem(sys.modules, 'outbound_safety', fake)
    monkeypatch.setattr(sys, 'argv', ['hsb_cli.py', 'send-batch', '--owner', 'JOEL', '--count', '5'])
    with pytest.raises(SystemExit) as err:
        hsb_cli.main()
    assert err.value.code == hsb_cli.SEND_HALTED_EXIT_CODE == 3
    assert '"JOEL": 2' in capsys.readouterr().out


def test_tranche_total_reads_the_indented_cli_result():
    from tranche_result import total_sent
    cli_output = 'SKIP L1: DRAFT_CHANGED\nNOT_ACCEPTED L9: MAIL_450 {kein JSON}\n' + json.dumps(
        {'status': 'COMPLETED', 'sent_counts': {'JOEL': 7}, 'skipped': {'DRAFT_CHANGED': 1}, 'halted': {}}, indent=2)
    assert total_sent(cli_output) == 7
    assert total_sent('Traceback ...\nRuntimeError: DOMAIN_PAUSED') == 0
    assert total_sent(json.dumps({'status': 'DRY_RUN_COMPLETED', 'sent_counts': {'JOEL': 0}}, indent=2)) == 0


def test_tranche_script_continues_with_the_second_mailbox_after_a_halt():
    from pathlib import Path
    script = (Path(__file__).resolve().parents[1] / 'bin/versand-tranche.sh').read_text(encoding='utf-8')
    assert '|| RC=$?' in script and 'if (( RC == 3 )); then HALTED=' in script
    assert 'elif (( RC != 0 )); then exit "$RC"; fi' in script
    assert script.rindex('exit 3') > script.index('total_sent=$TOTAL_SENT')
    assert 'python3 tranche_result.py' in script


def test_tranche_script_and_workflow_offer_only_counts_the_engine_accepts():
    # Die Engine lehnt mehr als MAX_DAILY_CAP_PER_MAILBOX je Postfach mit INVALID_BATCH_LIMITS ab; Skript und
    # Workflow dürfen deshalb keine höhere Anzahl anbieten oder als Tageslimit vorgeben.
    import re
    from pathlib import Path
    from send_governance import MAX_DAILY_CAP_PER_MAILBOX
    root = Path(__file__).resolve().parents[3]
    script = (root / 'apps/sales-os/bin/versand-tranche.sh').read_text(encoding='utf-8')
    workflow = (root / '.github/workflows/sales-os-safety.yml').read_text(encoding='utf-8')
    assert MAX_DAILY_CAP_PER_MAILBOX == 250
    assert int(re.search(r'COUNT <= (\d+)', script)[1]) == MAX_DAILY_CAP_PER_MAILBOX
    assert int(re.search(r'HSB_DAILY_CAP:-(\d+)', script)[1]) == MAX_DAILY_CAP_PER_MAILBOX
    assert f'Anzahl je Postfach (1-{MAX_DAILY_CAP_PER_MAILBOX})' in workflow
    with pytest.raises(ValueError, match='INVALID_BATCH_LIMITS'):
        out.dispatch_verified(count_per_owner=MAX_DAILY_CAP_PER_MAILBOX + 1, owners=('JOEL',), dry_run=True,
                              cap=MAX_DAILY_CAP_PER_MAILBOX, jitter_min=0, jitter_max=0)


# --------------------------------------------------------------------------- Gesundheitsprüfung je Mail: Durchsatz

class CountingMailbox:
    """IMAP-Attrappe je Postfach: zählt Abrufe und erlaubt neue Nachrichten zwischen zwei Prüfungen."""

    def __init__(self):
        self.folders = {'INBOX': {'validity': b'11', 'messages': {}}, 'Unzustellbar': {'validity': b'22', 'messages': {}}}
        self.fetches = 0
        self.searches = 0

    def add(self, folder, uid, message_id, body='Guten Tag'):
        msg = EmailMessage()
        msg['From'] = 'mailer-daemon@provider.invalid'; msg['Subject'] = 'Undeliverable'; msg['Message-ID'] = message_id
        msg.set_content(body)
        self.folders[folder]['messages'][str(uid).encode()] = msg.as_bytes()

    def session(self):
        box = self
        class IMAP:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def select(self, folder, readonly=True):
                self.folder = box.folders[folder]
                return 'OK', []
            def response(self, code): return code, [self.folder['validity']]
            def uid(self, verb, *args):
                if verb == 'search':
                    box.searches += 1
                    return 'OK', [b' '.join(sorted(self.folder['messages'], key=int))]
                box.fetches += 1
                return 'OK', [(b'h', self.folder['messages'][args[0]])]
        return IMAP()


def _mailbox_client(owner, box):
    client = object.__new__(ComMailboxClient)  # echte Klasse, auch wenn der Test mail.ComMailboxClient ersetzt
    client.owner, client.cfg = owner, {'inbox_folder': 'INBOX'}
    client._get_imap = box.session
    return client


def test_repeated_health_scans_download_each_message_only_once():
    box = CountingMailbox()
    for uid in range(1, 41):
        box.add('INBOX', uid, f'<in{uid}@x.invalid>')
    for uid in range(1, 61):
        box.add('Unzustellbar', uid, f'<ndr{uid}@x.invalid>')
    client = _mailbox_client('JOEL', box)

    def scan():
        return client.fetch_inbound_messages(limit=0) + client.fetch_inbound_messages(limit=0, folder='Unzustellbar')

    # Ohne Zwischenspeicher lädt jede Prüfung alles neu: so teuer war die Prüfung vor jeder einzelnen Mail.
    scan(); scan()
    assert box.fetches == 200
    box.fetches = 0
    with mail.inbound_message_cache():
        first = scan()
        for _ in range(99):
            assert scan() == first
        assert box.fetches == 100          # 100 Prüfungen, jede Nachricht genau einmal geladen
        assert box.searches >= 100 * 2 * 2  # die Liste der Nachrichten wird weiterhin jedes Mal live gelesen
    # Außerhalb des Blocks gilt wieder das alte Verhalten.
    box.fetches = 0
    scan()
    assert box.fetches == 100


def test_cached_scan_still_sees_new_removed_and_recreated_messages():
    box = CountingMailbox()
    box.add('INBOX', 1, '<a@x.invalid>'); box.add('INBOX', 2, '<b@x.invalid>')
    client = _mailbox_client('JOEL', box)
    ids = lambda: [m['internet_message_id'] for m in client.fetch_inbound_messages(limit=0)]
    with mail.inbound_message_cache():
        assert ids() == ['<a@x.invalid>', '<b@x.invalid>']
        # Neuer Bounce zwischen zwei Mails: wird vor der nächsten Mail gesehen.
        box.add('INBOX', 3, '<bounce@x.invalid>')
        assert ids() == ['<a@x.invalid>', '<b@x.invalid>', '<bounce@x.invalid>'] and box.fetches == 3
        # Verschobene Nachricht verschwindet aus dem Ergebnis, obwohl sie im Zwischenspeicher liegt.
        del box.folders['INBOX']['messages'][b'1']
        assert ids() == ['<b@x.invalid>', '<bounce@x.invalid>'] and box.fetches == 3
        # Ordner neu angelegt (neue UIDVALIDITY): gleiche UID ist eine andere Nachricht und wird neu geladen.
        box.folders['INBOX'] = {'validity': b'99', 'messages': {}}
        box.add('INBOX', 2, '<anders@x.invalid>')
        assert ids() == ['<anders@x.invalid>'] and box.fetches == 4
        # Ein Aufrufer darf das Ergebnis verändern, ohne den Zwischenspeicher zu verfälschen.
        client.fetch_inbound_messages(limit=0)[0]['body'] = 'manipuliert'
        assert client.fetch_inbound_messages(limit=0)[0]['body'].strip() == 'Guten Tag'


def test_health_check_before_each_mail_counts_a_bounce_that_arrives_mid_tranche(tmp_path, monkeypatch):
    import send_governance as guard
    boxes = {'JOEL': CountingMailbox(), 'JORDI': CountingMailbox()}
    for owner, box in boxes.items():
        for uid in range(1, 31):
            box.add('Unzustellbar', uid, f'<alt{uid}-{owner}@x.invalid>', 'Final-Recipient: rfc822;alt@firma.invalid\n550 5.1.1 user unknown')
    monkeypatch.setattr(mail, 'ComMailboxClient', lambda owner: _mailbox_client(owner, boxes[owner]))
    baseline = [f'<alt{uid}-{owner}@x.invalid>' for owner in boxes for uid in range(1, 31)]
    monkeypatch.setattr(guard, '_parse_send_health', lambda raw: {
        'seen_inbound_ids': list(baseline), 'sample_sent': 50, 'hard_bounces': 0, 'policy_bounces': 0,
        'deferrals_today': 0, 'spam_reports': 0, 'seed_dkim_pass': True})
    (tmp_path / 'send-health.json').write_text('{}')
    with mail.inbound_message_cache():
        for _ in range(20):
            assert guard.observed_health(tmp_path)['hard_bounces'] == 0
        assert sum(box.fetches for box in boxes.values()) == 60
        boxes['JORDI'].add('INBOX', 7, '<neu@x.invalid>', 'Final-Recipient: rfc822;neu@firma.invalid\n550 5.1.1 user unknown')
        stats = guard.observed_health(tmp_path)
        assert stats['hard_bounces'] + stats.get('review_bounces', 0) == 1
        assert sum(box.fetches for box in boxes.values()) == 61
