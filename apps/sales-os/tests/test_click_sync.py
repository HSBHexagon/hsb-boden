import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import click_sync

# Querfixture: identisch in apps/website/tests/click-redirect.test.ts
FIXTURE_SECRET = "fixture-secret"
FIXTURE_LEAD = "L-0001"
FIXTURE_TOKEN = "L-0001.e1a4bbf8b2bcf786"


class FakeKV:
    def __init__(self, data):
        self.data = data

    def list_keys(self, prefix):
        return [k for k in self.data if k.startswith(prefix)]

    def get(self, key):
        return self.data.get(key)


class FakeSheets:
    """Minimales Raster für den Tab CLICK_EVENTS."""

    def __init__(self, tab=True, rows=None, corrupt=False):
        self.tab = tab
        self.grid = [list(r) for r in (rows if rows is not None else ([click_sync.HEADER] if tab else []))]
        self.appended = []
        self.added = 0
        self.append_calls = 0
        self.corrupt = corrupt

    def spreadsheets(self):
        return self

    def get(self, **kw):
        titles = ["ALL_LEADS"] + (["CLICK_EVENTS"] if self.tab else [])
        return _Exec({"sheets": [{"properties": {"title": t}} for t in titles]})

    def values(self):
        return _Values(self)

    def batchUpdate(self, **kw):
        self.added += 1
        self.tab = True
        return _Exec({})


class _Values:
    def __init__(self, o):
        self.o = o

    def get(self, spreadsheetId, range):
        spec = range.split("!")[1]
        rows = self.o.grid
        if spec == "A:A":
            out = [[r[0]] for r in rows if r]
        else:
            m = re.match(r"A(\d+):E(\d+)", spec)
            lo, hi = int(m.group(1)), int(m.group(2))
            out = [list(r) for r in rows[lo - 1:hi]]
            # Sheets kürzt leere Endzellen
            out = [[c for c in r] for r in out]
            out = [r[: max([i + 1 for i, c in enumerate(r) if c] or [0])] for r in out]
            if self.o.corrupt and lo > 1:
                out = [r[:-1] + ["x"] if r else r for r in out]
        return _Exec({"values": out})

    def append(self, spreadsheetId, range, valueInputOption, insertDataOption, body):
        self.o.append_calls += 1
        start = len(self.o.grid) + 1
        self.o.grid.extend([list(r) for r in body["values"]])
        self.o.appended.extend(body["values"])
        end = len(self.o.grid)
        return _Exec({"updates": {"updatedRange": f"CLICK_EVENTS!A{start}:E{end}"}})


class _Exec:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


def _val(cls="human", reasons=()):
    return json.dumps({"class": cls, "reasons": list(reasons), "asn": 1, "ua_family": "chrome", "at": "2026-10-27T10:00:00.000Z"})


def test_click_token_matches_typescript_fixture():
    assert click_sync.click_token(FIXTURE_LEAD, FIXTURE_SECRET) == FIXTURE_TOKEN


def test_click_url_with_and_without_secret():
    assert click_sync.click_url(FIXTURE_LEAD, "architekten", FIXTURE_SECRET) == f"https://www.hsb-boden.de/r/{FIXTURE_TOKEN}?s=a"
    assert click_sync.click_url(FIXTURE_LEAD, "produktion", FIXTURE_SECRET).endswith("?s=p")
    plain = click_sync.click_url(FIXTURE_LEAD, "produktion", None)
    assert plain == "https://www.hsb-boden.de/flyer/?utm_source=hsb_outreach&utm_medium=email&utm_campaign=iboden_v2_produktion"
    assert FIXTURE_LEAD not in plain
    with pytest.raises(ValueError):
        click_sync.click_url(FIXTURE_LEAD, "sonstige", FIXTURE_SECRET)


def test_sync_appends_new_events_once():
    kv = FakeKV({"click:L-0001:1000": _val(), "click:invalid:2000": _val("bot", ["invalid_hmac"])})
    sheets = FakeSheets(tab=False)
    dry = click_sync.sync_clicks(False, kv_client=kv, sheets_svc=sheets)
    assert dry["new"] == 2 and dry["tab_missing"] is True
    assert sheets.appended == [] and sheets.added == 0

    first = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets)
    assert first["new"] == 2 and sheets.added == 1
    assert sheets.appended[0] == click_sync.HEADER
    assert sheets.appended[1] == ["click:L-0001:1000", "2026-10-27T10:00:00.000Z", "L-0001", "human", ""]
    assert sheets.appended[2][2:] == ["", "bot", "invalid_hmac"]

    again = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets)
    assert again["new"] == 0 and sheets.append_calls == 1


def test_sync_never_writes_bot_as_human():
    kv = FakeKV({
        "click:L-0001:1": _val("bot", ["datacenter_asn"]),
        "click:invalid:2": _val("human"),       # ungültiger Lead darf nie human werden
        "click:L-0002:3": _val("maybe"),         # unbekannte Klasse -> bot
        "click:L-0003:4": "kein json",           # unlesbar -> übersprungen
    })
    sheets = FakeSheets(tab=True)
    res = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets)
    classes = {r[0]: r[3] for r in sheets.appended}
    assert classes == {"click:L-0001:1": "bot", "click:invalid:2": "bot", "click:L-0002:3": "bot"}
    assert res["human"] == 0 and res["bot"] == 3 and res["skipped_unreadable"] == 1


def test_cli_click_sync_dry_run_prints_counts(capsys):
    import hsb_cli
    from types import SimpleNamespace
    kv = FakeKV({"click:L-0001:1000": _val()})
    hsb_cli.cmd_click_sync(SimpleNamespace(apply=False), kv_client=kv, svc=FakeSheets(tab=True))
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "dry-run" and out["new"] == 1


def test_header_and_first_rows_in_single_append():
    sheets = FakeSheets(tab=False)
    click_sync.sync_clicks(True, kv_client=FakeKV({"click:L-0001:1": _val()}), sheets_svc=sheets)
    assert sheets.append_calls == 1
    assert sheets.grid[0] == click_sync.HEADER and len(sheets.grid) == 2


def test_readback_mismatch_raises():
    sheets = FakeSheets(tab=True, corrupt=True)
    with pytest.raises(RuntimeError, match="CRM_READBACK_MISMATCH"):
        click_sync.sync_clicks(True, kv_client=FakeKV({"click:L-0001:1": _val()}), sheets_svc=sheets)


def test_existing_tab_with_wrong_header_raises_before_writing():
    sheets = FakeSheets(tab=True, rows=[["foo", "bar"]])
    with pytest.raises(RuntimeError, match="HEADER_MISMATCH"):
        click_sync.sync_clicks(True, kv_client=FakeKV({"click:L-0001:1": _val()}), sheets_svc=sheets)
    assert sheets.append_calls == 0


def test_fetch_limit_reports_remaining():
    kv = FakeKV({f"click:L-{i:04d}:1": _val() for i in range(5)})
    sheets = FakeSheets(tab=True)
    res = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets, max_fetch=3)
    assert res["new"] == 3 and res["remaining"] == 2
    res2 = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets, max_fetch=3)
    assert res2["new"] == 2 and res2["remaining"] == 0


def test_human_with_reasons_is_bot():
    sheets = FakeSheets(tab=True)
    click_sync.sync_clicks(True, kv_client=FakeKV({"click:L-0001:1": _val("human", ["ua_bot"])}), sheets_svc=sheets)
    assert sheets.appended[0][3] == "bot"


@pytest.mark.parametrize("bad", ["", "a.b", "a b", "x" * 65, "L/1"])
def test_invalid_lead_id_rejected(bad):
    with pytest.raises(ValueError):
        click_sync.click_token(bad, "s")
    with pytest.raises(ValueError):
        click_sync.click_url(bad, "produktion", "s")


def test_cloudflare_kv_get_reraises_auth_errors():
    import urllib.error

    def opener(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 403, "forbidden", {}, None)

    kv = click_sync.CloudflareKV("a", "t", "n", opener=opener)
    with pytest.raises(urllib.error.HTTPError):
        kv.get("click:L-0001:1")

    def opener404(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 404, "nf", {}, None)

    assert click_sync.CloudflareKV("a", "t", "n", opener=opener404).get("k") is None
