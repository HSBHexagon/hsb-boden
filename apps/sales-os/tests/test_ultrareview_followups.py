"""Regressionen zu den Ultrareview-Befunden 4–9 auf PR #505."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from canonical_template_factory import anrede_fuer_lead
from operator_layer import crm_dashboard as cd

ENGINE = Path(__file__).resolve().parents[1] / 'engine'


# Befund 7: "Herrn", "Herr." und "Frau." waren mit dem alten Teilstring-Abgleich gültig.
@pytest.mark.parametrize('ap,expected', [
    ('Herrn Dipl.-Ing. Müller', 'Sehr geehrter Herr Dipl.-Ing. Müller,'),
    ('Herr. Müller', 'Sehr geehrter Herr Müller,'),
    ('Frau. Schulz', 'Sehr geehrte Frau Schulz,'),
    ('Herr Müller', 'Sehr geehrter Herr Müller,'),
])
def test_salutation_accepts_all_forms_of_herr_and_frau(ap, expected):
    assert anrede_fuer_lead({'Ansprechpartner': ap}) == expected


# Befund 6: sync_inbounds speichert positiv/negativ/weiterleitung (sequence.reply_actions).
def test_reply_kpis_count_statuses_written_by_inbound_sync():
    f = cd.reply_count_formula()
    for status in ('positiv', 'negativ', 'weiterleitung'):
        assert f'"{status}"' in f


# Befund 8: soft_bounce (ingest_bounces, Apps Script) und Alt-Wert "hard" zählen als Bounce.
def test_bounce_kpi_counts_every_bounce_status_value():
    rows = {r[0]: r for r in cd.dashboard_rows() if r}
    for formula in rows['Bounces'][1:4]:
        for status in ('hard_bounce', 'bounce_review', 'soft_bounce', 'hard'):
            assert f'"{status}"' in formula


# Befund 5: als Skript gestartet liegt nur operator_layer/ im Suchpfad.
def test_dashboard_script_finds_engine_modules_when_run_as_script():
    code = ('import runpy, sys; sys.argv=["crm_dashboard.py"]; '
            f'sys.path[0]={str(ENGINE / "operator_layer")!r}; '
            f'm=runpy.run_path({str(ENGINE / "operator_layer" / "crm_dashboard.py")!r}, run_name="probe"); '
            'import sync_to_google_sheet; print("ok")')
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env, cwd='/')
    assert out.returncode == 0, out.stderr[-400:]


# Befund 4: ein Token ohne Drive-Scope liefert eine verständliche CRM_AUTH-Meldung statt 403-Stacktrace.
def test_missing_drive_scope_gives_clear_auth_error(monkeypatch):
    import sync_to_google_sheet as sg
    from googleapiclient.errors import HttpError

    class Resp(dict):
        status = 403
        reason = 'insufficientPermissions'

    class About:
        def about(self): return self
        def get(self, fields): return self
        def execute(self): raise HttpError(Resp(), b'{"error": {"message": "insufficient scopes"}}')

    sg._VERIFIED_PRINCIPALS.clear()
    monkeypatch.setattr(sg, 'build', lambda *a, **k: About())
    with pytest.raises(RuntimeError, match='CRM_AUTH_SCOPE_MISSING'):
        sg.assert_hsb_principal(object(), 'scope-test')


# Befund 9: Owner am Tageslimit – seine restlichen Einträge lösen keine CRM-/IMAP-Abfragen mehr aus.
def test_owner_at_cap_skips_remaining_items_without_io(tmp_path, monkeypatch):
    import hashlib
    from contextlib import nullcontext
    from datetime import datetime
    from email.message import EmailMessage
    from types import SimpleNamespace
    from zoneinfo import ZoneInfo
    import outbound_safety as out
    import sales_reconciliation as recon
    import sync_to_google_sheet as sheets
    import com_mailbox_manager as mail
    import closed_loop_crm as inbound
    import send_governance as guard
    from test_outbound_safety_gate import _crm_lead

    today = datetime.now(ZoneInfo('Europe/Berlin')).isoformat()
    leads = [_crm_lead(**{'Lead-ID': 'L0', 'Verantwortlicher': 'Joel Cherino Diaz', 'E-Mail': 'test0@firma.invalid',
                          'Sender_Account': 'j-cherino@hsb-boden.com', 'Send_Datum': today, 'Send_Status': 'sent'})]
    leads += [_crm_lead(**{'Lead-ID': f'L{i}', 'Verantwortlicher': 'Joel Cherino Diaz', 'E-Mail': f'test{i}@firma.invalid',
                           'Sender_Account': '', 'Send_Datum': '', 'Send_Status': ''}) for i in (1, 2, 3)]
    headers = list(leads[0])
    queue, drafts = [], []
    for i in (1, 2, 3):
        msg = EmailMessage(); msg['To'] = f'test{i}@firma.invalid'; msg.set_content('x')
        queue.append({'lead_id': f'L{i}', 'owner': 'JOEL', 'email': f'test{i}@firma.invalid'})
        drafts.append({'lead_id': f'L{i}', 'sendable': True, 'folder': 'Drafts', 'uidvalidity': '7', 'uid': str(i),
                       'sha256': hashlib.sha256(msg.as_bytes()).hexdigest()})
    client = SimpleNamespace(_get_imap=lambda: (_ for _ in ()).throw(AssertionError('kein IMAP nach Limit')), cfg={})
    monkeypatch.setattr(mail, 'ComMailboxClient', lambda o: client)
    monkeypatch.setattr(out, 'mailbox_dispatch_lock', lambda c: nullcontext())
    monkeypatch.setattr(inbound, 'sync_inbounds', lambda **k: None)

    def audit(path):
        path.mkdir(parents=True, exist_ok=True)
        (path / 'queue.json').write_text(json.dumps(queue)); (path / 'drafts.json').write_text(json.dumps(drafts))
    monkeypatch.setattr(recon, 'run_audit', audit)
    reads = []
    values = SimpleNamespace(get=lambda **k: (reads.append(1), SimpleNamespace(
        execute=lambda: {'values': [headers] + [[l.get(h, '') for h in headers] for l in leads]}))[1])
    monkeypatch.setattr(sheets, 'get_sheets_service', lambda: SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values)))
    monkeypatch.setattr('lead_quality.deliverability_flags', lambda *a: [])
    monkeypatch.setattr(guard, 'enforce_domain_health', lambda *a: 1)
    monkeypatch.setattr(out, 'complete_delivery', lambda *a: (_ for _ in ()).throw(AssertionError('kein Versand')))
    monkeypatch.setenv('HSB_CUSTOMER_SEND_ENABLED', 'yes')
    monkeypatch.setenv('HSB_SALES_STATE_DIR', str(tmp_path))
    out.dispatch_verified(3, owners=('JOEL',), dry_run=False)
    assert len(reads) == 1
