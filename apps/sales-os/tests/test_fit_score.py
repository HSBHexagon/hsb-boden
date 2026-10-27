"""Tests fuer Fit-Score, Website-Signale, Cache/robots und Tagesauswahl (offline)."""
from __future__ import annotations

import datetime
import io
import json
import re
import sys
import urllib.error
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
        return Resp(self.pages[req.full_url])


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
