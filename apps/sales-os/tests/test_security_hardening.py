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


# --- 5. Schutz auf Verbindungsebene (Weiterleitung, DNS-Rebinding) -------------

def test_redirect_to_internal_target_is_refused_before_request():
    import urllib.error
    handler = bra._PublicRedirectHandler()
    req = bra.urllib.request.Request("https://www.mueller-gmbh.de/impressum")
    with pytest.raises(urllib.error.HTTPError):
        handler.redirect_request(req, None, 302, "Found", {}, "http://127.0.0.1:5678/admin")


def test_connection_to_loopback_is_refused_even_if_dns_check_passed(monkeypatch):
    """Simuliert DNS-Rebinding: Vorabprüfung sagt 'öffentlich', die Verbindung landet aber lokal."""
    import http.server
    import threading

    hits = []

    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"info@mueller-gmbh.de")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        monkeypatch.setattr(bra, "is_public_hostname", lambda host: True)
        agent = BounceRescueAgent()
        url = f"http://127.0.0.1:{srv.server_address[1]}/impressum"
        assert agent._fetch_url_content(url) is None
        assert hits == []
    finally:
        srv.shutdown()


def test_redirect_to_ftp_is_refused():
    import urllib.error
    handler = bra._PublicRedirectHandler()
    req = bra.urllib.request.Request("https://www.mueller-gmbh.de/impressum")
    with pytest.raises(urllib.error.HTTPError):
        handler.redirect_request(req, None, 302, "Found", {}, "ftp://mueller-gmbh.de/x")


def test_opener_has_no_proxy_ftp_file_or_data_handler():
    names = {type(h).__name__ for h in bra.build_public_opener().handlers}
    assert not names & {"ProxyHandler", "FTPHandler", "FileHandler", "DataHandler", "CacheFTPHandler"}


def test_non_http_scheme_is_not_fetched(monkeypatch):
    agent = BounceRescueAgent()
    monkeypatch.setattr(agent, "_open", lambda req: pytest.fail("darf nicht abrufen"))
    assert agent._fetch_url_content("ftp://mueller-gmbh.de/impressum") is None


def test_no_tcp_connection_is_opened_to_private_address(monkeypatch):
    """Codex-Befund: Prüfung muss VOR TCP/TLS greifen – der lokale Listener darf keine Verbindung sehen."""
    import threading
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    listener.settimeout(0.5)
    accepted = []

    def accept_loop():
        try:
            while True:
                conn, _ = listener.accept()
                accepted.append(conn)
        except OSError:
            pass

    threading.Thread(target=accept_loop, daemon=True).start()
    port = listener.getsockname()[1]
    try:
        monkeypatch.setattr(bra, "is_public_hostname", lambda host: True)
        for scheme in ("http", "https"):
            assert BounceRescueAgent(timeout=2)._fetch_url_content(f"{scheme}://127.0.0.1:{port}/impressum") is None
        import time
        time.sleep(0.6)
        assert accepted == []
    finally:
        listener.close()


def test_public_ip_is_pinned_for_the_connection(monkeypatch):
    monkeypatch.setattr(
        bra.socket,
        "getaddrinfo",
        lambda host, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))],
    )
    assert bra._resolve_public_ip("mueller-gmbh.de", 80) == "93.184.216.34"


def test_mixed_dns_answer_with_private_ip_is_refused(monkeypatch):
    monkeypatch.setattr(
        bra.socket,
        "getaddrinfo",
        lambda host, *a, **k: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80)),
        ],
    )
    with pytest.raises(ConnectionRefusedError):
        bra._resolve_public_ip("mueller-gmbh.de", 80)
