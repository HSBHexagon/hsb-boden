"""Regression: Versandgesundheit sieht Bounces in 'Unzustellbar' und erzwingt 100/Tag."""
from __future__ import annotations

import pytest

import com_mailbox_manager as com
import dual_domain_collector as collector
import send_governance as health


def test_health_collector_reads_inbox_and_bounce_folder_without_duplicates(monkeypatch):
    called = []

    class Client:
        def __init__(self, owner):
            self.owner = owner

        def fetch_inbound_messages(self, limit=0, *, folder=None):
            called.append((self.owner, folder))
            common = dict(from_="postmaster@example.net", subject="Undeliverable",
                          body="Final-Recipient: rfc822;kunde@example.org\n550 5.1.1 user unknown")
            if folder is None:
                return [dict(id="<same@host>", internet_message_id="<same@host>",
                             date_str="2026-11-11", **{"from": common["from_"]},
                             subject=common["subject"], body=common["body"])]
            return [
                dict(id="<same@host>", internet_message_id="<same@host>",
                     date_str="2026-11-11", **{"from": common["from_"]},
                     subject=common["subject"], body=common["body"]),
                dict(id="<new@host>", internet_message_id="<new@host>",
                     date_str="2026-11-11", **{"from": common["from_"]},
                     subject=common["subject"], body=common["body"]),
            ]

    monkeypatch.setattr(com, "ComMailboxClient", Client)
    result = collector.collect_all_inbounds(owners=["JOEL"], include_de=False,
                                            include_bounce_folder=True)
    assert [m.message_id for m in result] == ["<same@host>", "<new@host>"]
    assert called == [("JOEL", None), ("JOEL", "Unzustellbar")]


def test_health_default_scans_bounce_archive(tmp_path, monkeypatch):
    (tmp_path / "send-health.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(health, "_parse_send_health", lambda _: {
        "seen_inbound_ids": [], "sample_sent": 1, "hard_bounces": 0,
        "policy_bounces": 0, "deferrals_today": 0, "spam_reports": 0,
        "seed_dkim_pass": True
    })
    called = []
    def fake_collector(*, limit_per_mailbox, include_de, include_bounce_folder):
        called.append((limit_per_mailbox, include_de, include_bounce_folder))
        return [collector.UnifiedInboundMessage(
            source="COM_IMAP", owner="JOEL", message_id="<dsn@provider>",
            date="2026-11-11", sender="mailer-daemon@example.net",
            subject="Undeliverable", body="Final-Recipient: rfc822;kunde@example.org\n550 5.1.1 user unknown")]
    monkeypatch.setattr(collector, "collect_all_inbounds", fake_collector)
    result = health.observed_health(tmp_path)
    assert called == [(0, False, True)]
    assert result["hard_bounces"] + result.get("review_bounces", 0) >= 1


def test_runtime_environment_supports_operator_configured_daily_cap(monkeypatch):
    from importlib.util import module_from_spec, spec_from_file_location

    monkeypatch.setenv("HSB_MAX_DAILY_CAP", "250")
    monkeypatch.setenv("HSB_DAILY_CAP", "250")
    monkeypatch.setenv("HSB_MAX_BUDGET", "250")
    # Isolated module: reloading the shared module changes exception identities in other tests.
    spec = spec_from_file_location("send_governance_cap_probe", health.__file__)
    assert spec is not None and spec.loader is not None
    probe = module_from_spec(spec)
    spec.loader.exec_module(probe)
    assert probe.MAX_DAILY_CAP_PER_MAILBOX == 250
    assert probe.DAILY_CAP_PER_MAILBOX == 250
    assert probe.daily_budget("2026-10-01", "2026-11-11") == 250


@pytest.mark.parametrize("list_response,expected", [
    (("OK", [None]), False),
    (("NO", []), True),
])
def test_missing_bounce_folder_only_empty_on_proved_absence(list_response, expected):
    class IMAP:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def select(self, folder, readonly=True): return "NO", []
        def list(self, root, folder): return list_response

    client = object.__new__(com.ComMailboxClient)
    client.owner = "JOEL"
    client.cfg = {"inbox_folder": "INBOX"}
    client._get_imap = lambda: IMAP()
    if expected:
        with pytest.raises(RuntimeError, match="BOUNCE_FOLDER_SELECT_FAILED"):
            client.fetch_inbound_messages(folder="Unzustellbar")
    else:
        assert client.fetch_inbound_messages(folder="Unzustellbar") == []
