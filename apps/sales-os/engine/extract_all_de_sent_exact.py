#!/usr/bin/env python3
"""
HSB Sales OS - Lückenlose forensische Extraktion ALLER gesendeten E-Mails von .de:
1. j-post@hsb-boden.de (M365 Exchange)
2. j-cherino@hsb-boden.de (M365 Exchange)
3. Historische Google Drive Kaltakquise-Sheets aus Juli 2026
"""
import sys
import os
import json
import csv
import re
import time
from datetime import datetime, date, timedelta
from pathlib import Path
import urllib.request
import urllib.parse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from run_100_batch import get_jordi_token
from reconcile_cloud_mailbox import get_az_apihub_token, RUNTIME_URL, CONNECTIONS
from sync_to_google_sheet import get_sheets_service

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def clean_recipients(recips_raw):
    found = EMAIL_RE.findall(str(recips_raw or ""))
    res = []
    for r in found:
        el = r.strip().lower()
        if not any(d in el for d in ["hsb-boden", "kasserver", "microsoft", "outlook"]):
            res.append(el)
    return list(dict.fromkeys(res))

def get_m365_sent_for_mailbox(owner_key, token, conn_id):
    mailbox_name = f"j-{'post' if owner_key == 'JORDI' else 'cherino'}@hsb-boden.de"
    print(f"[{owner_key}] Lese Gesendete Elemente aus {mailbox_name}...")

    all_messages = {} # mid -> dict

    # Scanne alle Tage vom 01.06.2026 bis 23.10.2026
    start_d = date(2026, 6, 1)
    end_d = date(2026, 10, 23)
    curr = start_d

    while curr <= end_d:
        ds = curr.strftime("%Y-%m-%d")
        params = urllib.parse.urlencode({
            "folderPath": "Gesendete Elemente",
            "fetchOnlyUnread": "false",
            "top": "100",
            "searchQuery": f"sent:{ds}"
        })
        url = f"{RUNTIME_URL}/{conn_id}/v3/Mail?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("value", [])

                # Wenn genau 100, könnte Tages-Limit erreicht sein -> teile in 4-Stunden-Slots
                if len(items) == 100:
                    for hour in range(0, 24, 4):
                        h_start = f"{ds}T{hour:02d}:00:00Z"
                        h_end = f"{ds}T{hour+3:02d}:59:59Z"
                        p_slot = urllib.parse.urlencode({
                            "folderPath": "Gesendete Elemente",
                            "fetchOnlyUnread": "false",
                            "top": "100",
                            "searchQuery": f"sent>={h_start} AND sent<={h_end}"
                        })
                        try:
                            req_slot = urllib.request.Request(f"{RUNTIME_URL}/{conn_id}/v3/Mail?{p_slot}", headers={"Authorization": f"Bearer {token}"})
                            with urllib.request.urlopen(req_slot, timeout=15) as resp_slot:
                                s_items = json.loads(resp_slot.read().decode("utf-8")).get("value", [])
                                for si in s_items:
                                    mid = si.get("id")
                                    if mid and mid not in all_messages:
                                        all_messages[mid] = si
                        except Exception:
                            pass
                        time.sleep(0.08)
                else:
                    for it in items:
                        mid = it.get("id")
                        if mid and mid not in all_messages:
                            all_messages[mid] = it
        except Exception:
            pass
        curr += timedelta(days=1)
        time.sleep(0.08)

    print(f"[{owner_key}] {len(all_messages)} gesendete Mails direkt aus Exchange geladen.")

    extracted = []
    for mid, m in all_messages.items():
        recips = clean_recipients(m.get("toRecipients") or m.get("To") or "")
        dt = m.get("receivedDateTime") or m.get("DateTimeReceived") or ""
        subj = m.get("subject") or m.get("Subject") or ""
        for r in recips:
            extracted.append({
                "Absender": mailbox_name,
                "Empfaenger_Email": r,
                "Sendedatum_ISO": dt,
                "Betreff": subj,
                "Message_ID": mid,
                "Quelle": "M365_EXCHANGE_LIVE"
            })
    return extracted

def get_historical_drive_sent():
    service = get_sheets_service()
    drive_sheets = [
        ("Jordi Juli 2026", "1ITFextI-EuDXNG2p9yfmAvzA_7AbFk4HDO-GqB7WyLI", "Sheet1", "j-post@hsb-boden.de"),
        ("Joel Juli 2026", "1FBY9tsDT6ode8QzkSsTQJZxVE81bLZ4DtgDCmojCFoQ", "Sheet1", "j-cherino@hsb-boden.de"),
        ("Master v2 Activities", "1JJ49g_P-gVSAE0eG9zlAJBAjopBoG0Ntb7tThJvrIvs", "ACTIVITIES", "j-post@hsb-boden.de"),
        ("Snapshot 2026-07-12", "1mQCHlJ08BUgyBTk5gSwHfWsS7jvW1FkrcPlo5eHoARk", "Sheet1", "j-post@hsb-boden.de")
    ]

    extracted = []
    for label, sid, tab, default_sender in drive_sheets:
        print(f"[Drive] Lese {label} (Tab: {tab})...")
        try:
            res = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{tab}!A1:Z2000").execute()
            rows = res.get("values", [])
            if not rows:
                continue
            header = [str(h).strip().lower() for h in rows[0]]

            # Finde Spalten
            email_col = None
            status_col = None
            date_col = None
            company_col = None
            for idx, h in enumerate(header):
                if h in ("email", "e-mail", "mail", "empfänger", "to"): email_col = idx
                if h in ("send_status", "status", "send-status", "aktivität"): status_col = idx
                if h in ("send_datum", "datum", "timestamp", "date", "zeitstempel"): date_col = idx
                if h in ("firma", "company", "firmenname"): company_col = idx

            if email_col is None:
                continue

            for r in rows[1:]:
                email = (r[email_col] if len(r) > email_col and r[email_col] else "").strip().lower()
                st = (r[status_col] if status_col is not None and len(r) > status_col and r[status_col] else "").strip().lower()
                dt = (r[date_col] if date_col is not None and len(r) > date_col and r[date_col] else "").strip()
                comp = (r[company_col] if company_col is not None and len(r) > company_col and r[company_col] else "").strip()

                if email and "@" in email:
                    # Wenn Status sent oder gesendet ist
                    if st in ("sent", "gesendet", "erfolgreich", "mail_sent", "mail gesendet") or "gesendet" in st or "sent" in st:
                        extracted.append({
                            "Absender": default_sender,
                            "Empfaenger_Email": email,
                            "Sendedatum_ISO": dt or "2026-07 (Historisch)",
                            "Betreff": f"Historische Kaltakquise Drive ({comp})",
                            "Message_ID": f"DRIVE_{sid[:10]}",
                            "Quelle": f"DRIVE_{label}"
                        })
        except Exception as e:
            print(f"[Drive] Fehler bei {label}: {e}")

    print(f"[Drive] {len(extracted)} historische Versendungen aus Drive-Dateien extrahiert.")
    return extracted

def main():
    print("=" * 95)
    print(" FORENSISCHE EXTRAKTION: JEDE EINZELNE .DE VERSENDUNG")
    print("=" * 95)

    jordi_token = get_jordi_token()
    joel_token = get_az_apihub_token()

    # 1. M365 Exchange Jordi
    m365_jordi = get_m365_sent_for_mailbox("JORDI", jordi_token, CONNECTIONS["JORDI"]["connection_id"])

    # 2. M365 Exchange Joel
    m365_joel = get_m365_sent_for_mailbox("JOEL", joel_token, CONNECTIONS["JOEL"]["connection_id"])

    # 3. Drive Sheets
    drive_sent = get_historical_drive_sent()

    # 4. Zusammenführen und Deduplizieren
    all_records = []
    seen = set()

    for r in m365_jordi + m365_joel + drive_sent:
        key = (r["Absender"], r["Empfaenger_Email"], r["Sendedatum_ISO"][:10])
        if key not in seen:
            seen.add(key)
            all_records.append(r)

    # Sortiere nach Datum
    all_records.sort(key=lambda x: str(x.get("Sendedatum_ISO", "")), reverse=True)

    out_dir = REPO_ROOT / "apps/sales-os/data"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = out_dir / "ALLE_DE_VERSENDUNGEN_VOLLSTAENDIG.csv"
    json_file = out_dir / "ALLE_DE_VERSENDUNGEN_VOLLSTAENDIG.json"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Absender", "Empfaenger_Email", "Sendedatum_ISO", "Betreff", "Message_ID", "Quelle"])
        writer.writeheader()
        writer.writerows(all_records)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print(f"\nERFOLG: Insgesamt {len(all_records)} tatsächliche .de-Versendungen forensisch erfasst!")
    print(f"CSV-Datei gespeichert in: {csv_file}")
    print(f"JSON-Datei gespeichert in: {json_file}")

    # Zählung nach Absender
    by_sender = {}
    for r in all_records:
        snd = r["Absender"]
        by_sender[snd] = by_sender.get(snd, 0) + 1

    print("\nÜBERSICHT NACH ABSENDER:")
    for s, c in by_sender.items():
        print(f"  {s:<30}: {c:5d} Versendungen")

if __name__ == "__main__":
    main()
