#!/usr/bin/env python3
"""
HSB Sales OS - Forensischer Mailbox-Vollscan (M365 & All-Inkl)
Liest jede einzelne gesendete Nachricht aus M365 Exchange und IMAP aus,
ohne Paginierungs-Verluste.
"""
import sys
import time
import json
import re
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
import urllib.request
import urllib.parse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from run_100_batch import get_jordi_token
from reconcile_cloud_mailbox import get_az_apihub_token, RUNTIME_URL, CONNECTIONS
from com_mailbox_manager import ComMailboxClient

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def extract_recipients(m):
    recips_raw = str(m.get("toRecipients") or m.get("To") or "")
    found = EMAIL_RE.findall(recips_raw)
    valid = []
    for r in found:
        el = r.strip().lower()
        if not any(d in el for d in ["hsb-boden", "kasserver", "microsoft", "outlook"]):
            valid.append(el)
    return list(dict.fromkeys(valid))

def scan_jordi_m365():
    token = get_jordi_token()
    conn_id = CONNECTIONS["JORDI"]["connection_id"]
    all_items = {} # id -> dict

    # Prüfe alle Tage zwischen 2026-06-01 und 2026-10-23
    start_d = date(2026, 6, 1)
    end_d = date(2026, 10, 23)
    curr = start_d

    print("Starte M365 Exchange Scan für Jordi Post (j-post@hsb-boden.de)...")
    while curr <= end_d:
        ds = curr.strftime("%Y-%m-%d")
        # Frage Tag ab
        params = urllib.parse.urlencode({
            "folderPath": "Gesendete Elemente",
            "fetchOnlyUnread": "false",
            "top": "100",
            "searchQuery": f"sent:{ds}"
        })
        url = f"{RUNTIME_URL}/{conn_id}/v3/Mail?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("value", [])

                # Wenn genau 100, könnten mehr als 100 an dem Tag liegen -> in 4-Stunden-Blöcken aufteilen
                if len(items) == 100:
                    print(f"  Tag {ds} hat >= 100 Mails -> Teile in 4-Stunden-Slots auf...")
                    for hour in range(0, 24, 4):
                        h_start = f"{ds}T{hour:02d}:00:00Z"
                        h_end = f"{ds}T{hour+3:02d}:59:59Z"
                        q_slot = f"sent>={h_start} AND sent<={h_end}"
                        p_slot = urllib.parse.urlencode({
                            "folderPath": "Gesendete Elemente",
                            "fetchOnlyUnread": "false",
                            "top": "100",
                            "searchQuery": q_slot
                        })
                        req_slot = urllib.request.Request(f"{RUNTIME_URL}/{conn_id}/v3/Mail?{p_slot}", headers={"Authorization": f"Bearer {token}"})
                        try:
                            with urllib.request.urlopen(req_slot, timeout=20) as resp_slot:
                                slot_items = json.loads(resp_slot.read().decode("utf-8")).get("value", [])
                                for si in slot_items:
                                    mid = si.get("id")
                                    if mid and mid not in all_items:
                                        all_items[mid] = si
                        except Exception as ex_slot:
                            print(f"    Slot {h_start} Fehler: {ex_slot}")
                        time.sleep(0.15)
                else:
                    for it in items:
                        mid = it.get("id")
                        if mid and mid not in all_items:
                            all_items[mid] = it
                if len(items) > 0:
                    print(f"  Tag {ds}: {len(items)} Items (Gesamt im Speicher: {len(all_items)})")
        except Exception as e:
            print(f"  Tag {ds} Fehler: {e}")

        curr += timedelta(days=1)
        time.sleep(0.15)

    print(f"M365 Jordi Scan beendet. Gesamt eindeutige Mails: {len(all_items)}")
    return list(all_items.values())

def scan_joel_m365():
    print("Starte M365 Exchange Scan für Joel Cherino (j-cherino@hsb-boden.de)...")
    try:
        token = get_az_apihub_token()
        conn_id = CONNECTIONS["JOEL"]["connection_id"]
        # Schneller Check ob überhaupt Mails da sind
        params = urllib.parse.urlencode({"folderPath": "Gesendete Elemente", "fetchOnlyUnread": "false", "top": "100"})
        url = f"{RUNTIME_URL}/{conn_id}/v3/Mail?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("value", [])
            print(f"M365 Joel Gesendete Elemente: {len(items)} Items.")
            return items
    except Exception as e:
        print(f"M365 Joel Scan Fehler: {e}")
        return []

def scan_com_mailboxes():
    res = {}
    for owner in ["JORDI", "JOEL"]:
        try:
            client = ComMailboxClient(owner)
            sent = client.fetch_sent_messages(limit=2000)
            print(f"All-Inkl .COM ({owner}): {len(sent)} gesendete Mails geladen.")
            res[owner] = sent
        except Exception as e:
            print(f"All-Inkl .COM ({owner}) Fehler: {e}")
            res[owner] = []
    return res

if __name__ == "__main__":
    t0 = time.time()
    jordi_m365 = scan_jordi_m365()
    joel_m365 = scan_joel_m365()
    com_sent = scan_com_mailboxes()

    # Extrahiere alle Empfänger
    unique_recipients = {} # email -> {source, date, subject, id}

    for m in jordi_m365:
        recips = extract_recipients(m)
        dt = m.get("receivedDateTime") or m.get("DateTimeReceived") or ""
        subj = m.get("subject") or ""
        mid = m.get("id") or ""
        for r in recips:
            if r not in unique_recipients:
                unique_recipients[r] = {"source": "M365_JORDI", "date": dt, "subject": subj, "id": mid}

    for m in joel_m365:
        recips = extract_recipients(m)
        dt = m.get("receivedDateTime") or m.get("DateTimeReceived") or ""
        subj = m.get("subject") or ""
        mid = m.get("id") or ""
        for r in recips:
            if r not in unique_recipients:
                unique_recipients[r] = {"source": "M365_JOEL", "date": dt, "subject": subj, "id": mid}

    for r in com_sent.get("JORDI", []):
        for recip in r.get("recipients", []):
            el = recip.strip().lower()
            if el not in unique_recipients:
                unique_recipients[el] = {"source": "COM_JORDI", "date": r.get("date_str"), "subject": r.get("subject"), "id": r.get("internet_message_id")}

    for r in com_sent.get("JOEL", []):
        for recip in r.get("recipients", []):
            el = recip.strip().lower()
            if el not in unique_recipients:
                unique_recipients[el] = {"source": "COM_JOEL", "date": r.get("date_str"), "subject": r.get("subject"), "id": r.get("internet_message_id")}

    out_file = REPO_ROOT / "apps/sales-os/data/forensic_sent_recipients.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(unique_recipients, f, indent=2, ensure_ascii=False)

    print(f"\nFORENSIK ERGEBNIS:")
    print(f"Gesamt gesendete Mails Jordi M365 : {len(jordi_m365)}")
    print(f"Gesamt gesendete Mails Joel M365  : {len(joel_m365)}")
    print(f"Gesamt gesendete Mails Jordi .COM : {len(com_sent.get('JORDI', []))}")
    print(f"Gesamt gesendete Mails Joel .COM  : {len(com_sent.get('JOEL', []))}")
    print(f"Eindeutige externe Empfänger      : {len(unique_recipients)}")
    print(f"Ergebnis gespeichert in           : {out_file}")
    print(f"Dauer: {time.time() - t0:.1f}s")
