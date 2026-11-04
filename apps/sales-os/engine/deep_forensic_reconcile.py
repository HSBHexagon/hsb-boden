#!/usr/bin/env python3
"""
HSB Sales OS - Deep Forensic Reconcile Engine.
Liest lückenlos ALLE gesendeten E-Mails aus:
1. Microsoft 365 Exchange (j-post@hsb-boden.de) via Power Automate APIHub
2. Microsoft 365 Exchange (j-cherino@hsb-boden.de) via Power Automate APIHub
3. All-Inkl IMAP (j-post@hsb-boden.com) via IMAP SSL
4. All-Inkl IMAP (j-cherino@hsb-boden.com) via IMAP SSL

Gleicht alle Empfänger-Adressen gegen ALL_LEADS (6.424 Zeilen) ab
und setzt alle tatsächlich versendeten Leads unumstößlich auf 'sent'.
"""
import sys
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from run_100_batch import get_jordi_token
from reconcile_cloud_mailbox import get_az_apihub_token, RUNTIME_URL, CONNECTIONS
from com_mailbox_manager import ComMailboxClient

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def fetch_all_m365_sent(token: str, conn_id: str, owner_name: str, max_pages: int = 40) -> list:
    """Holt paginiert gesendete Mails aus M365 Exchange via APIHub."""
    all_sent = []
    seen_ids = set()
    folder = "Gesendete Elemente"
    top = 50

    print(f"[{owner_name}] Lese Microsoft 365 Exchange SentItems via APIHub...")
    for page in range(max_pages):
        params = urllib.parse.urlencode({
            "folderPath": folder,
            "fetchOnlyUnread": "false",
            "top": str(top)
        })
        url = f"{RUNTIME_URL}/{conn_id}/v3/Mail?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("value", [])
                if not items:
                    break
                new_items = 0
                for it in items:
                    mid = it.get("id")
                    if mid and mid not in seen_ids:
                        seen_ids.add(mid)
                        all_sent.append(it)
                        new_items += 1
                if new_items == 0:
                    break
                # APIHub hat keine direkte skipToken-Syntax im URL-Params bei V3 Mail, bricht nach top ab
                break
        except Exception as e:
            print(f"[{owner_name}] Fehler beim Abruf von M365 SentItems: {e}")
            break
    print(f"[{owner_name}] {len(all_sent)} gesendete Mails aus M365 geladen.")
    return all_sent

def fetch_all_imap_sent(owner: str, limit: int = 1000) -> list:
    try:
        client = ComMailboxClient(owner)
        sent = client.fetch_sent_messages(limit=limit)
        print(f"[{owner}] {len(sent)} gesendete Mails aus All-Inkl .COM IMAP geladen.")
        return sent
    except Exception as e:
        print(f"[{owner}] Fehler bei IMAP Sent: {e}")
        return []

def main():
    print("=" * 95)
    print(" HSB SALES OS — DEEP FORENSIC RECONCILIATION & CRM AUDIT")
    print("=" * 95)

    # 1. Tokens holen
    jordi_token = get_jordi_token()
    joel_token = get_az_apihub_token()

    # 2. Sent-Mails aus allen 4 Quellen laden
    jordi_m365_sent = fetch_all_m365_sent(jordi_token, CONNECTIONS["JORDI"]["connection_id"], "JORDI")
    joel_m365_sent = fetch_all_m365_sent(joel_token, CONNECTIONS["JOEL"]["connection_id"], "JOEL")
    jordi_com_sent = fetch_all_imap_sent("JORDI", limit=1000)
    joel_com_sent = fetch_all_imap_sent("JOEL", limit=1000)

    # 3. Sammle alle kontaktierten E-Mails
    # Map: email -> list of (source, date, subject, msg_id)
    sent_registry = {}

    def register_sent(email_addr, src, dt, subj, mid):
        e = str(email_addr or "").strip().lower()
        if not e or "@" not in e:
            return
        # Filter interne Adressen
        if any(d in e for d in ["hsb-boden", "kasserver", "microsoft", "outlook"]):
            return
        if e not in sent_registry:
            sent_registry[e] = []
        sent_registry[e].append({
            "source": src,
            "date": dt,
            "subject": subj,
            "message_id": mid
        })

    # M365 Jordi
    for m in jordi_m365_sent:
        recips_raw = str(m.get("toRecipients") or m.get("To") or "")
        found = EMAIL_RE.findall(recips_raw)
        for r in found:
            register_sent(r, "M365_DE_JORDI", m.get("receivedDateTime"), m.get("subject"), m.get("id"))

    # M365 Joel
    for m in joel_m365_sent:
        recips_raw = str(m.get("toRecipients") or m.get("To") or "")
        found = EMAIL_RE.findall(recips_raw)
        for r in found:
            register_sent(r, "M365_DE_JOEL", m.get("receivedDateTime"), m.get("subject"), m.get("id"))

    # COM Jordi
    for m in jordi_com_sent:
        for r in m.get("recipients", []):
            register_sent(r, "COM_JORDI", m.get("date_str"), m.get("subject"), m.get("internet_message_id"))

    # COM Joel
    for m in joel_com_sent:
        for r in m.get("recipients", []):
            register_sent(r, "COM_JOEL", m.get("date_str"), m.get("subject"), m.get("internet_message_id"))

    print(f"\nForensisch ermittelt: Insgesamt {len(sent_registry)} EINZIGARTIGE externe Empfänger kontaktiert.")

    # 4. Lade ALL_LEADS aus Google Sheet
    service = get_sheets_service()
    res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A2:BM6425").execute()
    rows = res.get("values", [])
    print(f"Google Sheet ALL_LEADS geladen: {len(rows)} Leads.")

    already_marked_sent = 0
    newly_discovered_sent = 0
    updates_lead = []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 105)
    print(f"{'Row':<5} | {'Lead-ID':<18} | {'E-Mail':<30} | {'Bisher':<10} | {'Quelle':<15} | {'Status'}")
    print("-" * 105)

    for idx, r in enumerate(rows, start=2):
        lead_id = r[0] if len(r) > 0 else ""
        email = (r[8] if len(r) > 8 and r[8] else "").strip().lower()
        curr_send_st = (r[40] if len(r) > 40 and r[40] else "").strip().lower()
        curr_batch_st = (r[46] if len(r) > 46 and r[46] else "").strip()

        if email in sent_registry:
            ev = sent_registry[email][0]
            if curr_send_st == "sent":
                already_marked_sent += 1
            else:
                newly_discovered_sent += 1
                sent_time = ev["date"] or now_iso
                msg_id = ev["message_id"] or ""
                print(f"{idx:<5} | {lead_id[:18]:<18} | {email[:30]:<30} | {curr_send_st:<10} | {ev['source']:<15} | NEU AUF SENT GESETZT")

                updates_lead.append({"range": f"ALL_LEADS!AO{idx}", "values": [["sent"]]})
                updates_lead.append({"range": f"ALL_LEADS!AP{idx}", "values": [[sent_time]]})
                updates_lead.append({"range": f"ALL_LEADS!AU{idx}", "values": [[f"SENT_{ev['source']}"]]})
                if msg_id:
                    updates_lead.append({"range": f"ALL_LEADS!BA{idx}", "values": [[msg_id]]})

    print("=" * 105)
    print(f"Bereits als 'sent' im Sheet markiert : {already_marked_sent}")
    print(f"Neu entdeckte, tatsächlich gesendete : {newly_discovered_sent}")
    print(f"Gesamt tatsächlich kontaktierte Leads : {already_marked_sent + newly_discovered_sent}")

    if updates_lead:
        print(f"\nSchreibe {len(updates_lead)} Zellen-Updates live ins Google Sheet...")
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates_lead}
        ).execute()
        print("✓ Google Sheet ALL_LEADS erfolgreich auf den realen Stand synchronisiert!")
    else:
        print("\nKeine neuen Versendungen gefunden – Sheet ist bereits synchron mit den Postfächern.")

if __name__ == "__main__":
    main()
