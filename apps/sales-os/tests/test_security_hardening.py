"""Regression: Härtung von Bounce-Rescue (Domain-Bindung, SSRF, Lese-Limit) und Vacation-Mail (HTML-Escape)."""
from pathlib import Path
import socket
import sys

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

import bounce_rescue_agent as bra
from bounce_rescue_agent import BounceRescueAgent, is_public_hostname
from smart_vacation_agent import build_vacation_followup_email


def _public_dns(monkeypatch):
    monkeypatch.setattr(
        bra.socket,
        "getaddrinfo",
        lambda host, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )


# --- 1. Gerettete Adressen müssen zur Domain des Leads gehören -----------------

def test_rescue_ignores_addresses_of_foreign_domains(monkeypatch):
    agent = BounceRescueAgent()
    page = (
        "Impressum Mueller GmbH. Webdesign: info@agentur-xy.de "
        "Steuerberater: kanzlei@stb-beispiel.de"
    )
    monkeypatch.setattr(agent, "_fetch_url_content", lambda url: page)
    monkeypatch.setattr(bra, "is_public_hostname", lambda host: True)
    assert agent.search_alternative_emails("mueller-gmbh.de") == []


def test_rescue_keeps_own_and_subdomain_addresses(monkeypatch):
    agent = BounceRescueAgent()
    page = "Kontakt: info@mueller-gmbh.de, vertrieb@werk2.mueller-gmbh.de, info@agentur-xy.de"
    monkeypatch.setattr(agent, "_fetch_url_content", lambda url: page)
    monkeypatch.setattr(bra, "is_public_hostname", lambda host: True)
    found = {em for em, _src, _score in agent.search_alternative_emails("mueller-gmbh.de")}
    assert found == {"info@mueller-gmbh.de", "vertrieb@werk2.mueller-gmbh.de"}


def test_lookalike_domain_is_not_a_subdomain(monkeypatch):
    agent = BounceRescueAgent()
    monkeypatch.setattr(agent, "_fetch_url_content", lambda url: "info@fake-mueller-gmbh.de")
    monkeypatch.setattr(bra, "is_public_hostname", lambda host: True)
    assert agent.search_alternative_emails("mueller-gmbh.de") == []


# --- 2. Keine Anfragen an interne Ziele (SSRF) --------------------------------

@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "127.0.0.1",
        "192.168.1.1",
        "10.0.0.5",
        "169.254.169.254",
        "[::1]",
        "beispiel.de:5678",
        "user@beispiel.de",
        "intranet",
        "",
    ],
)
def test_internal_or_malformed_hosts_are_rejected(host):
    assert is_public_hostname(host) is False


def test_hostname_resolving_to_private_ip_is_rejected(monkeypatch):
    monkeypatch.setattr(
        bra.socket,
        "getaddrinfo",
        lambda host, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 0))],
    )
    assert is_public_hostname("rebind.beispiel.de") is False


def test_public_hostname_is_accepted(monkeypatch):
    _public_dns(monkeypatch)
    assert is_public_hostname("mueller-gmbh.de") is True


def test_search_does_not_fetch_internal_domain(monkeypatch):
    agent = BounceRescueAgent()
    calls = []
    monkeypatch.setattr(agent, "_fetch_url_content", lambda url: calls.append(url) or None)
    assert agent.search_alternative_emails("127.0.0.1") == []
    assert calls == []


def test_rescue_lead_reports_blocked_domain(monkeypatch):
    agent = BounceRescueAgent()
    monkeypatch.setattr(agent, "_fetch_url_content", lambda url: pytest.fail("darf nicht abrufen"))
    res = agent.rescue_lead({"Firma": "X", "Website": "http://192.168.1.1:5678", "E-Mail": "a@intranet"})
    assert res.status == "NO_CANDIDATE"


# --- 3. Begrenzte Lesemenge -----------------------------------------------------

class _FakeResp:
    def __init__(self, body, content_type="text/html", url="https://www.mueller-gmbh.de/impressum"):
        self._body = body
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
        self._url = url

    def read(self, n=-1):
        return self._body if n is None or n < 0 else self._body[:n]

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_oversized_page_is_discarded(monkeypatch):
    agent = BounceRescueAgent()
    big = b"x" * (bra.MAX_FETCH_BYTES + 10)
    monkeypatch.setattr(agent, "_open", lambda req: _FakeResp(big))
    _public_dns(monkeypatch)
    assert agent._fetch_url_content("https://www.mueller-gmbh.de/impressum") is None


def test_normal_page_is_read(monkeypatch):
    agent = BounceRescueAgent()
    monkeypatch.setattr(agent, "_open", lambda req: _FakeResp(b"info@mueller-gmbh.de"))
    _public_dns(monkeypatch)
    assert agent._fetch_url_content("https://www.mueller-gmbh.de/impressum") == "info@mueller-gmbh.de"


def test_redirect_to_internal_host_is_discarded(monkeypatch):
    agent = BounceRescueAgent()
    monkeypatch.setattr(agent, "_open", lambda req: _FakeResp(b"secret", url="http://127.0.0.1/admin"))
    _public_dns(monkeypatch)
    assert agent._fetch_url_content("https://www.mueller-gmbh.de/impressum") is None


# --- 4. Firmenname wird im HTML entschärft --------------------------------------

def test_vacation_mail_escapes_company_name():
    lead = {
        "Firma": 'Mueller <a href="https://evil.example">hier</a> & Co',
        "E-Mail": "info@mueller-gmbh.de",
        "Lead_ID": "TEST-1",
    }
    mail = build_vacation_followup_email("JOEL", lead)
    assert '<a href="https://evil.example">' not in mail["body_html"]
    assert "&lt;a href=" in mail["body_html"]
    assert "&amp; Co" in mail["body_html"]
