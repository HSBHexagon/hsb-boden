"""TDD regression suite for deduplication, opt-out bounce guard, and Outlook draft cleanup."""
from contextlib import nullcontext
from email import policy
from email.message import EmailMessage
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))


def _raw_msg(to_addr: str, mid: str, lead_id: str = "", sender: str = "j-cherino@hsb-boden.com", unsent: bool = False) -> bytes:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_addr
    msg["Subject"] = "Bodenreparatur"
    msg["Message-ID"] = mid
    if lead_id:
        msg["X-HSB-Lead-ID"] = lead_id
    if unsent:
        msg["X-Unsent"] = "1"
    msg.set_content("Guten Tag")
    return msg.as_bytes()


class FakeFolderImap:
    def __init__(self, folders: dict[str, dict[str, bytes]]):
        self.folders = {k: dict(v) for k, v in folders.items()}
        self.current = None
        self.deleted_log = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return None

    def list(self, *_):
        return "OK", [f'(\\HasNoChildren) "." "{name}"'.encode() for name in self.folders]

    def select(self, folder, readonly=False):
        if folder not in self.folders:
            return "NO", []
        self.current = folder
        return "OK", [str(len(self.folders[folder])).encode()]

    def uid(self, cmd, *args):
        cmd_l = cmd.lower()
        box = self.folders[self.current]
        if cmd_l == "search":
            return "OK", [b" ".join(u.encode() for u in box)]
        if cmd_l == "fetch":
            uids = str(args[0].decode() if isinstance(args[0], bytes) else args[0]).split(",")
            out = []
            for idx, u in enumerate(uids, 1):
                if u in box:
                    raw = box[u]
                    out.append((f"{idx} (UID {u} BODY[] {{{len(raw)}}}".encode(), raw))
                    out.append(b")")
            return "OK", out
        if cmd_l == "store" and "+FLAGS" in args and r"(\Deleted)" in args:
            uids = str(args[0].decode() if isinstance(args[0], bytes) else args[0]).split(",")
            for u in uids:
                if u in box:
                    self.deleted_log.append((self.current, u))
            return "OK", [b""]
        return "NO", []

    def expunge(self):
        for folder, uid in list(self.deleted_log):
            if folder == self.current:
                self.folders[folder].pop(uid, None)
        return "OK", []


def test_purge_owner_sent_drafts_matches_lead_id_and_message_id_when_to_differs():
    from draft_purge import purge_owner_sent_drafts

    imap = FakeFolderImap({
        "Entw&APw-rfe": {
            "13261": _raw_msg("skontakt@schilkin.de", "<m307@hsb-boden.com>", "HSB-20260708-00307", unsent=True),
            "13262": _raw_msg("other@kunde.de", "<m999@hsb-boden.com>", "HSB-20260708-00999"),
            "15969": _raw_msg("j-cherino@hsb-boden.com", "<ios-draft@hsb-boden.com>"),
        }
    })
    count = purge_owner_sent_drafts(
        imap,
        "Entw&APw-rfe",
        {"kontakt@schilkin.de"},
        sent_lead_ids={"HSB-20260708-00307"},
        sent_message_ids={"<m999@hsb-boden.com>"},
        apply=True,
    )
    assert count == 2
    assert set(imap.folders["Entw&APw-rfe"].keys()) == {"15969"}


def test_cmd_purge_sent_drafts_unions_crm_and_live_sent_identities(monkeypatch):
    from hsb_cli import cmd_purge_sent_drafts

    leads = [
        {"Lead-ID": "HSB-307", "E-Mail": "kontakt@schilkin.de", "Send_Status": "sent", "Internet_Message_ID": "<m307@hsb>"},
        {"Lead-ID": "HSB-500", "E-Mail": "open@kunde.de", "Send_Status": "drafted", "Internet_Message_ID": "<m500@hsb>"},
    ]
    monkeypatch.setattr("hsb_cli._load_all_leads", lambda svc: (["Lead-ID", "E-Mail", "Send_Status", "Internet_Message_ID"], leads))
    imap = FakeFolderImap({
        "Entw&APw-rfe": {
            "1": _raw_msg("skontakt@schilkin.de", "<m307@hsb>", "HSB-307"),
            "2": _raw_msg("extra-live@kunde.de", "<mlive@hsb>", "HSB-LIVE"),
            "3": _raw_msg("open@kunde.de", "<m500@hsb>", "HSB-500"),
        },
        "Gesendet": {
            "90": _raw_msg("extra-live@kunde.de", "<mlive@hsb>", "HSB-LIVE"),
        },
    })
    mc = MagicMock()
    mc.cfg = {"drafts_folder": "Entw&APw-rfe", "sent_folder": "Gesendet"}
    mc._get_imap.return_value.__enter__.return_value = imap
    monkeypatch.setattr("com_mailbox_manager.ComMailboxClient", lambda o: mc)
    report = cmd_purge_sent_drafts(SimpleNamespace(owner="JOEL", apply=True), svc=MagicMock())
    assert report["JOEL"] == {"orphaned_sent_drafts": 2, "applied": True}
    assert set(imap.folders["Entw&APw-rfe"].keys()) == {"3"}


def test_cleanup_sent_draft_checks_false_and_purges_duplicate_copies(capsys):
    from com_mailbox_manager import ComMailboxClient
    from outbound_safety import cleanup_sent_draft

    client = object.__new__(ComMailboxClient)
    client.owner = "JOEL"
    client.cfg = {"drafts_folder": "INBOX.Drafts"}
    imap = FakeFolderImap({
        "INBOX.Drafts": {
            "10": _raw_msg("info@firma.de", "<m1@hsb>", "HSB-1"),
            "11": _raw_msg("info@firma.de", "<m2@hsb>", "HSB-1"),
            "12": _raw_msg("keep@other.de", "<m3@hsb>", "HSB-2"),
        }
    })
    client._get_imap = lambda: imap
    cleanup_sent_draft(client, "INBOX.Drafts", "999", lead_id="HSB-1", message_id="<m1@hsb>", recipient="info@firma.de")
    assert set(imap.folders["INBOX.Drafts"].keys()) == {"12"}


def test_delete_draft_by_uid_returns_false_on_imap_no(monkeypatch):
    from com_mailbox_manager import ComMailboxClient

    mgr = ComMailboxClient("JOEL")
    imap_mock = MagicMock()
    imap_mock.select.return_value = ("OK", [b"1"])
    imap_mock.uid.return_value = ("NO", [b"store failed"])
    monkeypatch.setattr(mgr, "_get_imap", lambda: MagicMock(__enter__=lambda s: imap_mock, __exit__=lambda *a: None))
    assert mgr.delete_draft_by_uid("555", "INBOX.Drafts") is False


def test_dispatch_verified_blocks_corporate_domain_duplicates_and_allows_invalid(tmp_path, monkeypatch):
    import closed_loop_crm as inbound
    import com_mailbox_manager as mail
    import outbound_safety as out
    import sales_reconciliation as recon
    import send_governance as guard
    import sync_to_google_sheet as sheets
    from test_outbound_safety_gate import _crm_lead

    leads = [
        _crm_lead(**{"Lead-ID": "L1", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "alice@real-kunde.de"}),
        _crm_lead(**{"Lead-ID": "L2", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "bob@real-kunde.de"}),
        _crm_lead(**{"Lead-ID": "L3", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "carol@sending.de", "Send_Status": "SENDING"}),
        _crm_lead(**{"Lead-ID": "L4", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "dave@sending.de"}),
        _crm_lead(**{"Lead-ID": "L5", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "t1@firma.invalid"}),
        _crm_lead(**{"Lead-ID": "L6", "Verantwortlicher": "Joel Cherino Diaz", "E-Mail": "t2@firma.invalid"}),
    ]
    headers = list(leads[0])
    raws, queue, drafts = {}, [], []
    for i, lead in enumerate(leads, 1):
        raw = _raw_msg(lead["E-Mail"], f"<{i}@hsb-boden.com>", lead["Lead-ID"])
        raws[str(i)] = raw
        if lead["Lead-ID"] != "L3":
            queue.append({"lead_id": lead["Lead-ID"], "owner": "JOEL", "email": lead["E-Mail"]})
            drafts.append({
                "lead_id": lead["Lead-ID"], "sendable": True, "folder": "Drafts",
                "uidvalidity": "7", "uid": str(i), "sha256": hashlib.sha256(raw).hexdigest(),
            })

    class IMAP:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def select(self, *a, **k): return "OK", []
        def response(self, *a): return None, [b"7"]
        def uid(self, cmd, uid, *a): return "OK", [(b"h", raws[uid])]

    monkeypatch.setattr(mail, "ComMailboxClient", lambda o: SimpleNamespace(_get_imap=lambda: IMAP(), cfg={}))
    monkeypatch.setattr(out, "mailbox_dispatch_lock", lambda c, **k: nullcontext())
    monkeypatch.setattr(inbound, "sync_inbounds", lambda **k: None)

    def audit(path):
        path.mkdir(parents=True)
        (path / "queue.json").write_text(json.dumps(queue))
        (path / "drafts.json").write_text(json.dumps(drafts))

    monkeypatch.setattr(recon, "run_audit", audit)
    monkeypatch.setattr(recon, "assess_message", lambda *a: {"issues": []})
    monkeypatch.setattr(recon, "has_unreviewed_legacy_variant", lambda *a: False)
    values = SimpleNamespace(get=lambda **k: SimpleNamespace(
        execute=lambda: {"values": [headers] + [[l.get(h, "") for h in headers] for l in leads]}))
    monkeypatch.setattr(sheets, "get_sheets_service", lambda: SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values)))
    monkeypatch.setattr("lead_quality.deliverability_flags", lambda *a: [])
    monkeypatch.setattr(guard, "enforce_domain_health", lambda *a: 10)
    deliveries = []
    monkeypatch.setattr(out, "complete_delivery", lambda *a: (deliveries.append(a[6]["lead_id"]) or True))
    monkeypatch.setattr(out.time, "sleep", lambda *a: None)
    monkeypatch.setenv("HSB_CUSTOMER_SEND_ENABLED", "yes")
    monkeypatch.setenv("HSB_SALES_STATE_DIR", str(tmp_path))

    res = out.dispatch_verified(10, owners=("JOEL",), dry_run=False)
    assert deliveries == ["L1", "L5", "L6"]
    assert res["skipped"]["CORPORATE_DOMAIN_ALREADY_CONTACTED"] == 1


def test_select_queue_deduplicates_corporate_domains_only_after_owner_segment_variant_filters():
    from outbound_safety import select_queue

    queue = [
        {"lead_id": "L1", "owner": "JOEL", "email": "alice@firma-a.de"},
        {"lead_id": "L2", "owner": "JORDI", "email": "bob@firma-a.de"},
        {"lead_id": "L3", "owner": "JORDI", "email": "carol@firma-a.de"},
        {"lead_id": "L4", "owner": "JORDI", "email": "t1@firma.invalid"},
        {"lead_id": "L5", "owner": "JORDI", "email": "t2@firma.invalid"},
    ]
    drafts = [
        {"lead_id": "L1", "sendable": True, "template_id": "v2-architekten-1"},
        {"lead_id": "L2", "sendable": True, "template_id": "v2-produktion-reparatur-1"},
        {"lead_id": "L3", "sendable": True, "template_id": "v2-produktion-1"},
        {"lead_id": "L4", "sendable": True, "template_id": "v2-produktion-reparatur-1"},
        {"lead_id": "L5", "sendable": True, "template_id": "v2-produktion-reparatur-1"},
    ]
    # JORDI-only batch is NOT blocked by JOEL lead L1 on the same corporate domain.
    sel_jordi, used_jordi = select_queue(queue, drafts, ("JORDI",), 5)
    assert [x["lead_id"] for x in sel_jordi] == ["L2", "L4", "L5"]
    assert used_jordi == {"JORDI": 3}

    # Segment/variant filters run BEFORE domain dedupe, so L2 is still eligible if L1 didn't match.
    sel_rep, _ = select_queue(queue, drafts, ("JOEL", "JORDI"), 5, segments={"produktion"}, variant="reparatur")
    assert [x["lead_id"] for x in sel_rep] == ["L2", "L4", "L5"]

    # Combined unrestricted dispatch deduplicates L1 vs L2/L3 while allowing .invalid pairs.
    sel_all, used_all = select_queue(queue, drafts, ("JOEL", "JORDI"), 5)
    assert [x["lead_id"] for x in sel_all] == ["L1", "L4", "L5"]
    assert used_all == {"JOEL": 1, "JORDI": 2}


def test_dedupe_queue_corporate_domains_marks_second_company_contact_unsendable():
    from sales_reconciliation import dedupe_queue_corporate_domains

    balances = [
        {"lead_id": "L1", "email": "a@alpha.de", "reasons": [], "sendable": True},
        {"lead_id": "L2", "email": "b@alpha.de", "reasons": [], "sendable": True},
        {"lead_id": "L3", "email": "c@gmail.com", "reasons": [], "sendable": True},
        {"lead_id": "L4", "email": "d@gmail.com", "reasons": [], "sendable": True},
    ]
    dedupe_queue_corporate_domains(balances)
    assert balances[0]["sendable"] is True
    assert balances[1]["sendable"] is False
    assert "DUPLICATE_CORPORATE_DOMAIN_IN_QUEUE" in balances[1]["reasons"]
    assert balances[2]["sendable"] is True and balances[3]["sendable"] is True


def test_sync_inbounds_and_rescue_never_unsuppress_optout_leads(monkeypatch):
    from bounce_rescue_agent import RescueResult
    from closed_loop_crm import rescue_crm_bounces, sync_inbounds

    headers = ["Lead-ID", "E-Mail", "Opt-out-Status", "Versandfreigabe", "Suppressed", "Bounce_Status", "Reply_Status", "Suppression_Reason", "Pipeline", "Notizen"]
    lead = ["L-OPTOUT", "bad@optout-firma.de", "YES", "no", "yes", "hard_bounce", "opt_out", "INBOUND_OPTOUT", "Abgemeldet / Widerspruch", ""]
    rows = [headers, lead]
    writes = []
    inbox = SimpleNamespace(
        message_id="<b-optout@optout-firma.de>", source="COM_IMAP", owner="JOEL", date="2026-11-12T10:00:00Z",
        sender="mailer-daemon@optout-firma.de", subject="Undeliverable",
        body="Final-Recipient: rfc822; bad@optout-firma.de\nAction: failed\nStatus: 5.1.1\n",
    )

    class Values:
        events = []
        def get(self, *, range, **_):
            return SimpleNamespace(execute=lambda: {"values": rows if range.startswith("ALL_LEADS") else self.events})
        def append(self, *, body, **_):
            self.events = body["values"]
            return SimpleNamespace(execute=lambda: {"updates": {"updatedRange": "INBOUND_EVENTS!A2:M2"}})
        def batchUpdate(self, **_):
            raise AssertionError("batchUpdate must not run for opted-out lead")

    values_obj = Values()
    svc = SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values_obj))
    monkeypatch.setattr("sync_to_google_sheet.get_sheets_service", lambda: svc)
    monkeypatch.setattr("dual_domain_collector.collect_all_inbounds", lambda **_: [inbox])
    monkeypatch.setattr("outbound_safety.crm_write_readback", lambda *args: writes.append(args[-1]))
    monkeypatch.setattr("bounce_rescue_agent.BounceRescueAgent.rescue_lead",
                        lambda *a, **k: RescueResult(status="SUCCESS", failed_email="bad@optout-firma.de", rescued_email="info@optout-firma.de"))

    res_rescue = rescue_crm_bounces(apply=True, svc=svc)
    assert res_rescue["rescued_count"] == 0
    sync_inbounds(apply=True, include_de=False)
    for w in writes:
        assert w.get("Suppressed") != "no"
        assert w.get("Versandfreigabe") != "yes"
        assert w.get("Pipeline") != "Freigegeben"


def test_sent_header_repair_purge_verified_backups_requires_clean_sent_copy(tmp_path):
    from sent_header_repair import BACKUP, purge_verified_backups

    raw_backup = _raw_msg("x@kunde.de", "<m1@hsb>", "HSB-1", sender="j-post@hsb-boden.com", unsent=True)
    raw_unsent_sent = _raw_msg("x@kunde.de", "<m1@hsb>", "HSB-1", sender="j-post@hsb-boden.com", unsent=True)
    raw_clean_sent = _raw_msg("x@kunde.de", "<m1@hsb>", "HSB-1", sender="j-post@hsb-boden.com", unsent=False)

    imap_bad = FakeFolderImap({BACKUP: {"1": raw_backup}, "Gesendet": {"2": raw_unsent_sent}})
    client_bad = SimpleNamespace(cfg={"sent_folder": "Gesendet"}, _get_imap=lambda: imap_bad)
    with pytest.raises(RuntimeError, match="SENT_BACKUP_UNVERIFIED"):
        purge_verified_backups(client_bad, archive_dir=tmp_path / "arc", apply=True)
    assert "1" in imap_bad.folders[BACKUP]

    imap_ok = FakeFolderImap({BACKUP: {"1": raw_backup}, "Gesendet": {"2": raw_clean_sent}})
    client_ok = SimpleNamespace(cfg={"sent_folder": "Gesendet"}, _get_imap=lambda: imap_ok)
    res = purge_verified_backups(client_ok, archive_dir=tmp_path / "arc2", apply=True)
    assert res["verified_backups"] == 1 and res["purged_backups"] == 1
    assert imap_ok.folders[BACKUP] == {}
    assert (tmp_path / "arc2" / "manifest.json").is_file()


def test_collect_sent_identities_and_purge_match_case_insensitively():
    from draft_purge import collect_sent_identities, purge_owner_sent_drafts

    class ReadonlyLegacyImap:
        def __init__(self):
            self.active = "INBOX"
            self.deleted_uids = []
            self.folders = {
                "Gesendet": {
                    b"10": _raw_msg("Other@Kunde.de", "<M307@HSB.LOCAL>", "HSB-307", unsent=False),
                },
                "Entwuerfe": {
                    b"21": _raw_msg("alt@kunde.de", "<m307@hsb.local>", "hsb-999", unsent=True),
                    b"22": _raw_msg("alt2@kunde.de", "<other@hsb.local>", "hsb-307", unsent=True),
                    b"23": _raw_msg("keep@kunde.de", "<keep@hsb.local>", "hsb-888", unsent=True),
                },
            }

        def select(self, folder):
            self.active = folder
            return ("OK", [b"1"])

        def uid(self, op, *args):
            bucket = self.folders[self.active]
            if op == "search":
                return ("OK", [b" ".join(bucket.keys())])
            if op == "fetch":
                uids = args[0].split(b",")
                rows = [(b"1 (UID " + u + b")", bucket[u]) for u in uids]
                return ("OK", rows)
            if op == "store" and args[1] in {"+FLAGS", "+FLAGS.SILENT"}:
                for u in args[0].split(b","):
                    self.deleted_uids.append(u)
                    bucket.pop(u, None)
                return ("OK", None)
            raise AssertionError(f"Unexpected uid op: {op} {args}")

        def expunge(self):
            return ("OK", None)

    imap = ReadonlyLegacyImap()
    emails, lids, mids = collect_sent_identities(imap, "Gesendet")
    assert emails == {"other@kunde.de"}
    assert lids == {"hsb-307"}
    assert mids == {"<m307@hsb.local>"}

    purged = purge_owner_sent_drafts(
        imap,
        "Entwuerfe",
        {"OTHER@KUNDE.DE"},
        sent_lead_ids={"HSB-307"},
        sent_message_ids={"<M307@HSB.LOCAL>"},
        apply=True,
    )
    assert purged == 2
    assert set(imap.deleted_uids) == {b"21", b"22"}
    assert list(imap.folders["Entwuerfe"].keys()) == [b"23"]

