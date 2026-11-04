"""Tests fuer Seed-Test (Auth-Results, Versandschutz) und Blocklisten-Pruefung (offline)."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import seed_test
from seed_test import blocklist_status, parse_auth_results, send_seed


GMAIL_RAW = (
    b"Authentication-Results: mx.google.com;\r\n"
    b"       dkim=pass header.i=@hsb-boden.com header.s=default header.b=abc;\r\n"
    b"       spf=pass (google.com: domain of j-cherino@hsb-boden.com designates 1.2.3.4 as permitted sender) smtp.mailfrom=j-cherino@hsb-boden.com;\r\n"
    b"       dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=hsb-boden.com\r\n"
    b"From: a@hsb-boden.com\r\nTo: seed-gmail@seedbox.test\r\nSubject: Test\r\n\r\nHallo\r\n"
)


def test_parse_gmail_auth_results_pass():
    r = parse_auth_results(GMAIL_RAW)
    assert r["spf"] == "pass"
    assert r["dkim"] == "pass"
    assert r["dmarc"] == "pass"
    assert r["dkim_domain"] == "hsb-boden.com"
    assert r["folder"] is None


def test_parse_missing_dkim():
    raw = (
        b"Authentication-Results: mx.example.net; spf=pass smtp.mailfrom=a@hsb-boden.com;"
        b" dmarc=fail header.from=hsb-boden.com\r\nSubject: x\r\n\r\nbody\r\n"
    )
    r = parse_auth_results(raw)
    assert r["spf"] == "pass"
    assert r["dkim"] is None
    assert r["dkim_domain"] is None
    assert r["dmarc"] == "fail"


class FakeResolver:
    """Beantwortet Reverse-Lookups aus einer Tabelle; unbekannt = NXDOMAIN."""

    def __init__(self, answers):
        self.answers = answers

    def __call__(self, host):
        if host in self.answers:
            return self.answers[host]
        raise socket.gaierror(8, "NXDOMAIN")


def _ok_zone_answers(zone):
    return {f"2.0.0.127.{zone}": "127.0.0.2"}


def test_blocklist_clean_and_listed():
    answers = {}
    for z in seed_test.BLOCKLIST_ZONES.values():
        answers.update(_ok_zone_answers(z))
    answers["17.130.13.85.bl.spamcop.net"] = "127.0.0.2"
    res = blocklist_status("85.13.130.17", resolver=FakeResolver(answers))
    assert res["SpamCop"] == "listed"
    assert res["Barracuda"] == "clean"
    assert set(res) == set(seed_test.BLOCKLIST_ZONES)


def test_blocklist_testentry_failure_is_check_failed():
    answers = {}
    for name, z in seed_test.BLOCKLIST_ZONES.items():
        if name != "Barracuda":
            answers.update(_ok_zone_answers(z))
    # Barracuda: Testeintrag nicht gelistet; Abfrage selbst wuerde "clean" ergeben
    res = blocklist_status("85.13.130.17", resolver=FakeResolver(answers))
    assert res["Barracuda"] == "check_failed"
    assert res["SpamCop"] == "clean"


def test_blocklist_refusal_answer_is_check_failed():
    answers = {}
    for z in seed_test.BLOCKLIST_ZONES.values():
        answers.update(_ok_zone_answers(z))
    answers["17.130.13.85.psbl.surriel.com"] = "127.255.255.254"
    res = blocklist_status("85.13.130.17", resolver=FakeResolver(answers))
    assert res["PSBL"] == "check_failed"


class FakeClient:
    def __init__(self):
        self.sent = []

    def send_message(self, **kw):
        self.sent.append(kw)
        return True, "<id@x>"


def _seed_file(tmp_path):
    p = tmp_path / "seed_inboxes.json"
    p.write_text(json.dumps([{"provider": "gmail", "address": "seed-gmail@seedbox.test", "imap": False}]))
    return p


def test_seed_send_refuses_non_seed_recipient(tmp_path, monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    client = FakeClient()
    with pytest.raises(PermissionError):
        send_seed(client, _seed_file(tmp_path), ["kunde@firma.de"])
    assert client.sent == []


def test_seed_send_requires_internal_flag(tmp_path, monkeypatch):
    monkeypatch.delenv("HSB_INTERNAL_TEST_SEND_ENABLED", raising=False)
    client = FakeClient()
    with pytest.raises(PermissionError):
        send_seed(client, _seed_file(tmp_path), ["seed-gmail@seedbox.test"])
    assert client.sent == []


def test_seed_send_sends_plain_text_with_token(tmp_path, monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    client = FakeClient()
    token, results = send_seed(client, _seed_file(tmp_path), None)
    assert len(client.sent) == 1
    kw = client.sent[0]
    assert token in kw["subject"]
    assert kw["to_email"] == "seed-gmail@seedbox.test"
    assert kw["body_plain"]
    assert kw["extra_allowed_recipients"] == {"seed-gmail@seedbox.test"}
    assert results[0]["address"] == "seed-gmail@seedbox.test"


def test_print_checklist(tmp_path, capsys):
    seed_test.print_checklist(json.loads(_seed_file(tmp_path).read_text()), "HSB-SEED-abc")
    out = capsys.readouterr().out
    assert "HSB-SEED-abc" in out and "gmail" in out and "Authentication-Results" in out


def test_blocklist_testentry_in_refusal_range_is_check_failed():
    answers = {}
    for z in seed_test.BLOCKLIST_ZONES.values():
        answers.update(_ok_zone_answers(z))
    answers["2.0.0.127.bl.mailspike.net"] = "127.255.255.254"
    res = blocklist_status("85.13.130.17", resolver=FakeResolver(answers))
    assert res["Mailspike"] == "check_failed"


def test_blocklist_wildcard_zone_is_check_failed():
    answers = {}
    for z in seed_test.BLOCKLIST_ZONES.values():
        answers.update(_ok_zone_answers(z))
    answers["1.0.0.127.bl.spamcop.net"] = "127.0.0.2"
    res = blocklist_status("85.13.130.17", resolver=FakeResolver(answers))
    assert res["SpamCop"] == "check_failed"


def test_seed_send_empty_targets_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    p = tmp_path / "s.json"
    p.write_text("[]")
    with pytest.raises(ValueError):
        send_seed(FakeClient(), p, None)


def test_seed_list_rejects_example_addresses(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps([{"provider": "gmail", "address": "seed-gmail@example.com"}]))
    with pytest.raises(ValueError):
        seed_test.load_seed_inboxes(p)


def _args(**kw):
    import argparse
    base = dict(owner="JOEL", to=None, seed_file=None, raw_file=None, token=None)
    base.update(kw)
    return argparse.Namespace(**base)


def test_cmd_seed_send_with_to_filter(tmp_path, monkeypatch, capsys):
    import hsb_cli
    monkeypatch.setenv("HSB_INTERNAL_TEST_SEND_ENABLED", "yes")
    p = tmp_path / "s.json"
    p.write_text(json.dumps([
        {"provider": "gmail", "address": "seed-gmail@seedbox.test"},
        {"provider": "gmx", "address": "seed-gmx@seedbox.test"}]))
    client = FakeClient()
    hsb_cli.cmd_seed_send(_args(seed_file=str(p), to=["seed-gmx@seedbox.test"]), client=client)
    assert [k["to_email"] for k in client.sent] == ["seed-gmx@seedbox.test"]
    assert "Seed-Kennung: HSB-SEED-" in capsys.readouterr().out
    with pytest.raises(PermissionError):
        hsb_cli.cmd_seed_send(_args(seed_file=str(p), to=["other@firma.de"]), client=client)


def test_cmd_seed_read_raw_file_and_checklist(tmp_path, capsys):
    import hsb_cli
    eml = tmp_path / "m.eml"
    eml.write_bytes(GMAIL_RAW)
    hsb_cli.cmd_seed_read(_args(raw_file=str(eml)))
    out = capsys.readouterr().out
    assert "spf: pass" in out and "dkim_domain: hsb-boden.com" in out and "folder: unbekannt" in out
    p = tmp_path / "s.json"
    p.write_text(json.dumps([{"provider": "gmail", "address": "seed-gmail@seedbox.test"}]))
    hsb_cli.cmd_seed_read(_args(seed_file=str(p), token="HSB-SEED-x"))
    assert "HSB-SEED-x" in capsys.readouterr().out
