"""Regression tests for live-mailbox safety and B2B email enrichment.

Never connect to an actual SMTP/IMAP server or mutate a real Google Sheet.
"""
import email
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

from com_mailbox_manager import ComMailboxClient
import com_mailbox_manager
import ingest_optouts
import enrich_missing_emails


def test_dry_run_never_purges_real_drafts(monkeypatch):
    monkeypatch.setattr(ingest_optouts, "get_sheets_service", lambda: object())
    monkeypatch.setattr(ingest_optouts, "load_all_leads_index",
                        lambda _s: ({"ann@example.com": {"row": 9, "lead_id": "L9", "email": "ann@example.com"}}, set()))
    calls = []
    class DummyMailbox:
        def __init__(self, owner):
            calls.append(owner)
        def purge_drafts_for_recipient(self, recipient):
            calls.append(recipient)
            return 1
    monkeypatch.setattr(com_mailbox_manager, "ComMailboxClient", DummyMailbox)
    result = ingest_optouts.suppress_lead_direct("ann@example.com", dry_run=True)
    assert result["ok"] is True
    assert result["purged_drafts"] == 0
    assert calls == []


def test_mismatched_lead_id_rejected_without_mailbox_mutation(monkeypatch):
    monkeypatch.setattr(ingest_optouts, "get_sheets_service", lambda: object())
    monkeypatch.setattr(ingest_optouts, "load_all_leads_index",
                        lambda _s: ({"ann@example.com": {"row": 9, "lead_id": "L9", "email": "ann@example.com"}}, set()))
    result = ingest_optouts.suppress_lead_direct("ann@example.com", lead_id="SOMEONE_ELSE", dry_run=True)
    assert result == {"ok": False, "error": "lead_id_email_mismatch"}


def test_purge_uses_exact_mailbox_address_not_substring(monkeypatch):
    client = ComMailboxClient("JOEL")
    actions = []
    class FakeImap:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def select(self, folder):
            return "OK", [b"2"]
        def search(self, *args):
            return "OK", [b"1 2"]
        def fetch(self, num, what):
            recipient = "joann@example.com" if num == b"1" else "Ann <ann@example.com>"
            raw = f"To: {recipient}\r\nSubject: Test\r\n\r\n".encode()
            return "OK", [(b"RFC822.HEADER", raw)]
        def store(self, num, *args):
            actions.append(("store", num))
            return "OK", []
        def expunge(self):
            actions.append(("expunge",))
            return "OK", []
    monkeypatch.setattr(client, "_get_imap", lambda: FakeImap())
    assert client.purge_drafts_for_recipient("ann@example.com") == 1
    assert [a for a in actions if a[0] == "store"] == [("store", b"2")]


def test_extract_email_from_normal_html_and_ignore_agency_address():
    html = '<a href="mailto:info@kunde.de">Kontakt</a><footer>agentur@webagentur.de</footer>'
    assert enrich_missing_emails.extract_emails_from_html(html, "https://kunde.de/kontakt") == ["info@kunde.de"]
    assert enrich_missing_emails.extract_emails_from_html(html, "anderer-kunde.de") == []


def test_enrichment_uses_website_column_not_phone(monkeypatch):
    hdr = ["Lead_ID", "Company"] + [""] * 6 + ["E-Mail", "Telefon", "Website"] + [""] * 36
    row = ["L1", "Industrie GmbH"] + [""] * 6 + ["", "0123456789", "kunde.de"] + [""] * 36
    class Sheet:
        def execute(self):
            return {"values": [hdr, row]}
        def get(self, **kwargs):
            return self
        def values(self):
            return self
        def spreadsheets(self):
            return self
    monkeypatch.setattr(enrich_missing_emails, "get_sheets_service", lambda: Sheet())
    domains = []
    def crawler(domain):
        domains.append(domain)
        return "info@kunde.de"
    monkeypatch.setattr(enrich_missing_emails, "crawl_domain_for_email", crawler)
    assert enrich_missing_emails.run_missing_email_enrichment(limit=1, apply=False) == 1
    assert domains == ["kunde.de"]
