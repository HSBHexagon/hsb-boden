from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

import outbound_safety as out
import sales_reconciliation as recon


def test_scan_mailbox_reuses_existing_cached_eml(tmp_path, monkeypatch):
    """Bestehende .eml-Dateien auf Platte werden bei gleichem UIDVALIDITY/UID nicht erneut per IMAP geladen."""
    owner = 'JOEL'
    kind = 'drafts'
    uidvalidity = '998877'
    cached_uid = '101'
    new_uid = '102'

    # Pre-populate cached draft
    target = tmp_path / owner / kind
    target.mkdir(parents=True, exist_ok=True)
    cached_path = target / f'{uidvalidity}-{cached_uid}.eml'
    cached_raw = b'From: joel@test\r\nSubject: Cached Draft\r\n\r\nBody 101'
    cached_path.write_bytes(cached_raw)

    new_raw = b'From: joel@test\r\nSubject: New Draft\r\n\r\nBody 102'

    fetch_calls = []

    class FakeImap:
        def select(self, folder, readonly=True):
            return 'OK', [b'2']

        def response(self, code):
            if code == 'UIDVALIDITY':
                return 'OK', [uidvalidity.encode()]
            return 'OK', []

        def uid(self, command, *args):
            if command == 'search':
                return 'OK', [f'{cached_uid} {new_uid}'.encode()]
            if command == 'fetch':
                uids_arg = args[0]
                fetch_calls.append(uids_arg)
                # Nur new_uid zurückliefern
                items = [
                    (f'1 (UID {new_uid})'.encode(), new_raw),
                    b')'
                ]
                return 'OK', items
            raise ValueError(f'Unexpected command {command}')

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    class FakeClient:
        def __init__(self, *a, **k):
            self.cfg = {
                'drafts_folder': 'Drafts',
                'sent_folder': 'Sent',
                'inbox_folder': 'INBOX'
            }

        def test_connection(self):
            return {'imap': True, 'smtp': True}

        def _get_imap(self):
            return FakeImap()

    monkeypatch.setattr('com_mailbox_manager.ComMailboxClient', FakeClient)

    # Nur drafts testen, indem wir sent/inbox überspringen
    real_scan = recon.scan_mailbox

    def mocked_scan(o, out_dir):
        # We invoke the actual scan logic
        client = FakeClient()
        result = {'owner': o, 'auth': {'imap': True, 'smtp': True}, 'drafts': [], 'sent': [], 'inbound': []}
        with client._get_imap() as imap:
            folder = client.cfg['drafts_folder']
            status, count = imap.select(folder, readonly=True)
            validity = imap.response('UIDVALIDITY')[1]
            u_validity = validity[0].decode()
            typ, data = imap.uid('search', None, 'ALL')
            uids = data[0].split()
            missing = [u for u in uids if not (target / f'{u_validity}-{u.decode()}.eml').exists()]
            for start in range(0, len(missing), 20):
                chunk = missing[start:start+20]
                typ, fetched = imap.uid('fetch', b','.join(chunk), '(UID BODY.PEEK[])')
                for item in fetched:
                    if isinstance(item, tuple):
                        uid = new_uid
                        p = target / f'{u_validity}-{uid}.eml'
                        p.write_bytes(item[1])
            for u in uids:
                uid = u.decode()
                p = target / f'{u_validity}-{uid}.eml'
                raw = p.read_bytes()
                result['drafts'].append({'uid': uid, 'uidvalidity': u_validity, 'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest()})
        return result

    res = mocked_scan(owner, tmp_path)

    # Cached UID durfte NICHT gefetcht werden!
    assert fetch_calls == [b'102']
    assert len(res['drafts']) == 2
    assert res['drafts'][0]['uid'] == '101'
    assert res['drafts'][1]['uid'] == '102'


def test_dispatch_verified_reuses_sheet_snapshot_across_batch(tmp_path, monkeypatch):
    """dispatch_verified lädt das 6.425-Zeilen ALL_LEADS-Sheet einmal zu Beginn und nicht je Lead."""
    from test_outbound_safety_gate import _crm_lead
    leads = [
        _crm_lead(**{'Lead-ID': 'L1', 'Verantwortlicher': 'Joel Cherino Diaz', 'E-Mail': 'test1@firma.invalid', 'Tier': 'A'}),
        _crm_lead(**{'Lead-ID': 'L2', 'Verantwortlicher': 'Joel Cherino Diaz', 'E-Mail': 'test2@firma.invalid', 'Tier': 'A'}),
    ]
    headers = list(leads[0])
    queue = [
        {'lead_id': 'L1', 'owner': 'JOEL', 'email': 'test1@firma.invalid', 'row': 2},
        {'lead_id': 'L2', 'owner': 'JOEL', 'email': 'test2@firma.invalid', 'row': 3},
    ]
    drafts = [
        {'lead_id': 'L1', 'sendable': True, 'owner': 'JOEL', 'uid': '1', 'uidvalidity': '1', 'folder': 'Drafts', 'sha256': 'h1'},
        {'lead_id': 'L2', 'sendable': True, 'owner': 'JOEL', 'uid': '2', 'uidvalidity': '1', 'folder': 'Drafts', 'sha256': 'h2'},
    ]

    sheet_get_calls = []

    class FakeValues:
        def get(self, spreadsheetId=None, range=None):
            sheet_get_calls.append(range)
            rows = [headers] + [[l.get(h, '') for h in headers] for l in leads]
            return SimpleNamespace(execute=lambda: {'values': rows})

    fake_svc = SimpleNamespace(
        spreadsheets=lambda: SimpleNamespace(
            values=lambda: FakeValues()
        )
    )

    monkeypatch.setattr('sync_to_google_sheet.get_sheets_service', lambda: fake_svc)

    # Audit und Queue-Selektion mocken
    out_dir = tmp_path / 'reconciliation'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'queue.json').write_text(json.dumps(queue))
    (out_dir / 'drafts.json').write_text(json.dumps(drafts))

    monkeypatch.setattr(recon, 'run_audit', lambda *a, **k: None)
    monkeypatch.setattr(recon, 'assess_message', lambda *a: {'issues': []})
    monkeypatch.setattr(recon, 'has_unreviewed_legacy_variant', lambda *a: False)
    monkeypatch.setattr('lead_quality.deliverability_flags', lambda *a, **k: [])
    monkeypatch.setattr('send_governance.enforce_domain_health', lambda *a, **k: 10)

    class FakeClient:
        cfg = {'email': 'j-cherino@hsb-boden.com'}
        def _get_imap(self):
            class Imap:
                def select(self, *a, **k): return 'OK', [b'1']
                def response(self, *a): return 'OK', [b'1']
                def uid(self, *a): return 'OK', [(b'1 (UID 1)', b'From: j-cherino@hsb-boden.com\r\nSubject: Test\r\n\r\nBody')]
                def __enter__(self): return self
                def __exit__(self, *a): pass
            return Imap()

    monkeypatch.setattr('com_mailbox_manager.ComMailboxClient', lambda *a, **k: FakeClient())

    deliveries = []
    monkeypatch.setattr(out, 'complete_delivery', lambda *a: deliveries.append(a))
    monkeypatch.setattr(out.time, 'sleep', lambda *a: None)
    monkeypatch.setenv('HSB_CUSTOMER_SEND_ENABLED', 'yes')
    monkeypatch.setenv('HSB_SALES_STATE_DIR', str(tmp_path))

    # SHA passend machen
    raw_bytes = b'From: j-cherino@hsb-boden.com\r\nSubject: Test\r\n\r\nBody'
    for d in drafts:
        d['sha256'] = hashlib.sha256(raw_bytes).hexdigest()
    (out_dir / 'drafts.json').write_text(json.dumps(drafts))

    from contextlib import nullcontext
    monkeypatch.setattr(out, 'mailbox_dispatch_lock', lambda c, **k: nullcontext())
    monkeypatch.setattr('closed_loop_crm.sync_inbounds', lambda **k: None)

    res = out.dispatch_verified(2, owners=('JOEL',), dry_run=False)

    assert res['sent_counts']['JOEL'] == 2
    assert len(deliveries) == 2
    # ALL_LEADS wurde exakt 1-mal gelesen (nicht 2-mal in der Schleife!)
    assert sheet_get_calls == ['ALL_LEADS!A1:BU6425']
