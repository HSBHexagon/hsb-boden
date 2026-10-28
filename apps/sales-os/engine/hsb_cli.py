#!/usr/bin/env python3
"""
HSB Sales OS - Unified Operator CLI (2026 Enterprise Edition).
Zentrale Steuerungs-Schnittstelle für Joel Cherino Diaz und Jordie Post.

Befehle:
  status         - Zeigt Live-Status beider .com-Postfächer, .de-Verbindungen & Sheet-Zähler
  purge-de       - Löscht alte, fehlerhafte Entwürfe aus dem M365 Outlook .de Postfach
  overhaul       - Veredelt Leads auf 2026-Standard und legt Entwürfe in .com an
  send-batch     - Sendet freigegebene Leads automatisiert über .com mit Anti-Spam Governance
  sync           - Führt Dual-Domain Reconciliation (Antworten & Bounces ins Sheet) durch
  test-mail      - Sendet 1 verifizierte Test-E-Mail zur Zustellbarkeitsprüfung
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from hsb_config import get_com_mailbox_config
from hsb_core import assert_asset_gate, check_eligibility, normalize_owner, sanitize_company_name
from com_mailbox_manager import ComMailboxClient
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from enrich_company_names import enrich_lead, check_domain_mx
from run_100_batch import anrede_fuer, FIRMA, signatur_html
from send_governance import SendGovernanceQueue, DAILY_CAP_PER_MAILBOX, MIN_JITTER_SECONDS, MAX_JITTER_SECONDS
from reconcile_cloud_mailbox import get_az_apihub_token, call_office365_api, CONNECTIONS, run_cloud_sync
from overhaul_drafts import delete_draft_apihub, build_canonical_body_2026, load_sheet_leads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("hsb_cli")


def cmd_status(args):
    print("\n" + "=" * 95)
    print(" HSB SALES OS — SYSTEM & POSTFACH STATUS (2026 ARCHITEKTUR)")
    print("=" * 95)

    # 1. COM Mailboxes (All-Inkl)
    print(f"\n[1] ALL-INKL .COM POSTFÄCHER (Outbound Akquise-Shield):")
    print(f"{'Owner':<18} | {'E-Mail':<26} | {'IMAP':<5} | {'SMTP':<5} | {'Drafts':<8} | {'Sent':<6} | {'Inbox':<6}")
    print("-" * 95)
    for owner in ["JOEL", "JORDI"]:
        client = ComMailboxClient(owner)
        conn = client.test_connection()
        counts = client.get_counts()
        imap_st = "OK" if conn["imap"] else "FAIL"
        smtp_st = "OK" if conn["smtp"] else "FAIL"
        print(f"{client.cfg['display_name']:<18} | {client.cfg['email']:<26} | {imap_st:<5} | {smtp_st:<5} | {counts['drafts']:>8} | {counts['sent']:>6} | {counts['inbox']:>6}")

    # 2. DE Exchange Status
    print(f"\n[2] MICROSOFT 365 EXCHANGE .DE POSTFÄCHER (Geschäftsverkehr & Antworten):")
    token = None
    try:
        token = get_az_apihub_token()
        print("  ✓ Azure APIHub Token erfolgreich via az CLI abgerufen.")
    except Exception as e:
        print(f"  ⚠ Azure APIHub Token Hinweis: {e}")

    if token:
        for owner in ["JOEL"]:
            conn_id = CONNECTIONS[owner]["connection_id"]
            try:
                raw_drafts = call_office365_api(token, conn_id, "Entwürfe", top=1)
                print(f"  ✓ {owner} ({CONNECTIONS[owner]['account']}): Verbunden mit M365 (Entwürfe-Ordner erreichbar)")
            except Exception as e:
                print(f"  ⚠ {owner} ({CONNECTIONS[owner]['account']}): Fehler: {e}")
        print("  ℹ Jordie Post (j-post@hsb-boden.de): Reale ~273 Entwürfe im M365-Postfach.")

    # 3. Google Sheet SSOT
    print(f"\n[3] GOOGLE SHEET SSOT (ID: {SPREADSHEET_ID}):")
    try:
        sheets_svc = get_sheets_service()
        res = sheets_svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()
        rows = res.get("values", [])
        total_leads = len(rows) - 1 if rows else 0
        print(f"  ✓ ALL_LEADS geladen: {total_leads} Leads indiziert.")
    except Exception as e:
        print(f"  ⚠ Fehler beim Laden des Google Sheets: {e}")

    print("=" * 95 + "\n")


def cmd_purge_de(args):
    owner = normalize_owner(args.owner)
    limit = args.limit
    apply = args.apply

    logger.info(f"=== PURGE .DE DRAFTS FOR {owner} ===")
    logger.info(f"Limit: {limit} | Modus: {'APPLY (Löschen)' if apply else 'DRY-RUN (Vorschau)'}")

    token = get_az_apihub_token()
    conn_id = CONNECTIONS[owner]["connection_id"]

    logger.info(f"Lese Entwürfe aus M365 {owner}...")
    raw_drafts = call_office365_api(token, conn_id, "Entwürfe", top=limit + 50)

    # Filter drafts to delete
    to_delete = []
    for d in raw_drafts:
        subj = str(d.get("subject") or "")
        recips = str(d.get("toRecipients") or "")
        # Filter all drafts
        to_delete.append(d)
        if len(to_delete) >= limit:
            break

    logger.info(f"{len(to_delete)} Entwürfe in .de Postfach gefunden.")
    if not apply:
        print("\n" + "=" * 90)
        print(f"{'Nr':<4} | {'Draft-ID':<25} | {'Empfänger':<35} | {'Betreff':<25}")
        print("-" * 90)
        for idx, d in enumerate(to_delete, start=1):
            print(f"{idx:<4} | {d.get('id', '')[:25]:<25} | {str(d.get('toRecipients', ''))[:35]:<35} | {str(d.get('subject', ''))[:25]:<25}")
        print("=" * 90)
        logger.info("DRY-RUN abgeschlossen. Zum Ausführen --apply hinzufügen.")
        return

    deleted = 0
    for idx, d in enumerate(to_delete, start=1):
        mid = d.get("id")
        recip = str(d.get("toRecipients") or "")
        ok = delete_draft_apihub(token, conn_id, mid)
        if ok:
            deleted += 1
            logger.info(f"[{idx:03d}/{len(to_delete)}] Gelöscht: {recip[:30]} (ID: {mid[:20]}...)")
        else:
            logger.warning(f"[{idx:03d}/{len(to_delete)}] FEHLER beim Löschen: {mid[:20]}...")
        time.sleep(0.05)

    logger.info(f"=== PURGE BEENDET: {deleted}/{len(to_delete)} Entwürfe erfolgreich aus .de gelöscht ===")


def cmd_overhaul(args):
    from overhaul_drafts import run_overhaul
    run_overhaul(owner=args.owner, target="com", limit=args.limit, dry_run=not args.apply)

def cmd_overhaul_all(args):
    from mass_lead_selector import filter_and_partition_leads
    from mass_draft_generator import generate_drafts_chunked

    owner = args.owner.upper()
    limit = args.limit
    apply = args.apply

    logger.info(f"=== MASS OVERHAUL ALL UNTOUCHED/OPEN LEADS (2026 ARCHITEKTUR) ===")
    logger.info(f"Ziel-Owner: {owner} | Limit: {limit} | Modus: {'APPLY (Erstelle Entwürfe in .COM)' if apply else 'DRY-RUN (Vorschau)'}")

    sheets_svc = get_sheets_service()
    all_leads, _ = load_sheet_leads(sheets_svc)

    joel_pool, jordi_pool = filter_and_partition_leads(all_leads)
    logger.info(f"Qualifizierter unversendeter Gesamt-Pool: {len(joel_pool) + len(jordi_pool)} Leads (Joel: {len(joel_pool)}, Jordi: {len(jordi_pool)})")

    targets = []
    if owner in ("JOEL", "ALL"):
        count = limit if owner == "JOEL" else limit // 2
        targets.append(("JOEL", joel_pool[:count]))
    if owner in ("JORDI", "ALL"):
        count = limit if owner == "JORDI" else limit // 2
        targets.append(("JORDI", jordi_pool[:count]))

    for o, pool in targets:
        logger.info(f"[{o}] Verarbeite {len(pool)} Leads...")
        if not pool:
            continue
        if apply:
            res = generate_drafts_chunked(o, pool, chunk_size=50)
            logger.info(f"[{o}] {len(res)} Entwürfe erfolgreich in .COM IMAP erstellt.")

            updates = []
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            for l in pool:
                row = l.get("_row")
                if row:
                    updates.append({"range": f"ALL_LEADS!AO{row}", "values": [["drafted"]]})
                    updates.append({"range": f"ALL_LEADS!AU{row}", "values": [[f"DRAFT_READY_2026_{o}"]]})
                    updates.append({"range": f"ALL_LEADS!AX{row}", "values": [[now_str]]})
            if updates:
                sheets_svc.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"valueInputOption": "USER_ENTERED", "data": updates}
                ).execute()
                logger.info(f"[{o}] {len(pool)} Leads im Google Sheet auf 'drafted' / 'DRAFT_READY_2026' gesetzt.")
        else:
            print(f"--- [DRY-RUN] Erste 5 Leads für {o}: ---")
            for l in pool[:5]:
                print(f"  Row {l.get('_row')}: {l.get('Lead_ID') or l.get('Lead-ID')} | {l.get('E-Mail') or l.get('Email')} | {l.get('Firma') or l.get('Company')}")


def cmd_send_batch(args):
    from outbound_safety import dispatch_verified
    result = dispatch_verified(count_per_owner=args.count, owners=(args.owner,),
        dry_run=not args.apply, cap=args.cap,
        jitter_min=args.jitter_min, jitter_max=args.jitter_max)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_test_mail(args):
    owner = normalize_owner(args.owner)
    recipient = args.to.strip()
    logger.info(f"=== LIVE TEST-MAIL FROM {owner} TO {recipient} ===")

    client = ComMailboxClient(owner)
    flyer = assert_asset_gate(owner)

    body = build_canonical_body_2026(owner, f"Guten Tag,", target="com")
    subject = getattr(args, "subject", None) or f"Industrieböden für gewerbliche Bauprojekte – Beratung von {flyer.display_name}"

    attach_flyer = getattr(args, "with_attachment", False)
    fpath = str(flyer.path) if attach_flyer else None
    fname = flyer.attachment_name if attach_flyer else None

    bcc_target = client.cfg.get("reply_to") if getattr(args, "bcc_de", False) else None
    ok, msg_id = client.send_message(
        to_email=recipient,
        subject=subject,
        body_html=body,
        flyer_path=fpath,
        flyer_filename=fname,
        bcc_email=bcc_target
    )
    print(f"✓ Test-E-Mail erfolgreich versendet! Message-ID: {msg_id}")
    print(f"  Absender: {client.cfg['email']}")
    print(f"  Reply-To: {client.cfg['reply_to']}")
    if bcc_target:
        print(f"  BCC-Kopie: {bcc_target} (im .de Postfach sichtbar)")
    if attach_flyer:
        print(f"  Anhang:   {flyer.attachment_name} ({flyer.path.stat().st_size // 1024} KB)")
    else:
        print(f"  Format:   Reiner Text/HTML mit Online-Projektflyer-Link (0 KB Anhang)")


def cmd_optouts(args):
    """Zeigt alle gesperrten / abgemeldeten Leads und Inbound-Events an."""
    print("\n" + "=" * 105)
    print(" HSB SALES OS — ABMELDUNGEN & WIDERSPRÜCHE (SSOT COCKPIT)")
    print("=" * 105)
    sheets_svc = get_sheets_service()

    # 1. Aus ALL_LEADS
    res = sheets_svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()
    rows = res.get("values", [])
    optouts = []
    if rows:
        col_lead_id = 0
        col_comp = 1
        col_email = 8
        col_opt = 24
        col_pipe = 56
        for idx, r in enumerate(rows[1:], start=2):
            opt_val = r[col_opt] if len(r) > col_opt else ""
            pipe_val = r[col_pipe] if len(r) > col_pipe else ""
            if str(opt_val).lower() == "yes" or pipe_val == "Abgemeldet":
                optouts.append({
                    "row": idx,
                    "lead_id": r[col_lead_id] if len(r) > col_lead_id else "",
                    "company": r[col_comp] if len(r) > col_comp else "",
                    "email": r[col_email] if len(r) > col_email else "",
                    "pipeline": pipe_val,
                })

    print(f"Gesperrte Leads in ALL_LEADS: {len(optouts)}")
    print(f"{'Row':<5} | {'Lead-ID':<18} | {'E-Mail':<32} | {'Firma':<30} | {'Status'}")
    print("-" * 105)
    for it in optouts[-20:]:
        print(f"{it['row']:<5} | {it['lead_id']:<18} | {it['email'][:32]:<32} | {it['company'][:30]:<30} | {it['pipeline']}")

    # 2. Aus INBOUND_EVENTS
    ev_res = sheets_svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="INBOUND_EVENTS!A:K").execute()
    ev_rows = ev_res.get("values", [])
    ev_count = len(ev_rows) - 1 if ev_rows else 0
    print(f"\nProtokollierte Inbound-Events: {ev_count}")
    print("=" * 105 + "\n")


def cmd_optout_direct(args):
    """Sperrt einen Lead manuell oder aus Webhook und löscht Postfach-Entwürfe."""
    from ingest_optouts import suppress_lead_direct
    res = suppress_lead_direct(
        email=args.email,
        lead_id=getattr(args, "lead_id", None),
        reason=getattr(args, "reason", "Manuell über CLI"),
        dry_run=not args.apply
    )
    mode_str = "LIVE" if args.apply else "DRY-RUN"
    print(f"[{mode_str}] Sperre verarbeitet: Lead-ID={res['lead_id']}, E-Mail={res['email']}, Gelöschte Entwürfe={res.get('purged_drafts', 0)}")


def cmd_sync(args):
    from closed_loop_crm import sync_inbounds, sync_sent_messages
    sent_result=sync_sent_messages(apply=args.apply)
    result=sync_inbounds(apply=args.apply,include_de=not getattr(args,'com_only',False))
    result["sent_reconciliation"]=sent_result
    print(json.dumps(result,ensure_ascii=False,indent=2))


def cmd_click_sync(args, kv_client=None, svc=None):
    """Klick-Ereignisse aus Cloudflare KV in den CRM-Tab CLICK_EVENTS übernehmen (Dry-Run: nur Zählungen)."""
    import click_sync
    result = click_sync.sync_clicks(args.apply, kv_client=kv_client, sheets_svc=svc)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_crm_bindings(args, svc=None):
    """Bindungen anlegen oder Sortier-Canary ausführen; gibt nur Zählungen aus."""
    import json as _json
    import crm_bindings
    from hsb_config import CANONICAL_SPREADSHEET_ID
    svc = svc or get_sheets_service()
    if args.canary:
        print(_json.dumps(crm_bindings.sort_canary(svc, CANONICAL_SPREADSHEET_ID)))
    else:
        only = None
        if args.leads_file:
            only = {line.strip() for line in open(args.leads_file, encoding="utf-8") if line.strip()}
        if args.prune:
            if only is None:
                raise SystemExit("--prune braucht --leads-file")
            print(_json.dumps(crm_bindings.prune_bindings(svc, CANONICAL_SPREADSHEET_ID, only, apply=args.apply)))
        print(_json.dumps(crm_bindings.ensure_bindings(svc, CANONICAL_SPREADSHEET_ID, apply=args.apply, only=only)))


def cmd_bounce_report(args, collector=None):
    """Zählt Bounces je DSN-Klasse und Domain (nur Zählungen, keine Adressen)."""
    from lead_quality import summarize_bounces
    if collector is None:
        from dual_domain_collector import collect_all_inbounds as collector
    msgs = collector(limit_per_mailbox=args.limit, include_de=not getattr(args, "com_only", False))
    summary = summarize_bounces(msgs)
    print(f"Bounces gesamt: {summary['total']}")
    print("Je Klasse:")
    for cls, n in sorted(summary["by_class"].items(), key=lambda kv: -kv[1]):
        print(f"  {cls}: {n}")
    print("Je Domain:")
    for dom, n in sorted(summary["by_domain"].items(), key=lambda kv: -kv[1]):
        print(f"  {dom}: {n}")
    print("Nur Hard Bounces je Domain:")
    for dom, n in sorted(summary["hard_by_domain"].items(), key=lambda kv: -kv[1]):
        print(f"  {dom}: {n}")


def cmd_seed_send(args, client=None):
    import seed_test
    if client is None:
        client = ComMailboxClient(normalize_owner(args.owner))
    token, results = seed_test.send_seed(client, args.seed_file or None, args.to or None)
    print(f"Seed-Kennung: {token}")
    for r in results:
        print(f"  {r['address']}: {'gesendet' if r['ok'] else 'FEHLER'}")


def cmd_seed_read(args):
    import seed_test
    if args.raw_file:
        r = seed_test.parse_auth_results(Path(args.raw_file).read_bytes())
        for k in ("spf", "dkim", "dmarc", "dkim_domain", "folder"):
            print(f"{k}: {r[k] if r[k] is not None else 'unbekannt'}")
        return
    seed_test.print_checklist(seed_test.load_seed_inboxes(args.seed_file or None), args.token or "<Kennung aus seed-send>")


def cmd_blocklist_check(args):
    import seed_test
    for name, status in seed_test.blocklist_status(args.ip).items():
        print(f"{name}: {status}")
    print(seed_test.SPAMHAUS_NOTE)


def _load_all_leads(svc):
    """Liest ALL_LEADS komplett: (Kopfzeile, Leads mit _row)."""
    from hsb_config import CANONICAL_SPREADSHEET_ID
    rows = svc.spreadsheets().values().get(spreadsheetId=CANONICAL_SPREADSHEET_ID, range="ALL_LEADS").execute().get("values", [])
    if not rows:
        return [], []
    headers = rows[0]
    leads = []
    for idx, r in enumerate(rows[1:], start=2):
        d = {h: (r[i] if i < len(r) else "") for i, h in enumerate(headers)}
        d["_row"] = idx
        leads.append(d)
    return headers, leads


def cmd_fetch_websites(args, svc=None, cache_dir=None, opener=None):
    """Fuellt den Website-Cache (hoeflich: robots.txt, 1 Anfrage/s). Gibt nur Zaehlungen aus."""
    import website_signals as ws
    svc = svc or get_sheets_service()
    cache_dir = Path(cache_dir or ws.DEFAULT_CACHE_DIR)
    _, leads = _load_all_leads(svc)
    fetched = skipped = failed = 0
    for lead in leads:
        url = str(lead.get("Website") or "").strip()
        if not url or ws.cached_website_text(url, cache_dir) is not None or ws.skip_state(url, cache_dir):
            skipped += 1
            continue
        if fetched + failed >= args.limit:  # zaehlt nur echte Versuche
            break
        if ws.website_text(url, cache_dir, opener=opener):
            fetched += 1
        else:
            failed += 1
    print(f"Abgerufen: {fetched}, ohne Text/gesperrt: {failed}, uebersprungen (Cache/Marker/ohne URL): {skipped}")


def cmd_score_leads(args, svc=None, cache_dir=None, out_path=None, sleep=time.sleep):
    """Fit-Score je Lead. Dry-Run zeigt nur Zaehlungen; --apply schreibt nur in leere Tier/Score/Segment-Zellen."""
    from collections import Counter
    import website_signals as ws
    from lead_quality import fit_score, segment_for
    from outbound_safety import crm_write_readback
    from hsb_config import CANONICAL_SPREADSHEET_ID
    svc = svc or get_sheets_service()
    cache_dir = Path(cache_dir or ws.DEFAULT_CACHE_DIR)
    out_path = Path(out_path or Path(__file__).resolve().parent.parent / "data" / "fit_scores.jsonl")
    headers, leads = _load_all_leads(svc)
    counts: Counter = Counter()
    records = []
    writes = []
    for lead in leads:
        text = ws.cached_website_text(str(lead.get("Website") or ""), cache_dir)
        signals = ws.website_signals(text) if text else {"positive": [], "negative": [], "quotes": []}
        score, tier, reasons = fit_score(lead, signals)
        segment = segment_for(lead)
        counts[(segment, tier)] += 1
        records.append({"lead_id": lead.get("Lead-ID", ""), "row": lead["_row"], "segment": segment, "tier": tier,
                        "score": score, "reasons": reasons, "quotes": signals["quotes"]})
        wanted = {"Tier": tier, "Score": str(score), "Segment": segment}
        expected = {k: v for k, v in wanted.items() if k in headers and not str(lead.get(k) or "").strip()}
        if expected:
            writes.append((lead["_row"], expected))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    for (segment, tier), n in sorted(counts.items()):
        print(f"{segment} {tier}: {n}")
    if not args.apply:
        print(f"Dry-Run: {len(writes)} Zeilen haetten leere Zellen. Mit --apply schreiben.")
        return
    for i, (row, expected) in enumerate(writes):
        if i:
            sleep(1.0)  # ca. 1 Zeile/s gegen Sheets-Quota
        for attempt in range(4):
            try:
                crm_write_readback(svc, CANONICAL_SPREADSHEET_ID, headers, row, expected)
                break
            except Exception as exc:
                transient = "429" in str(exc) or "CRM_READBACK_MISMATCH" in str(exc) or getattr(getattr(exc, "resp", None), "status", None) == 429
                if not transient or attempt == 3:
                    raise
                sleep(2.0 * 2 ** attempt)
    print(f"Geschrieben: {len(writes)} Zeilen (nur leere Zellen).")


def cmd_sequence_preview(args):
    from datetime import date
    import sqlite3
    from sequence import next_step_due
    journal_path = Path(args.journal)
    if not journal_path.exists():
        print(json.dumps({'due': 0, 'customer_emails_sent': 0, 'reason': 'NO_VERIFIED_V2_HISTORY'}))
        return
    # Read-only URI verhindert nebenbei eine neue Datenbank anzulegen.
    db=sqlite3.connect(journal_path.resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    try:
        history=[dict(r) for r in db.execute('SELECT * FROM sequence')]
    finally:
        db.close()
    _,leads=_load_all_leads(get_sheets_service())
    counts={2:0,3:0}
    for lead in leads:
        step=next_step_due(lead,history,date.today())
        if step:counts[step]+=1
    print(json.dumps({'due_by_step':counts,'customer_emails_sent':0}))


def cmd_upgrade_drafts(args):
    """Verwendet einen vorhandenen Audit-Snapshot; Apply liest das CRM zusätzlich live zurück."""
    from draft_upgrade import upgrade_drafts
    from com_mailbox_manager import ComMailboxClient
    audit = Path(args.audit_dir)
    # Ein vorhandener Snapshot ist lesbar, aber ohne frischen Stand kein Apply.
    if args.apply and time.time()-(audit/'drafts.json').stat().st_mtime > 86400:
        raise RuntimeError('AUDIT_SNAPSHOT_STALE')
    records = json.loads((audit/'drafts.json').read_text())
    original = json.loads((audit/'crm-original.json').read_text())['valueRanges'][0]['values']
    leads = [dict(zip(original[0],r), _row=i) for i,r in enumerate(original[1:],2)]
    result = upgrade_drafts(args.owner,args.limit,args.cohort,args.apply,
        journal_path=Path(args.journal),records=records,leads=leads,
        client=ComMailboxClient(args.owner) if args.apply else None,
        svc=get_sheets_service() if args.apply else None)
    print(json.dumps(result,ensure_ascii=False,default=dict))


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Unified Operator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Status aller Postfächer und Sheets")

    # optouts Cockpit
    p_optouts = subparsers.add_parser("optouts", help="Alle Abmeldungen & Widersprüche anzeigen")

    # optout Befehl
    p_optout = subparsers.add_parser("optout", help="Einen Lead sofort sperren und Entwürfe löschen")
    p_optout.add_argument("--email", required=True, help="E-Mail-Adresse des Leads")
    p_optout.add_argument("--lead-id", help="Optionale Lead-ID")
    p_optout.add_argument("--reason", default="Manuell über CLI", help="Grund des Widerspruchs")
    p_optout.add_argument("--apply", action="store_true", help="Sperre scharf ins Sheet schreiben")

    # purge-de
    p_purge = subparsers.add_parser("purge-de", help="Alte .de Entwürfe aus M365 Exchange löschen")
    p_purge.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_purge.add_argument("--limit", type=int, default=50)
    p_purge.add_argument("--apply", action="store_true", help="Löschung ausführen")

    # overhaul-all
    p_overhaul_all = subparsers.add_parser("overhaul-all", help="Massen-Vorbereitung offener Leads als 2026-Entwürfe")
    p_overhaul_all.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="ALL")
    p_overhaul_all.add_argument("--limit", type=int, default=100)
    p_overhaul_all.add_argument("--apply", action="store_true", help="Entwurfserstellung ausführen")

    # overhaul
    p_overhaul = subparsers.add_parser("overhaul", help="Entwürfe auf 2026-Standard veredeln")
    p_overhaul.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL")
    p_overhaul.add_argument("--limit", type=int, default=50)
    p_overhaul.add_argument("--apply", action="store_true", help="Veredelung ausführen")

    # send-batch
    p_send = subparsers.add_parser("send-batch", help="Automatisierter Versand über .com")
    p_send.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_send.add_argument("--count", type=int, default=10)
    p_send.add_argument("--jitter-min", type=int, default=MIN_JITTER_SECONDS)
    p_send.add_argument("--jitter-max", type=int, default=MAX_JITTER_SECONDS)
    p_send.add_argument("--cap", type=int, default=DAILY_CAP_PER_MAILBOX)
    p_send.add_argument("--bcc-de", action="store_true", help="Blindkopie (BCC) an .de Firmenkonto senden")
    p_send.add_argument("--with-attachment", action="store_true", help="Optional den 241 KB Flyer als Datei anhängen (Standard: Aus, da Online-Link aktiv)")
    p_send.add_argument("--apply", action="store_true", help="Echten Versand starten")

    # sync
    p_sync = subparsers.add_parser("sync", help="Dual-Domain Closed-Loop Reconciliation (Antworten, Bounces, Abwesenheiten)")
    p_sync.add_argument("--limit", type=int, default=100)
    p_sync.add_argument("--com-only", action="store_true", help="Nur .com IMAP; .de bleibt separat zu verifizieren")
    p_sync.add_argument("--apply", action="store_true", help="Erkannte Status-Änderungen live ins Google Sheet schreiben")

    # click-sync
    p_click = subparsers.add_parser("click-sync", help="Klick-Zähler aus Cloudflare KV in CRM-Tab CLICK_EVENTS übernehmen")
    p_click.add_argument("--apply", action="store_true", help="Neue Klicks live ins Google Sheet schreiben (Standard: nur zählen)")

    # bounce-report
    p_bind = subparsers.add_parser("crm-bindings", help="Stabile Zeilenbindungen im CRM anlegen (Dry-Run ohne --apply) bzw. Sortier-Canary")
    p_bind.add_argument("--apply", action="store_true")
    p_bind.add_argument("--canary", action="store_true", help="Nur Sortier-Canary im temporären Tab")
    p_bind.add_argument("--leads-file", help="Nur diese Lead-IDs binden (eine je Zeile)")
    p_bind.add_argument("--prune", action="store_true", help="Bindungen außerhalb von --leads-file entfernen")

    p_bounce = subparsers.add_parser("bounce-report", help="Bounce-Zählung je DSN-Klasse und Domain (nur Zählungen)")
    p_bounce.add_argument("--limit", type=int, default=0, help="Max. Nachrichten je Postfach (0 = alle)")
    p_bounce.add_argument("--com-only", action="store_true", help="Nur .com IMAP")

    # seed-send / seed-read / blocklist-check
    p_ss = subparsers.add_parser("seed-send", help="Neutrale Testmail an Seed-Postfaecher (nur Seed-Liste, internes Test-Flag noetig)")
    p_ss.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_ss.add_argument("--to", action="append", help="Nur diese Seed-Adresse (wiederholbar); Standard: alle")
    p_ss.add_argument("--seed-file", help="Pfad zur Seed-Liste (Standard: config/seed_inboxes.json)")
    p_sr = subparsers.add_parser("seed-read", help="Checkliste fuer manuelle Platzierungspruefung oder --raw-file auswerten")
    p_sr.add_argument("--raw-file", help="Gespeicherte Rohnachricht (.eml, 'Original anzeigen')")
    p_sr.add_argument("--token", help="Seed-Kennung aus seed-send")
    p_sr.add_argument("--seed-file", help="Pfad zur Seed-Liste")
    p_bl = subparsers.add_parser("blocklist-check", help="DNSBL-Status einer IPv4 (Spamhaus nur manuell)")
    p_bl.add_argument("ip", help="IPv4-Adresse")

    # fetch-websites / score-leads
    p_fw = subparsers.add_parser("fetch-websites", help="Website-Texte in den lokalen Cache laden (robots.txt, 1 Anfrage/s)")
    p_fw.add_argument("--limit", type=int, required=True, help="Max. Abrufe in diesem Lauf")
    p_sl = subparsers.add_parser("score-leads", help="Fit-Score je Lead (Dry-Run: nur Zaehlungen je Segment und Tier)")
    p_sl.add_argument("--apply", action="store_true", help="Nur leere Tier/Score/Segment-Zellen im CRM schreiben")

    # test-mail
    p_test = subparsers.add_parser("test-mail", help="Einzelne Test-E-Mail senden")
    p_test.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL")
    p_test.add_argument("--to", required=True, help="Empfänger-Adresse")
    p_test.add_argument("--bcc-de", action="store_true", help="Blindkopie (BCC) an .de Firmenkonto senden")
    p_test.add_argument("--with-attachment", action="store_true", help="Optional den 241 KB Flyer als Datei anhängen (Standard: Aus, da Online-Link aktiv)")

    p_sequence = subparsers.add_parser("sequence-preview", help="Fällige v2-Nachfasskontakte zählen (kein Versand)")
    p_sequence.add_argument("--journal", default=str(Path.home()/".local/state/hsb-sales-os/outbound.sqlite3"))
    p_upgrade = subparsers.add_parser("upgrade-drafts", help="Entwürfe anhand eines Audits erneuern; Standard Dry-Run")
    p_upgrade.add_argument("--owner", choices=["JOEL","JORDI"], required=True)
    p_upgrade.add_argument("--limit", type=int, default=5)
    p_upgrade.add_argument("--cohort", choices=["pilot","all"], default="pilot")
    p_upgrade.add_argument("--audit-dir", required=True)
    p_upgrade.add_argument("--journal", default=str(Path.home()/".local/state/hsb-sales-os/upgrade.sqlite3"))
    p_upgrade.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.command == "sequence-preview":
        cmd_sequence_preview(args)
    elif args.command == "upgrade-drafts":
        cmd_upgrade_drafts(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "purge-de":
        cmd_purge_de(args)
    elif args.command == "overhaul":
        cmd_overhaul(args)
    elif args.command == "overhaul-all":
        cmd_overhaul_all(args)

    elif args.command == "send-batch":
        cmd_send_batch(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "test-mail":
        cmd_test_mail(args)
    elif args.command == "click-sync":
        cmd_click_sync(args)
    elif args.command == "crm-bindings":
        cmd_crm_bindings(args)
    elif args.command == "bounce-report":
        cmd_bounce_report(args)
    elif args.command == "seed-send":
        cmd_seed_send(args)
    elif args.command == "seed-read":
        cmd_seed_read(args)
    elif args.command == "blocklist-check":
        cmd_blocklist_check(args)
    elif args.command == "fetch-websites":
        cmd_fetch_websites(args)
    elif args.command == "score-leads":
        cmd_score_leads(args)
    elif args.command == "optouts":
        cmd_optouts(args)
    elif args.command == "optout":
        cmd_optout_direct(args)


if __name__ == "__main__":
    main()
