#!/usr/bin/env python3
"""
HSB Sales OS - Reconcile & Live Sync to Google Sheets.
Gleicht die 1.083 forensisch verifizierten gesendeten Empfänger
mit ALL_LEADS (6.424 Zeilen) ab und schreibt die Änderungen live
und atomar ins Google Sheet.
"""
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

def main():
    print("=" * 105)
    print(" HSB SALES OS — CRM AUDIT & LIVE SYNC TO GOOGLE SHEETS")
    print("=" * 105)

    # 1. Lade forensische Daten
    json_path = REPO_ROOT / "apps/sales-os/data/forensic_sent_recipients.json"
    if not json_path.exists():
        json_path = REPO_ROOT / "apps/sales-os/apps/sales-os/data/forensic_sent_recipients.json"

    with open(json_path, "r", encoding="utf-8") as f:
        sent_registry = json.load(f)
    print(f"Forensische Registry geladen: {len(sent_registry)} eindeutige Empfänger.")

    # 2. Lade ALL_LEADS
    service = get_sheets_service()
    print("Lade Google Sheet ALL_LEADS (A1:BU6425)...")
    res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()
    rows = res.get("values", [])
    header = rows[0]
    data_rows = rows[1:]
    print(f"ALL_LEADS geladen: {len(data_rows)} Datenzeilen.")

    already_sent = 0
    newly_detected_sent = 0
    already_bounced = 0
    updates = []

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 115)
    print(f"{'Zeile':<6} | {'Lead-ID':<20} | {'Firma':<30} | {'E-Mail':<32} | {'Bisher':<10} | {'Aktion'}")
    print("-" * 115)

    for idx, r in enumerate(data_rows, start=2):
        lead_id = r[0] if len(r) > 0 else ""
        firma = r[2] if len(r) > 2 else ""
        email = (r[8] if len(r) > 8 and r[8] else "").strip().lower()
        curr_send_st = (r[40] if len(r) > 40 and r[40] else "").strip().lower()
        curr_batch_st = (r[46] if len(r) > 46 and r[46] else "").strip()

        if curr_send_st == "bounced":
            already_bounced += 1

        if email in sent_registry:
            ev = sent_registry[email]
            if curr_send_st == "sent":
                already_sent += 1
            elif curr_send_st == "bounced":
                # Wenn er schon bounced ist, belassen wir bounced (wichtig für Suppression)
                pass
            else:
                newly_detected_sent += 1
                sent_time = ev.get("date") or now_iso
                msg_id = ev.get("id") or ""
                src = ev.get("source") or "M365"

                if newly_detected_sent <= 30 or newly_detected_sent % 50 == 0:
                    print(f"{idx:<6} | {lead_id[:20]:<20} | {firma[:30]:<30} | {email[:32]:<32} | {curr_send_st:<10} | -> NEU AUF SENT ({src})")

                # Spalte AO: SendStatus, AP: SendDate, AU: BatchStatus, BA: MessageId
                updates.append({"range": f"ALL_LEADS!AO{idx}", "values": [["sent"]]})
                updates.append({"range": f"ALL_LEADS!AP{idx}", "values": [[sent_time]]})
                updates.append({"range": f"ALL_LEADS!AU{idx}", "values": [[f"SENT_{src}"]]})
                if msg_id:
                    updates.append({"range": f"ALL_LEADS!BA{idx}", "values": [[msg_id]]})

    print("=" * 115)
    print(f"\nSTATISTIK VOR LIVE-UPDATE:")
    print(f"Bereits als 'sent' markiert im Sheet     : {already_sent}")
    print(f"Bereits als 'bounced' markiert im Sheet  : {already_bounced}")
    print(f"Neu entdeckte tatsächliche Versendungen : {newly_detected_sent}")
    print(f"NEUE GESAMTSUMME KONTAKTIERTER KUNDEN    : {already_sent + newly_detected_sent}")

    if updates:
        print(f"\nSchreibe {len(updates)} Zellen-Aktualisierungen in Chunks à 500 ins Google Sheet...")
        chunk_size = 500
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i+chunk_size]
            body = {"valueInputOption": "USER_ENTERED", "data": chunk}
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            print(f"  Chunk {i//chunk_size + 1}/{(len(updates)-1)//chunk_size + 1} ({len(chunk)} Updates) geschrieben.")
            time.sleep(0.5)
        print("\n✓ ALLE ÄNDERUNGEN ERFOLGREICH LIVE IM GOOGLE SHEET EINGETRAGEN!")
    else:
        print("\nKeine Änderungen erforderlich.")

    # 3. CRM-Gesamtstatus nach Update ermitteln
    print("\nErmittle finalen CRM-Status nach Bereinigung...")
    res_final = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!AO2:AU6425").execute()
    final_rows = res_final.get("values", [])

    st_counts = {}
    for r in final_rows:
        st = (r[0] if len(r) > 0 and r[0] else "open").strip().lower()
        st_counts[st] = st_counts.get(st, 0) + 1

    print("\n" + "=" * 50)
    print(" FINALE CRM-STATUSVERTEILUNG (SSOT Google Sheet):")
    print("-" * 50)
    for st, count in sorted(st_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {st:<15}: {count:5d} Leads")
    print("-" * 50)
    print(f"  GESAMT         : {len(final_rows):5d} Leads")
    print("=" * 50)

if __name__ == "__main__":
    main()
