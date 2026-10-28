"""Tests fuer Fit-Score, Website-Signale, Cache/robots und Tagesauswahl (offline)."""
from __future__ import annotations

import datetime
import io
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import hsb_cli
import website_signals as ws
from lead_quality import daily_selection, fit_score, segment_for


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    ws._last_request[0] = None


def test_production_with_contact_is_a():
    lead = {"Branche": "Getränke", "Ansprechpartner": "Frau Muster"}
    score, tier, _ = fit_score(lead, None)
    assert (segment_for(lead), score, tier) == ("produktion", 80, "A")


def test_production_domain_bounce_penalty():
    lead = {"Branche": "Produktion", "Ansprechpartner": "X", "Deliverability_Flags": "DOMAIN_BOUNCED_BEFORE"}
    assert fit_score(lead, None)[:2] == (60, "B")


def test_architect_with_website_quote_brauerei_is_a():
    lead = {"Branche": "Architekten", "Ansprechpartner": "Herr Bau"}
    text = "Wir planen Hallen und eine neue Brauerei für den Mittelstand."
    sig = ws.website_signals(text)
    score, tier, reasons = fit_score(lead, sig)
    assert (score, tier) == (80, "A")
    assert any("Brauerei" in r for r in reasons)


def test_architect_without_contact_positive_is_b():
    assert fit_score({"Branche": "Architekt", "Notizen": "Industriebau"}, None)[:2] == (70, "B")


def test_interior_only_is_z():
    lead = {"Branche": "Architekten", "Firma": "Innenarchitekt Müller", "Ansprechpartner": "M"}
    assert fit_score(lead, ws.website_signals("Möbel und Einrichtung"))[1] == "Z"


def test_unclear_is_c():
    score, tier, _ = fit_score({"Branche": "Architekten", "Ansprechpartner": "M"}, ws.website_signals("Willkommen"))
    assert (score, tier) == (40, "C")


def test_signals_keep_verbatim_quote():
    text = "Unser Büro   plant\nLogistik-Zentren und Gartenanlagen."
    sig = ws.website_signals(ws.html_to_text(f"<html><nav>Möbel</nav><body><script>var Labor</script>{text}</body></html>"))
    assert "logistik" in sig["positive"] and "garten" in sig["negative"]
    assert "möbel" not in sig["negative"]
    flat = ws.html_to_text(text)
    assert sig["quotes"] and all(q in flat for q in sig["quotes"])


class Resp(io.BytesIO):
    status = 200

    def __init__(self, data, ctype="text/html; charset=utf-8", url=None):
        super().__init__(data)
        self.headers = {"Content-Type": ctype}
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class FakeOpener:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def open(self, req, timeout=None):
        self.calls.append(req.full_url)
        if req.full_url not in self.pages:
            raise urllib.error.HTTPError(req.full_url, 404, "nf", None, None)
        page = self.pages[req.full_url]
        if isinstance(page, Resp):
            page._url = page._url or req.full_url
            return page
        return Resp(page, url=req.full_url)


def test_fetch_respects_robots_disallow(tmp_path):
    op = FakeOpener({"https://a.test/robots.txt": b"User-agent: *\nDisallow: /\n", "https://a.test/": b"<p>Brauerei</p>"})
    assert ws.website_text("https://a.test/", tmp_path, opener=op) is None
    assert "https://a.test/" not in op.calls
    assert not list(tmp_path.glob("*.txt"))


def test_fetch_caches_per_domain_and_rate_limits(tmp_path):
    now = [100.0]
    sleeps = []

    def clock():
        return now[0]

    def sleep(s):
        sleeps.append(s)
        now[0] += s

    op = FakeOpener({"https://www.b.test/": b"<html><body><p>Molkerei Planung</p></body></html>"})
    text = ws.website_text("https://www.b.test/", tmp_path, opener=op, clock=clock, sleep=sleep)
    assert text == "Molkerei Planung"
    assert sleeps and sleeps[0] == pytest.approx(1.0)  # robots.txt, dann Seite: 1 Anfrage/s
    assert (tmp_path / "b.test.txt").exists()
    n = len(op.calls)
    assert ws.website_text("b.test", tmp_path, opener=op, clock=clock, sleep=sleep) == text
    assert len(op.calls) == n  # Cache-Treffer ohne Netz


def test_fetch_limits_body_to_2mb(tmp_path):
    big = b"<p>" + b"a" * (3 * 1024 * 1024) + b"</p>"
    text = ws.website_text("https://c.test/", tmp_path, opener=FakeOpener({"https://c.test/": big}))
    assert len(text) <= ws.MAX_BYTES


def test_exploration_share_15_percent_deterministic_per_day():
    leads = [{"Lead-ID": f"A{i}", "Tier": "A", "Score": 80} for i in range(30)]
    leads += [{"Lead-ID": f"B{i}", "Tier": "B", "Score": 60} for i in range(30)]
    leads += [{"Lead-ID": f"C{i}", "Tier": "C", "Score": 40} for i in range(30)]
    leads += [{"Lead-ID": f"Z{i}", "Tier": "Z", "Score": 0} for i in range(5)]
    d = datetime.date(2026, 10, 27)
    sel = daily_selection(leads, 20, d)
    assert len(sel) == 20
    assert sum(l["Tier"] == "C" for l in sel) == 3
    assert sum(l["Tier"] == "A" for l in sel) == 17
    assert not any(l["Tier"] == "Z" for l in sel)
    assert sel == daily_selection(leads, 20, d)
    other = [l["Lead-ID"] for l in daily_selection(leads, 20, datetime.date(2026, 10, 28)) if l["Tier"] == "C"]
    assert other != [l["Lead-ID"] for l in sel if l["Tier"] == "C"]


class FakeSheets:
    """Minimaler Sheets-Fake: values.get / batchUpdate / batchGet auf ALL_LEADS."""

    def __init__(self, rows):
        self.rows, self.writes = rows, []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def _cell(self, ref):
        m = re.match(r"ALL_LEADS!([A-Z]+)(\d+)$", ref)
        col = 0
        for ch in m.group(1):
            col = col * 26 + ord(ch) - 64
        return col - 1, int(m.group(2)) - 1

    def get(self, spreadsheetId, range):
        return SimpleNamespace(execute=lambda: {"values": self.rows})

    def batchUpdate(self, spreadsheetId, body):
        def run():
            for u in body["data"]:
                c, r = self._cell(u["range"])
                row = self.rows[r]
                row += [""] * (c + 1 - len(row))
                row[c] = u["values"][0][0]
                self.writes.append(u["range"])
        return SimpleNamespace(execute=run)

    def batchGet(self, spreadsheetId, ranges):
        def run():
            out = []
            for ref in ranges:
                c, r = self._cell(ref)
                v = self.rows[r][c] if c < len(self.rows[r]) else ""
                out.append({"values": [[v]]} if v != "" else {})
            return {"valueRanges": out}
        return SimpleNamespace(execute=run)


def test_score_writes_only_empty_cells(tmp_path, capsys):
    header = ["Lead-ID", "Firma", "Branche", "Tier", "Ansprechpartner", "Website", "Score", "Segment"]
    rows = [header,
            ["L1", "Brau GmbH", "Getränke", "", "Frau X", "", "", ""],
            ["L2", "Bau AG", "Architekten", "B", "Herr Y", "", "", ""]]
    svc = FakeSheets(rows)
    out = tmp_path / "fit.jsonl"
    args = SimpleNamespace(apply=True)
    hsb_cli.cmd_score_leads(args, svc=svc, cache_dir=tmp_path / "cache", out_path=out)
    assert (rows[1][3], rows[1][6], rows[1][7]) == ("A", "80", "produktion")
    assert rows[2][3] == "B"  # vorhandener Tier bleibt
    assert (rows[2][6], rows[2][7]) == ("40", "architekten")
    recs = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert {r["lead_id"] for r in recs} == {"L1", "L2"}
    printed = capsys.readouterr().out
    assert "L1" not in printed and "Frau" not in printed


def test_score_dry_run_writes_nothing(tmp_path):
    rows = [["Lead-ID", "Branche", "Tier", "Score", "Segment"], ["L1", "Produktion", "", "", ""]]
    svc = FakeSheets(rows)
    hsb_cli.cmd_score_leads(SimpleNamespace(apply=False), svc=svc, cache_dir=tmp_path, out_path=tmp_path / "o.jsonl")
    assert svc.writes == [] and rows[1][2] == ""


def test_segment_unknown_or_empty_branche_is_architekten():
    assert segment_for({}) == "architekten"
    assert segment_for({"Branche": "Sonstiges"}) == "architekten"
    assert segment_for({"Branche": "Lebensmittel"}) == "produktion"


def _skip(tmp_path, domain):
    return json.loads((tmp_path / f"{domain}.skip").read_text())


def test_failures_write_skip_markers_and_block_nothing(tmp_path):
    op = FakeOpener({"https://a.test/robots.txt": b"User-agent: *\nDisallow: /\n"})
    assert ws.website_text("https://a.test/", tmp_path, opener=op) is None
    assert _skip(tmp_path, "a.test")["reason"] == "robots"
    assert ws.cached_website_text("a.test", tmp_path) is None  # Marker ist kein Text-Treffer
    n = len(op.calls)
    assert ws.website_text("https://a.test/", tmp_path, opener=op) is None
    assert len(op.calls) == n  # dauerhaft: kein erneuter Versuch
    assert ws.website_text("https://e.test/", tmp_path, opener=FakeOpener({"https://e.test/": b"<script>x</script>"})) is None
    assert _skip(tmp_path, "e.test")["reason"] == "empty"
    ws._last_request[0] = None
    assert ws.website_text("https://n.test/", tmp_path, opener=FakeOpener({})) is None  # 404
    assert _skip(tmp_path, "n.test")["reason"] == "http_4xx"


def test_non_text_content_type_is_skipped(tmp_path):
    op = FakeOpener({"https://p.test/": Resp(b"%PDF", ctype="application/pdf")})
    assert ws.website_text("https://p.test/", tmp_path, opener=op) is None
    assert _skip(tmp_path, "p.test")["reason"] == "non_text"


def test_transient_error_retried_after_ttl(tmp_path):
    class Boom:
        calls = 0

        def open(self, req, timeout=None):
            Boom.calls += 1
            raise TimeoutError("t")

    wall = [1000.0]
    assert ws.website_text("https://t.test/", tmp_path, opener=Boom(), wall=lambda: wall[0], sleep=lambda s: None) is None
    assert _skip(tmp_path, "t.test")["permanent"] is False
    assert ws.skip_state("t.test", tmp_path, lambda: wall[0] + 3600)
    assert ws.skip_state("t.test", tmp_path, lambda: wall[0] + 8 * 24 * 3600) is None


def test_fetch_websites_limit_counts_only_real_attempts(tmp_path, capsys):
    rows = [["Lead-ID", "Website"], ["1", "https://a.test/"], ["2", "https://b.test/"], ["3", "https://c.test/"]]
    op = FakeOpener({"https://a.test/robots.txt": b"User-agent: *\nDisallow: /\n",
                     "https://b.test/": b"<p>Brauerei</p>", "https://c.test/": b"<p>Halle</p>"})
    args = SimpleNamespace(limit=1)
    hsb_cli.cmd_fetch_websites(args, svc=FakeSheets(rows), cache_dir=tmp_path, opener=op)
    ws._last_request[0] = None
    hsb_cli.cmd_fetch_websites(args, svc=FakeSheets(rows), cache_dir=tmp_path, opener=op)  # a.test uebersprungen
    assert (tmp_path / "b.test.txt").exists()


def test_cross_host_redirect_is_rejected(tmp_path):
    op = FakeOpener({"https://r.test/": Resp(b"<p>Brauerei</p>", url="https://evil.test/")})
    assert ws.website_text("https://r.test/", tmp_path, opener=op) is None
    assert _skip(tmp_path, "r.test")["reason"] == "cross_host_redirect"


def test_same_host_redirect_rechecks_robots(tmp_path):
    op = FakeOpener({"https://s.test/robots.txt": b"User-agent: *\nDisallow: /privat\n",
                     "https://s.test/": Resp(b"<p>Brauerei</p>", url="https://www.s.test/privat/start")})
    assert ws.website_text("https://s.test/", tmp_path, opener=op) is None
    assert _skip(tmp_path, "s.test")["reason"] == "robots"
    op2 = FakeOpener({"https://o.test/": Resp(b"<p>Molkerei</p>", url="https://www.o.test/start")})
    assert ws.website_text("https://o.test/", tmp_path, opener=op2) == "Molkerei"


def test_robots_403_means_disallow_all(tmp_path):
    class Op(FakeOpener):
        def open(self, req, timeout=None):
            if req.full_url.endswith("/robots.txt"):
                raise urllib.error.HTTPError(req.full_url, 403, "f", None, None)
            return super().open(req, timeout)

    assert ws.website_text("https://f.test/", tmp_path, opener=Op({"https://f.test/": b"<p>x</p>"})) is None
    assert _skip(tmp_path, "f.test")["reason"] == "robots"


def test_default_opener_is_public_opener(tmp_path, monkeypatch):
    used = []
    fake = FakeOpener({"https://d.test/": b"<p>Labor</p>"})
    monkeypatch.setattr(ws, "build_public_opener", lambda: used.append(1) or fake)
    assert ws.website_text("https://d.test/", tmp_path) == "Labor"
    assert used == [1]


def test_public_opener_refuses_loopback():
    import http.server
    import threading
    import bounce_rescue_agent

    hits = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        with pytest.raises(Exception):
            bounce_rescue_agent.build_public_opener().open(
                urllib.request.Request(f"http://127.0.0.1:{srv.server_port}/"), timeout=3)
    finally:
        srv.shutdown()
        srv.server_close()
    assert hits == []


def test_slow_drip_hits_total_deadline(tmp_path):
    now = [0.0]

    class Drip(Resp):
        def read1(self, n=-1):
            now[0] += 6.0
            return b"<p>tropf</p>"

    op = FakeOpener({"https://slow.test/": Drip(b"", url="https://slow.test/")})
    assert ws.website_text("https://slow.test/", tmp_path, opener=op, clock=lambda: now[0], sleep=lambda s: None) is None
    assert _skip(tmp_path, "slow.test")["reason"] == "timeout"
    assert _skip(tmp_path, "slow.test")["permanent"] is False


def test_apply_paces_and_retries_readback_mismatch(tmp_path, monkeypatch):
    rows = [["Lead-ID", "Branche", "Tier", "Score", "Segment"], ["1", "Produktion", "", "", ""], ["2", "Produktion", "", "", ""]]
    svc = FakeSheets(rows)
    import outbound_safety
    real = outbound_safety.crm_write_readback
    fails = [1]

    def flaky(*a, **k):
        if fails[0]:
            fails[0] -= 1
            raise RuntimeError("CRM_READBACK_MISMATCH")
        return real(*a, **k)

    monkeypatch.setattr(outbound_safety, "crm_write_readback", flaky)
    sleeps = []
    hsb_cli.cmd_score_leads(SimpleNamespace(apply=True), svc=svc, cache_dir=tmp_path, out_path=tmp_path / "o.jsonl", sleep=sleeps.append)
    assert rows[2][2] == "A" or rows[2][2] == "B"
    assert 1.0 in sleeps and 2.0 in sleeps
    # nach 4 Fehlschlaegen: Abbruch
    fails[0] = 99
    rows[1][2:] = ["", "", ""]
    with pytest.raises(RuntimeError):
        hsb_cli.cmd_score_leads(SimpleNamespace(apply=True), svc=svc, cache_dir=tmp_path, out_path=tmp_path / "o.jsonl", sleep=lambda s: None)
