"""
Unit Tests fuer Cloud-Native Mailbox Reconciliation Engine (UG-03).
Prueft:
1. Dynamischen RFC 3464 DSN Bounce Parser (Statuscodes 550, 5.4.1, 5.1.0 etc.).
2. Dynamischen RFC 3834 Auto-Reply / OOO Parser.
3. Struktur & Integritaet der Cloud-Verbindungsdaten.
"""
import pytest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from reconcile_cloud_mailbox import (
    parse_rfc3464_dsn,
    parse_rfc3834_autoreply,
    CONNECTIONS,
    BOUNCE_SUBJ_RE,
    AUTO_REPLY_SUBJ_RE
)

def test_rfc3464_bounce_parsing_hard_bounces():
    subj = "Unzustellbar: Industrieböden & Säurebau – HSB Hexagon"
    body = """
    Ihre Nachricht konnte nicht zugestellt werden.
    Fehler beim Übermitteln der Nachricht: 550 5.4.1 Mailbox nicht gefunden: info@milchhuus.ch
    Diagnostic-Code: smtp; 550 5.4.1 [info@milchhuus.ch]: Recipient address rejected
    """
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is True
    assert "550 5.4.1" in reason
    assert "info@milchhuus.ch" in recips

def test_rfc3464_bounce_various_status_codes():
    cases = [
        ("Undeliverable: Offer", "Remote server returned: 550 5.1.0 Mailbox rejected target@firma.de", "550 5.1.0", "target@firma.de"),
        ("Delivery Status Notification (Failure)", "Diagnostic-Code: smtp; 550 5.7.3 Access denied for test@kunde.com", "550 5.7.3", "test@kunde.com"),
        ("Fehler bei der Zustellung: failed", "Status: 5.4.3 System unavailable bad@domain.de", "5.4.3", "bad@domain.de"),
    ]
    for subj, body, expected_code, expected_email in cases:
        is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
        assert is_bounce is True, f"Sollte als Bounce erkannt werden: {subj}"
        assert expected_code in reason, f"Erwarteter Code {expected_code} in {reason}"
        assert expected_email in recips, f"Erwartete E-Mail {expected_email} in {recips}"

def test_rfc3464_non_bounces():
    subj = "Re: Industrieböden für Ihr Unternehmen"
    body = "Vielen Dank für das Angebot. Wir prüfen das intern."
    is_bounce, reason, recips = parse_rfc3464_dsn(subj, body)
    assert is_bounce is False
    assert reason is None
    assert recips == []

def test_rfc3834_autoreply_detection():
    # Fall 1: Absender mit no-reply
    is_ar, cls = parse_rfc3834_autoreply("no-reply@darboven.com", "[Wichtig] Ihre Anfrage", "Vielen Dank")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 2: Case Number im Betreff
    is_ar, cls = parse_rfc3834_autoreply("support@becks.de", "::No Reply:: Case Number: 00531307", "Ticket erfasst")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 3: Abwesenheitsnotiz
    is_ar, cls = parse_rfc3834_autoreply("gf@kunde.de", "Automatische Antwort: Bis 20.09 außer Haus", "Ich bin im Urlaub")
    assert is_ar is True
    assert cls == "AUTO_REPLY_OOO"

    # Fall 4: Echte Antwort
    is_ar, cls = parse_rfc3834_autoreply("gf@kunde.de", "Re: Industrieböden", "Rufen Sie mich gerne morgen an.")
    assert is_ar is False
    assert cls == ""

def test_cloud_connections_structure():
    assert "JOEL" in CONNECTIONS
    assert "JORDI" in CONNECTIONS

    assert CONNECTIONS["JOEL"]["account"] == "j-cherino@hsb-boden.de"
    assert CONNECTIONS["JOEL"]["connection_id"] == "shared-office365-819bd473"

    assert CONNECTIONS["JORDI"]["account"] == "j-post@hsb-boden.de"
    assert CONNECTIONS["JORDI"]["connection_id"] == "3d152ea7ddb24e9286fe006cb9f5069b"


def test_inbound_event_row_has_message_id_in_column_f():
    import reconcile_cloud_mailbox as m
    row = m.build_inbound_event_row(
        event_id="X", msg_date="2026-09-17T00:00:00Z", mailbox="j-cherino@hsb-boden.de",
        sender="a@b.de", subject="AW", message_id="<1@b>", lead_id="HSB-1",
        classification="REPLY", stop="no", processed="PROCESSED", notes="n")
    assert row[5] == "<1@b>" and row[11] == "" and len(row) == 12
    assert row[:5] == ["X", "2026-09-17T00:00:00Z", "j-cherino@hsb-boden.de", "a@b.de", "AW"]
    assert row[6:11] == ["HSB-1", "REPLY", "no", "PROCESSED", "n"]


# --- APIHUB-Drosselung (HTTP 429), Störung 04.11.2026 im Joel-Postfach ---
import io
import urllib.error as _ue

import reconcile_cloud_mailbox as rcm


class _Resp:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self.payload


def _http_error(code, retry_after=None):
    headers = {'Retry-After': retry_after} if retry_after is not None else {}
    return _ue.HTTPError('https://apihub', code, 'throttled', headers, io.BytesIO(b'{}'))


def _fake(responses, calls):
    def urlopen(req, timeout=30):
        calls.append(req.full_url)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _Resp(item)
    return urlopen


@pytest.fixture(autouse=False)
def fresh_limiter(monkeypatch):
    monkeypatch.setattr(rcm, '_apihub_next_slot', [0.0])
    monkeypatch.setattr(rcm, 'APIHUB_MIN_INTERVAL_S', 0.0)


def test_429_honours_retry_after_then_succeeds(fresh_limiter):
    calls, sleeps = [], []
    urlopen = _fake([_http_error(429, '7'), b'{"value": [{"id": "m1"}]}'], calls)
    msgs = rcm.call_office365_api('t', 'c', 'Gesendete Elemente', urlopen=urlopen, sleep=sleeps.append, clock=lambda: 0.0)
    assert msgs == [{'id': 'm1'}] and len(calls) == 2
    assert 7.0 in sleeps


def test_429_without_retry_after_uses_bounded_exponential_backoff(fresh_limiter):
    calls, sleeps = [], []
    urlopen = _fake([_http_error(429)] * rcm.APIHUB_MAX_ATTEMPTS, calls)
    with pytest.raises(rcm.APIHubRateLimited):
        rcm.call_office365_api('t', 'c', 'Posteingang', urlopen=urlopen, sleep=sleeps.append, clock=lambda: 0.0)
    assert len(calls) == rcm.APIHUB_MAX_ATTEMPTS
    assert sleeps and all(0 < s <= rcm.APIHUB_MAX_BACKOFF_S for s in sleeps)


def test_throttling_never_triggers_english_folder_fallback(fresh_limiter, monkeypatch):
    seen = []

    def fake_call(token, conn, folder, top=50):
        seen.append(folder)
        raise rcm.APIHubRateLimited('429')
    monkeypatch.setattr(rcm, 'call_office365_api', fake_call)
    with pytest.raises(rcm.APIHubRateLimited):
        rcm.fetch_cloud_sent_messages('t', 'c')
    with pytest.raises(rcm.APIHubRateLimited):
        rcm.fetch_cloud_inbound_messages('t', 'c')
    assert seen == ['Gesendete Elemente', 'Posteingang']


def test_missing_folder_still_falls_back(fresh_limiter, monkeypatch):
    seen = []

    def fake_call(token, conn, folder, top=50):
        seen.append(folder)
        if folder == 'Gesendete Elemente':
            raise RuntimeError('Office365 API Fehler (HTTP 404)')
        return []
    monkeypatch.setattr(rcm, 'call_office365_api', fake_call)
    assert rcm.fetch_cloud_sent_messages('t', 'c') == [] and seen == ['Gesendete Elemente', 'SentItems']


def test_non_throttle_http_error_is_not_retried(fresh_limiter):
    calls = []
    urlopen = _fake([_http_error(401)], calls)
    with pytest.raises(RuntimeError, match='HTTP 401'):
        rcm.call_office365_api('t', 'c', 'Inbox', urlopen=urlopen, sleep=lambda s: None, clock=lambda: 0.0)
    assert len(calls) == 1


def test_shared_limiter_spaces_consecutive_calls(monkeypatch):
    monkeypatch.setattr(rcm, '_apihub_next_slot', [0.0])
    monkeypatch.setattr(rcm, 'APIHUB_MIN_INTERVAL_S', 1.5)
    sleeps = []
    for _ in range(3):
        rcm._wait_for_slot(clock=lambda: 10.0, sleep=sleeps.append)
    assert sleeps == [1.5, 3.0]


def test_retry_after_http_date():
    import datetime as _dt
    now = _dt.datetime(2026, 11, 4, 17, 0, 0, tzinfo=_dt.timezone.utc)
    assert rcm.retry_after_seconds('Wed, 04 Nov 2026 17:00:30 GMT', now=now) == 30.0
    assert rcm.retry_after_seconds('kaputt') is None


def test_final_throttle_still_sets_shared_cooldown(fresh_limiter):
    # Codex-Review #518: Retry-After der letzten Antwort muss auch den nächsten Aufruf bremsen.
    urlopen = _fake([_http_error(429, '1')] * (rcm.APIHUB_MAX_ATTEMPTS - 1) + [_http_error(429, '100')], [])
    with pytest.raises(rcm.APIHubRateLimited):
        rcm.call_office365_api('t', 'c', 'Gesendete Elemente', urlopen=urlopen, sleep=lambda s: None, clock=lambda: 0.0)
    sleeps = []
    rcm.call_office365_api('t', 'c', 'Posteingang', urlopen=_fake([b'{"value": []}'], []),
                           sleep=sleeps.append, clock=lambda: 0.0)
    assert sleeps == [100.0]


def test_bounce_scan_keeps_results_when_later_folder_throttled(monkeypatch):
    # Codex-Review #518: bereits gefundene Bounces dürfen bei Drosselung nicht verloren gehen.
    import ingest_bounces as ib
    seen = []

    def fake_call(token, conn, folder, top=50):
        seen.append(folder)
        if folder == 'Unzustellbar':
            return [{'id': 'b1', 'subject': 'Undeliverable: x', 'body': 'x'}]
        raise rcm.APIHubRateLimited('429')
    monkeypatch.setattr(ib, 'call_office365_api', fake_call)
    monkeypatch.setattr(ib, 'parse_rfc3464_dsn', lambda s, b: (True, '5.1.1', ['x@firma.de']))
    found = ib.scan_mailbox_for_bounces('t', 'c', 'JOEL')
    assert [f['msg_id'] for f in found] == ['b1'] and seen == ['Unzustellbar', 'Bounces']
