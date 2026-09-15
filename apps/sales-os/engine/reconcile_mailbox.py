#!/usr/bin/env python3
"""
HSB Sales OS - Postfach- & Sende-Abgleich (Reconciliation Engine).
Single Source of Truth im Google Sheet 'ALL_LEADS'.

Funktionen:
1. Status-Prüfung (--status):
   Zählt alle gedrafteten, gesendeten und beantworteten Leads je Absender.
2. Manuelle/Batch-Bestätigung bereits gesendeter Mails (--mark-sent):
   Setzt die Zeilen auf 'sent', stempelt Datum und aktiviert die blaue Hervorhebung.
3. Cloud API Sent-Items & Inbound Abgleich (--sync-cloud / --sync):
   Liest gesendete Mails und Antworten/Bounces direkt über den M365 Power Platform
   APIHub / Office 365 Outlook Connector und gleicht sie mit ALL_LEADS ab.
   (Ersetzt alle lokalen Apple-Mail- und osascript-Abhängigkeiten).
"""
import argparse
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from hsb_core import FLYERS, normalize_owner


def get_leads_status():
    service = get_sheets_service()
    ranges = [
        "ALL_LEADS!A2:A6425",
        "ALL_LEADS!I2:I6425",
        "ALL_LEADS!AA2:AA6425",
        "ALL_LEADS!AO2:AO6425",
        "ALL_LEADS!AP2:AP6425",
        "ALL_LEADS!AR2:AR6425",
        "ALL_LEADS!AU2:AU6425",
    ]
    res = (
        service.spreadsheets()
        .values()
        .batchGet(spreadsheetId=SPREADSHEET_ID, ranges=ranges)
        .execute()
    )
    value_ranges = res.get("valueRanges", [])

    col_a = value_ranges[0].get("values", [])
    col_i = value_ranges[1].get("values", [])
    col_aa = value_ranges[2].get("values", [])
    col_ao = value_ranges[3].get("values", [])
    col_ap = value_ranges[4].get("values", [])
    col_ar = value_ranges[5].get("values", [])
    col_au = value_ranges[6].get("values", [])

    n = max(len(col_a), len(col_i), len(col_aa), len(col_ao))
    leads = []
    for idx in range(n):
        row_num = idx + 2
        lead_id = col_a[idx][0] if idx < len(col_a) and col_a[idx] else ""
        email = col_i[idx][0] if idx < len(col_i) and col_i[idx] else ""
        owner_raw = col_aa[idx][0] if idx < len(col_aa) and col_aa[idx] else ""
        send_status = col_ao[idx][0] if idx < len(col_ao) and col_ao[idx] else ""
        send_datum = col_ap[idx][0] if idx < len(col_ap) and col_ap[idx] else ""
        reply_status = col_ar[idx][0] if idx < len(col_ar) and col_ar[idx] else ""
        batch_status = col_au[idx][0] if idx < len(col_au) and col_au[idx] else ""

        leads.append(
            {
                "row": row_num,
                "lead_id": lead_id,
                "email": email,
                "owner": normalize_owner(owner_raw),
                "owner_raw": owner_raw,
                "send_status": send_status,
                "send_datum": send_datum,
                "reply_status": reply_status,
                "batch_status": batch_status,
            }
        )
    return leads


def print_status():
    leads = get_leads_status()

    joel_leads = [l for l in leads if l["owner"] == "JOEL"]
    jordi_leads = [l for l in leads if l["owner"] == "JORDI"]

    def stats(subset):
        drafted = sum(
            1
            for l in subset
            if l["send_status"] == "drafted" or l["batch_status"] == "DRAFTED"
        )
        sent = sum(
            1
            for l in subset
            if l["send_status"] == "sent" or l["batch_status"] == "SENT"
        )
        replied = sum(
            1
            for l in subset
            if l["reply_status"] in ["reply", "replied", "auto_reply_ooo", "positive_reply"]
        )
        return len(subset), drafted, sent, replied

    t_all, d_all, s_all, r_all = stats(leads)
    t_joel, d_joel, s_joel, r_joel = stats(joel_leads)
    t_jordi, d_jordi, s_jordi, r_jordi = stats(jordi_leads)

    print("\n================================================================================")
    print(" HSB SALES OS — CRM STATUS & SENDE-MONITOR (Single Source of Truth)")
    print("================================================================================")
    print(f"{'Metrik':<30} | {'Gesamt':<10} | {'Joel Cherino':<15} | {'Jordie Post':<15}")
    print("-" * 80)
    print(f"{'Kontakte in Datenbank':<30} | {t_all:<10} | {t_joel:<15} | {t_jordi:<15}")
    print(f"{'Entwürfe in Outlook (DRAFTED)':<30} | {d_all:<10} | {d_joel:<15} | {d_jordi:<15}")
    print(f"{'Tatsächlich versendet (BLAU)':<30} | {s_all:<10} | {s_joel:<15} | {s_jordi:<15}")
    print(f"{'Antworten erhalten (GRÜN)':<30} | {r_all:<10} | {r_joel:<15} | {r_jordi:<15}")
    print("================================================================================\n")


def mark_rows_sent(start_row: int, end_row: int, send_timestamp: str = None):
    if not send_timestamp:
        send_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    service = get_sheets_service()
    count = end_row - start_row + 1
    print(f"Markiere Zeilen {start_row} bis {end_row} ({count} Zeilen) als 'sent'...")

    ao_ap_range = f"ALL_LEADS!AO{start_row}:AP{end_row}"
    ao_ap_values = [["sent", send_timestamp] for _ in range(count)]

    au_range = f"ALL_LEADS!AU{start_row}:AU{end_row}"
    au_values = [["SENT"] for _ in range(count)]

    bd_range = f"ALL_LEADS!BD{start_row}:BD{end_row}"
    bd_values = [[""] for _ in range(count)]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": ao_ap_range, "values": ao_ap_values},
                {"range": au_range, "values": au_values},
                {"range": bd_range, "values": bd_values},
            ],
        },
    ).execute()

    print(f"ERFOLG: {count} Zeilen erfolgreich auf 'sent' gesetzt. Blaue Formatierung ist aktiv!")


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Postfach- und Sende-Abgleich")
    parser.add_argument("--status", action="store_true", help="Zeigt aktuellen Status aller Leads im CRM an")
    parser.add_argument(
        "--mark-sent",
        nargs=2,
        type=int,
        metavar=("START_ROW", "END_ROW"),
        help="Markiert Zeilenbereich als versendet (z.B. --mark-sent 52 71)",
    )
    parser.add_argument(
        "--mark-sent-owner",
        choices=["JOEL", "JORDI"],
        help="Markiert erste N Entwürfe eines Absenders als versendet",
    )
    parser.add_argument("--count", type=int, default=10, help="Anzahl für --mark-sent-owner (Standard: 10)")
    parser.add_argument(
        "--sync-cloud",
        "--sync",
        action="store_true",
        help="Synchronisiert reale gesendete Mails und Bounces direkt ueber M365 Power Platform APIHub (Cloud)",
    )
    parser.add_argument(
        "--owner",
        choices=["JOEL", "JORDI"],
        help="Filter fuer Cloud-Synchronisation auf bestimmten Absender",
    )
    parser.add_argument(
        "--sync-apple-mail",
        action="store_true",
        help="DEPRECATED: Leitet automatisch auf den Cloud-Native Sync um (kein Apple Mail / osascript)",
    )
    args = parser.parse_args()

    if args.sync_cloud or args.sync_apple_mail:
        if args.sync_apple_mail:
            print("[INFO] Apple Mail ist abgeloest durch Cloud-Native Sync via APIHub. Führe Cloud-Sync aus...")
        from reconcile_cloud_mailbox import run_cloud_sync
        run_cloud_sync(target_owner=args.owner)
        print_status()
    elif args.mark_sent:
        mark_rows_sent(args.mark_sent[0], args.mark_sent[1])
        print_status()
    elif args.mark_sent_owner:
        leads = get_leads_status()
        owner_drafts = [
            l
            for l in leads
            if l["owner"] == args.mark_sent_owner and l["send_status"] == "drafted"
        ]
        if not owner_drafts:
            print(f"Keine offenen Entwürfe für {args.mark_sent_owner} gefunden.")
            return
        selected = owner_drafts[: args.count]
        start_row = selected[0]["row"]
        end_row = selected[-1]["row"]
        print(f"Gefundene Entwürfe für {args.mark_sent_owner}: Zeilen {start_row} bis {end_row}")
        mark_rows_sent(start_row, end_row)
        print_status()
    else:
        print_status()


if __name__ == "__main__":
    main()
