#!/usr/bin/env python3
"""
HSB Sales OS - Rapid .COM Batch Runner CLI.
Injiziert Akquise-Entwuerfe atomar per IMAP-SSL direkt in das .com-Postfach auf KASServer.
Aktualisiert anschliessend das Google Sheet ALL_LEADS (2D-Matrix Bulk).
"""
from __future__ import annotations

import argparse
import datetime
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from com_batch_selector import select_com_eligible_leads
from com_mailbox_manager import ComMailboxClient
from canonical_template_factory import render_canonical_email
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

try:
    from high_volume_matrix_engine import load_leads_authoritative, write_2d_matrix_bulk
except ImportError:
    load_leads_authoritative = None
    write_2d_matrix_bulk = None


def run_com_batch_in_memory(
    leads: List[Dict[str, Any]],
    owner: str = "JOEL",
    limit: int = 50,
    dry_run: bool = True
) -> Dict[str, Any]:
    """In-Memory Ausfuehrung fuer Tests und Vorschau."""
    selected = select_com_eligible_leads(leads, owner=owner, limit=limit)
    if not selected:
        return {"status": "NO_ELIGIBLE_LEADS", "selected_count": 0, "manifest": []}

    client = None if dry_run else ComMailboxClient(owner)
    manifest = []
    norm_owner = owner.strip().upper()
    sender_email = "j-cherino@hsb-boden.com" if norm_owner in ("JOEL", "J-CHERINO") else "j-post@hsb-boden.com"

    for lead in selected:
        email_data = render_canonical_email(lead, owner=owner, domain="com")
        item = {
            "lead_id": lead.get("Lead_ID") or lead.get("Lead-ID"),
            "row_idx": lead.get("row_idx") or lead.get("_row"),
            "to": email_data["to_address"],
            "subject": email_data["subject"],
            "sender": sender_email,
            "flyer_filename": "HSB-HEXAGON-Industrieboeden-Flyer.pdf",
        }
        if not dry_run and client:
            ok, mid = client.create_draft(
                to_email=email_data["to_address"],
                subject=email_data["subject"],
                body_html=email_data["body_html"],
                flyer_path=email_data["flyer_path"],
                flyer_filename=email_data["flyer_filename"]
            )
            item["message_id"] = mid
            item["status"] = "DRAFTED"
        else:
            item["status"] = "DRY_RUN"

        manifest.append(item)

    status_str = "SUCCESS_DRY_RUN" if dry_run else "SUCCESS_LIVE"
    return {"status": status_str, "selected_count": len(manifest), "manifest": manifest}


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS .COM Rapid Batch Runner")
    parser.add_argument("--owner", choices=["JOEL", "JORDI"], default="JOEL", help="Verantwortlicher (JOEL oder JORDI)")
    parser.add_argument("--count", type=int, default=10, help="Anzahl der zu erstellenden Entwuerfe")
    parser.add_argument("--apply", action="store_true", help="Scharf schalten: Reale IMAP-Injektion und Sheet-Writeback")
    args = parser.parse_args()

    print("=" * 80)
    print(f" HSB SALES OS — .COM RAPID BATCH RUNNER (Owner: {args.owner}, Count: {args.count})")
    print("=" * 80)

    if not load_leads_authoritative:
        print("❌ Fehlende Abhängigkeit: load_leads_authoritative nicht gefunden.")
        sys.exit(1)

    print("⏳ Lade Leads aus Google Sheet 'ALL_LEADS' ...")
    raw_leads = load_leads_authoritative()
    print(f"✅ {len(raw_leads)} Leads geladen.")

    dry_run = not args.apply
    if dry_run:
        print("ℹ️  Modus: DRY-RUN (Vorschau). Keine Entwuerfe erstellt, kein Sheet-Writeback.")
    else:
        print("🚀 Modus: APPLY LIVE. Entwuerfe werden im .com Postfach angelegt!")

    result = run_com_batch_in_memory(raw_leads, owner=args.owner, limit=args.count, dry_run=dry_run)
    print(f"Ergebnis: {result['status']}, Ausgewählte Leads: {result['selected_count']}")

    for idx, item in enumerate(result["manifest"], 1):
        print(f" [{idx:02d}] {item['lead_id']} -> {item['to']} ({item['subject']})")

    if args.apply and result["selected_count"] > 0:
        print("⏳ Aktualisiere Google Sheet ALL_LEADS ...")
        try:
            sheets_svc = get_sheets_service()
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            batch_id = f"COM-{args.owner}-{ts[:8]}"
            sheet_updates = []
            for item in result["manifest"]:
                row_num = item["row_idx"]
                msg_id = item.get("message_id", "")
                sheet_updates.append({"range": f"ALL_LEADS!AN{row_num}", "values": [[batch_id]]})
                sheet_updates.append({"range": f"ALL_LEADS!AO{row_num}", "values": [["drafted"]]})
                sheet_updates.append({"range": f"ALL_LEADS!AU{row_num}", "values": [["DRAFTED_COM_2026"]]})
                sheet_updates.append({"range": f"ALL_LEADS!AW{row_num}", "values": [[msg_id]]})
                sheet_updates.append({"range": f"ALL_LEADS!AX{row_num}", "values": [[now_iso]]})
                sheet_updates.append({"range": f"ALL_LEADS!BA{row_num}", "values": [[msg_id]]})
            if sheet_updates:
                sheets_svc.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"valueInputOption": "USER_ENTERED", "data": sheet_updates}
                ).execute()
                print(f"✅ Sheet erfolgreich mit {len(sheet_updates)} Zellen-Updates aktualisiert.")
        except Exception as e:
            print(f"⚠ Fehler beim Sheet-Update: {e}")

    print("=" * 80)


if __name__ == "__main__":
    main()
