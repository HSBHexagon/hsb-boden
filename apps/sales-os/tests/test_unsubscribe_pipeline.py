"""Regression for the real public unsubscribe route and its CRM ingestion."""
import io
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

@pytest.mark.parametrize("subject", ["Abmelden", "Abmeldung", "Re: Abmelden", "Unsubscribe"])
def test_subject_only_unsubscribe_is_an_explicit_optout(subject):
    from inbound_classifier import classify_inbound_message
    assert classify_inbound_message("buyer@example.invalid", subject, "").category == "OPTOUT"

def test_question_about_unsubscribe_is_not_an_optout():
    from inbound_classifier import classify_inbound_message
    assert classify_inbound_message("buyer@example.invalid", "Frage zum Abmelden", "Wie funktioniert das?").category == "NEUTRAL"

@pytest.mark.parametrize("page,expected", [
    ("<h1>Erfolgreich abgemeldet</h1><p>Ihre Adresse wurde gesperrt.</p>", False),
    ("<h1>Abmeldung anfordern</h1><a href='mailto:j-cherino@hsb-boden.com?subject=Abmelden'>Abmeldung per E-Mail senden</a>", True),
    ("<h1>Not found</h1>", False),
])
def test_optout_probe_requires_a_real_request_route(monkeypatch, page, expected):
    import sales_reconciliation as recon
    class Response(io.BytesIO):
        status = 200
        url = "https://www.hsb-boden.de/abmelden/"
        headers = {"Content-Type": "text/html; charset=utf-8"}
    data = ("<html><body>" + page + " " * 600 + "</body></html>").encode()
    monkeypatch.setattr(recon, "urlopen", lambda *a, **k: Response(data))
    result = recon.probe_url("https://www.hsb-boden.de/abmelden")
    assert result["reachable"] is True
    assert result["valid"] is expected

@pytest.mark.parametrize("fail_first_append", [False, True])
def test_previously_neutral_unsubscribe_is_repaired_once(monkeypatch, fail_first_append):
    import closed_loop_crm
    import dual_domain_collector
    import outbound_safety
    import sync_to_google_sheet
    from inbound_classifier import classify_inbound_message
    headers = ["Lead-ID", "E-Mail", "Reply_Status", "Suppressed", "Versandfreigabe",
               "Opt-out-Status", "Suppression_Reason", "Last_Reply_At"]
    rows = [headers, ["L1", "buyer@example.invalid", "replied", "", "yes", "", "", ""]]
    mid = "<unsubscribe@example.invalid>"
    events = [["id", "at", "source", "sender", "subject", "mid"],
              ["old-event", "", "COM:JOEL", "", "Abmelden", mid]]
    appended = []
    append_calls = []
    class Values:
        def get(self, **kw):
            value = rows if kw["range"].startswith("ALL_LEADS!") else appended if kw["range"] == "INBOUND_EVENTS!A3:M3" else events
            return SimpleNamespace(execute=lambda: {"values": value})
        def append(self, **kw):
            append_calls.append(kw)
            if fail_first_append and len(append_calls) == 1:
                raise RuntimeError("append interrupted after CRM write")
            appended[:] = kw["body"]["values"]
            events.extend(appended)
            return SimpleNamespace(execute=lambda: {"updates": {"updatedRange": "INBOUND_EVENTS!A3:M3"}})
    values = Values()
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values))
    monkeypatch.setattr(sync_to_google_sheet, "get_sheets_service", lambda: svc)
    monkeypatch.setattr(dual_domain_collector, "collect_all_inbounds", lambda **kw: [
        SimpleNamespace(message_id=mid, source="COM", owner="JOEL",
                        sender="buyer@example.invalid", subject="Abmelden", body="",
                        date="2026-10-26T10:00:00Z")])
    writes = []
    def write(_svc, _sheet, _headers, row, change):
        writes.append(change)
        for k, v in change.items():
            rows[row-1][headers.index(k)] = v
    monkeypatch.setattr(outbound_safety, "crm_write_readback", write)
    if fail_first_append:
        with pytest.raises(RuntimeError, match="append interrupted"):
            closed_loop_crm.sync_inbounds(apply=True, include_de=False)
    first = closed_loop_crm.sync_inbounds(apply=True, include_de=False)
    assert first["matched_new_events"] == 1
    assert rows[1][headers.index("Opt-out-Status")] == "yes"
    assert rows[1][headers.index("Suppressed")] == "yes"
    assert rows[1][headers.index("Versandfreigabe")] == "no"
    second = closed_loop_crm.sync_inbounds(apply=True, include_de=False)
    assert second["matched_new_events"] == 0
    assert len(writes) == (2 if fail_first_append else 1)
    assert len(appended) == 1


def test_unsubscribe_from_colleague_mailbox_suppresses_original_lead_via_token(monkeypatch):
    """List-Unsubscribe-Klick aus einem anderen Firmenpostfach: Zuordnung über das Lead-Token im Text."""
    import closed_loop_crm
    import dual_domain_collector
    import outbound_safety
    import sync_to_google_sheet
    headers = ["Lead-ID", "E-Mail", "Reply_Status", "Suppressed", "Versandfreigabe",
               "Opt-out-Status", "Suppression_Reason", "Last_Reply_At"]
    headers = headers + ["Website"]
    rows = [headers,
            ["HSB-7", "info@firma.invalid", "", "", "yes", "", "", "", "https://www.firma.invalid/"],
            ["HSB-8", "other@firma.invalid", "", "", "yes", "", "", "", "https://www.firma.invalid/"]]
    events = [["id", "at", "source", "sender", "subject", "mid"]]
    appended = []
    class Values:
        def get(self, **kw):
            value = rows if kw["range"].startswith("ALL_LEADS!") else appended if kw["range"] == "INBOUND_EVENTS!A2:M2" else events
            return SimpleNamespace(execute=lambda: {"values": value})
        def append(self, **kw):
            appended[:] = kw["body"]["values"]
            events.extend(appended)
            return SimpleNamespace(execute=lambda: {"updates": {"updatedRange": "INBOUND_EVENTS!A2:M2"}})
    values = Values()
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values))
    monkeypatch.setattr(sync_to_google_sheet, "get_sheets_service", lambda: svc)
    monkeypatch.setattr(dual_domain_collector, "collect_all_inbounds", lambda **kw: [
        SimpleNamespace(message_id="<alias@firma.invalid>", source="COM", owner="JOEL",
                        sender="kollege@firma.invalid", subject="Abmelden",
                        body="Bitte keine weiteren E-Mails. HSB-ABMELDUNG: HSB-7",
                        date="2026-10-26T10:00:00Z")])
    def write(_svc, _sheet, _headers, row, change):
        for k, v in change.items():
            rows[row-1][headers.index(k)] = v
    monkeypatch.setattr(outbound_safety, "crm_write_readback", write)
    result = closed_loop_crm.sync_inbounds(apply=True, include_de=False)
    assert result["matched_new_events"] == 1
    assert rows[1][headers.index("Opt-out-Status")] == "yes"
    assert rows[1][headers.index("Suppressed")] == "yes"
    assert rows[2][headers.index("Suppressed")] == ""


def test_lead_token_in_ordinary_reply_does_not_suppress(monkeypatch):
    """Nur eine echte Abmeldung wertet das Token aus; eine normale Antwort mit zitiertem Link nicht."""
    from inbound_classifier import classify_inbound_message
    result = classify_inbound_message("kollege@firma.invalid", "Re: Industrieböden",
                                      "Gerne Termin nächste Woche. HSB-ABMELDUNG: HSB-7")
    assert result.category != "OPTOUT"


@pytest.mark.parametrize("sender,body,lead_email", [
    ("fremder@andere-firma.invalid", "HSB-ABMELDUNG: HSB-7", "info@firma.invalid"),
    ("unrelated-person@gmail.com", "HSB-ABMELDUNG: HSB-7", "customer@gmail.com"),
    ("unrelated@gmx.com", "HSB-ABMELDUNG: HSB-7", "customer@gmx.com"),
    ("unrelated@pm.me", "HSB-ABMELDUNG: HSB-7", "customer@pm.me"),
    ("kollege@firma.invalid", "HSB-ABMELDUNG: HSB-7 HSB-ABMELDUNG: HSB-8", "info@firma.invalid"),
])
def test_token_from_foreign_domain_or_multiple_tokens_does_not_suppress(monkeypatch, sender, body, lead_email):
    import closed_loop_crm
    import dual_domain_collector
    import outbound_safety
    import sync_to_google_sheet
    headers = ["Lead-ID", "E-Mail", "Reply_Status", "Suppressed", "Versandfreigabe",
               "Opt-out-Status", "Suppression_Reason", "Last_Reply_At"]
    rows = [headers,
            ["HSB-7", lead_email, "", "", "yes", "", "", ""],
            ["HSB-8", "other@firma.invalid", "", "", "yes", "", "", ""]]
    # Website zeigt bewusst NICHT auf die Freemail-Domain: keine verifizierte Firmendomain.
    headers = headers + ["Website"]
    rows = [headers] + [r + ["https://www.firma.invalid/"] for r in rows[1:]]
    events = [["id", "at", "source", "sender", "subject", "mid"]]
    class Values:
        def get(self, **kw):
            value = rows if kw["range"].startswith("ALL_LEADS!") else events
            return SimpleNamespace(execute=lambda: {"values": value})
        def append(self, **kw):
            raise AssertionError("no event expected")
    values = Values()
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values))
    monkeypatch.setattr(sync_to_google_sheet, "get_sheets_service", lambda: svc)
    monkeypatch.setattr(dual_domain_collector, "collect_all_inbounds", lambda **kw: [
        SimpleNamespace(message_id="<forged@x.invalid>", source="COM", owner="JOEL",
                        sender=sender, subject="Abmelden", body=body, date="2026-10-26T10:00:00Z")])
    monkeypatch.setattr(outbound_safety, "crm_write_readback", lambda *a: pytest.fail("no CRM write expected"))
    result = closed_loop_crm.sync_inbounds(apply=True, include_de=False)
    assert result["matched_new_events"] == 0
    assert rows[1][headers.index("Suppressed")] == "" and rows[2][headers.index("Suppressed")] == ""



def test_mime_encoded_unsubscribe_subject_is_an_optout():
    from inbound_classifier import classify_inbound_message
    assert classify_inbound_message("kollege@firma.invalid", "=?UTF-8?B?QWJtZWxkZW4=?=", "HSB-ABMELDUNG: HSB-7").category == "OPTOUT"


def test_company_domain_from_website():
    import closed_loop_crm
    assert closed_loop_crm.company_domain({"Website": "https://www.Firma.invalid/impressum?x=1"}) == "firma.invalid"
    assert closed_loop_crm.company_domain({"Website": ""}) == ""


@pytest.mark.parametrize("subject", ["=?utf-8?b?QQ?=", "=?x-unknown?q?a?=", "=?utf-8?b?=?=", "=?utf-8?q?=FF?="])
def test_malformed_encoded_subject_never_raises(subject):
    from inbound_classifier import classify_inbound_message, decode_mime_header
    assert isinstance(decode_mime_header(subject), str)
    assert classify_inbound_message("a@firma.invalid", subject, "").category in {"NEUTRAL", "OPTOUT", "HOT_LEAD", "OOO_URLAUB", "BOUNCE"}
