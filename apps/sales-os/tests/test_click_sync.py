import json
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
    def __init__(self, tab=True, rows=None):
        self.tab = tab
        self.rows = rows or []
        self.appended = []
        self.added = 0

    def spreadsheets(self):
        return self

    def get(self, **kw):
        titles = ["ALL_LEADS"] + (["CLICK_EVENTS"] if self.tab else [])
        return _Exec({"sheets": [{"properties": {"title": t}} for t in titles]})

    def values(self):
        return self

    def batchUpdate(self, **kw):
        self.added += 1
        self.tab = True
        return _Exec({})

    def append(self, **kw):
        self.appended.extend(kw["body"]["values"])
        return _Exec({})


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

    already = [[r[0]] for r in sheets.appended[1:]]
    sheets2 = FakeSheets(tab=True)
    sheets2.values = lambda: _ValuesWithRows(already, sheets2)
    again = click_sync.sync_clicks(True, kv_client=kv, sheets_svc=sheets2)
    assert again["new"] == 0 and sheets2.appended == []


class _ValuesWithRows:
    def __init__(self, rows, owner):
        self.rows, self.owner = rows, owner

    def get(self, **kw):
        return _Exec({"values": [["event_id"]] + self.rows})

    def append(self, **kw):
        return self.owner.append(**kw)


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
