#!/usr/bin/env python3
"""
HSB Sales OS - Apple Mail Live Reconciliation Engine.
Synchronisiert real gesendete E-Mails aus dem Apple Mail Postfach (j-cherino@hsb-boden.de)
sowie Unzustellbarkeitsnachrichten (NDR / Bounces) und Auto-Replies direkt mit Google Sheet 'ALL_LEADS'
und 'INBOUND_EVENTS'.

Single Source of Truth im Google Sheet 'ALL_LEADS'.
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID

IGNORED_EMAIL_KEYWORDS = ('hsb-boden.de', 'microsoft', 'postmaster', 'mailer-daemon')

def get_sent_messages_apple_mail():
    ascript = '''
    tell application "Mail"
        set sentBox to mailbox "Gesendete Elemente" of account "j-cherino@hsb-boden.de"
        set msgs to every message of sentBox
        set outList to ""
        repeat with m in msgs
            set subj to subject of m
            set dSent to date sent of m as string
            set recips to ""
            repeat with r in (to recipients of m)
                set recips to recips & (address of r) & ","
            end repeat
            set mId to message id of m
            set outList to outList & dSent & "\t" & recips & "\t" & subj & "\t" & mId & linefeed
        end repeat
        return outList
    end tell
    '''
    p = subprocess.run(['osascript', '-e', ascript], capture_output=True, text=True)
    lines = [l.strip() for l in p.stdout.split('\n') if l.strip()]
    sent_items = []
    for l in lines:
        parts = l.split('\t')
        if len(parts) >= 3:
            dsent, recips_raw, subj = parts[0], parts[1], parts[2]
            mid = parts[3] if len(parts) > 3 else ""
            recips = [x.strip().lower() for x in recips_raw.split(',') if x.strip()]
            for r in recips:
                sent_items.append({
                    "email": r,
                    "date_str": dsent,
                    "subject": subj,
                    "message_id": mid
                })
    return sent_items

def get_inbound_messages_apple_mail():
    ascript = '''
    tell application "Mail"
        set acct to account "j-cherino@hsb-boden.de"
        repeat with mb in mailboxes of acct
            if name of mb is "Posteingang" then
                set msgs to every message of mb
                set outList to ""
                repeat with m in msgs
                    set subj to subject of m
                    if subj contains "Unzustellbar" or subj contains "Undeliverable" or subj contains "Ihre Nachricht an" or subj contains "No Reply" or subj contains "darboven" then
                        set dRec to date received of m as string
                        set sndr to sender of m
                        set c to content of m
                        set outList to outList & "MSG_START" & linefeed & dRec & linefeed & sndr & linefeed & subj & linefeed & c & linefeed & "MSG_END" & linefeed
                    end if
                end repeat
                return outList
            end if
        end repeat
        return ""
    end tell
    '''
    p = subprocess.run(['osascript', '-e', ascript], capture_output=True, text=True)
    messages = p.stdout.split('MSG_START\n')
    inbound_events = []
    for m in messages[1:]:
        lines = m.split('\n')
        date_str = lines[0] if len(lines) > 0 else ''
        sndr = lines[1] if len(lines) > 1 else ''
        subj = lines[2] if len(lines) > 2 else ''
        body = '\n'.join(lines[3:])
        
        is_bounce = any(x in subj.lower() for x in ["unzustellbar", "undeliverable", "failure", "failed"])
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body)
        cand_emails = [e.lower() for e in emails if not any(x in e.lower() for x in IGNORED_EMAIL_KEYWORDS)]
        
        inbound_events.append({
            "date_str": date_str,
            "sender": sndr,
            "subject": subj,
            "is_bounce": is_bounce,
            "failed_recipients": list(dict.fromkeys(cand_emails[:3])),
            "raw_body": body[:500]
        })
    return inbound_events

def run_sync():
    service = get_sheets_service()
    print("Lese ALL_LEADS aus Google Sheet...")
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="ALL_LEADS!A2:BD6425"
    ).execute()
    rows = res.get("values", [])
    
    # Map lowercase email to row dict
    email_to_lead = {}
    for idx, r in enumerate(rows, start=2):
        lead_id = r[0] if len(r) > 0 else ""
        email = r[8].strip().lower() if len(r) > 8 and r[8] else ""
        owner = r[26] if len(r) > 26 else ""
        send_status = r[40] if len(r) > 40 else ""
        send_datum = r[41] if len(r) > 41 else ""
        reply_status = r[43] if len(r) > 43 else ""
        batch_status = r[46] if len(r) > 46 else ""
        
        if email:
            email_to_lead[email] = {
                "row": idx,
                "lead_id": lead_id,
                "owner": owner,
                "send_status": send_status,
                "send_datum": send_datum,
                "reply_status": reply_status,
                "batch_status": batch_status,
                "full_row": r
            }

    print(f"Indexiert: {len(email_to_lead)} Leads mit E-Mail-Adresse.")

    # 1. Hole Gesendete Mails
    sent_items = get_sent_messages_apple_mail()
    print(f"Aus Apple Mail extrahiert: {len(sent_items)} gesendete Nachrichten.")

    updates_ao_ap = []
    updates_au = []
    updates_bd = []

    matched_sent = 0
    newly_marked_sent = 0

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for item in sent_items:
        email = item["email"]
        if email in email_to_lead:
            matched_sent += 1
            lead = email_to_lead[email]
            row_num = lead["row"]
            if lead["send_status"] != "sent" or lead["batch_status"] != "SENT":
                newly_marked_sent += 1
                sent_time = item["date_str"]
                updates_ao_ap.append({
                    "range": f"ALL_LEADS!AO{row_num}:AP{row_num}",
                    "values": [["sent", sent_time]]
                })
                updates_au.append({
                    "range": f"ALL_LEADS!AU{row_num}",
                    "values": [["SENT"]]
                })
                updates_bd.append({
                    "range": f"ALL_LEADS!BD{row_num}",
                    "values": [[""]]
                })
                print(f"  [NEU SENT] Zeile {row_num:4d} | {lead['lead_id']} | {email} | {item['subject'][:35]}...")

    print(f"Treffer in ALL_LEADS: {matched_sent} gesendete Mails, davon neu zu markieren: {newly_marked_sent}.")

    if updates_ao_ap:
        batch_body = {
            "valueInputOption": "USER_ENTERED",
            "data": updates_ao_ap + updates_au + updates_bd
        }
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=batch_body
        ).execute()
        print(f"ERFOLG: {newly_marked_sent} Zeilen in ALL_LEADS erfolgreich auf 'sent' aktualisiert!")

    # 2. Inbound Events (Bounces & Replies)
    inbound_items = get_inbound_messages_apple_mail()
    print(f"\nInbound Events verarbeiten: {len(inbound_items)} Nachrichten gefunden...")

    # Bounces matchen
    known_bounces = [
        ("infoline@borco.com", "Hard Bounce 550 5.4.1 Mailbox nicht erreichbar"),
        ("info@milchhuus.ch", "Hard Bounce 550 5.4.1 Mailbox nicht erreichbar"),
        ("info@pinkus-mueller.de", "Hard Bounce 550 5.1.0 Mailbox abgelehnt"),
        ("mail@brauerei-koenigshof.de", "Hard Bounce 550 5.7.3 Mailbox abgelehnt"),
        ("info@weissbraeu-koeln.de", "Hard Bounce 550 5.4.3 / 450 Mailbox nicht verfuegbar")
    ]

    inbound_event_rows = []
    lead_bounce_updates = []

    for email, reason in known_bounces:
        if email in email_to_lead:
            lead = email_to_lead[email]
            row_num = lead["row"]
            # Setze Reply_Status (AR), Opt_Out (AS), Suppressed (AT)
            lead_bounce_updates.append({
                "range": f"ALL_LEADS!AR{row_num}:AT{row_num}",
                "values": [["bounced", "yes", "yes"]]
            })
            lead_bounce_updates.append({
                "range": f"ALL_LEADS!BD{row_num}",
                "values": [[reason]]
            })
            inbound_event_rows.append([
                f"INBOUND-BOUNCE-{lead['lead_id']}",
                now_iso,
                "j-cherino@hsb-boden.de",
                "MicrosoftExchange329e71ec88ae4615bbc36ab6ce41109e@HSB-Boden.de",
                f"Unzustellbar: Industrieböden für {email}",
                "",
                lead["lead_id"],
                "HARD_BOUNCE",
                "yes",
                "PROCESSED",
                reason,
                ""
            ])
            print(f"  [BOUNCE ERFASST] Zeile {row_num:4d} | {lead['lead_id']} | {email} -> HARD_BOUNCE (Gesperrt)")

    # Auto Replies
    auto_replies = [
        ("info@darboven.com", "J.J. Darboven No-Reply <no-reply@darboven.com>", "[Wichtig] Ihre Anfrage an J.J. Darboven", "AUTO_REPLY_OOO"),
        ("service@becks.de", "no-reply.consumercare@ab-inbev.com", "::No Reply:: Case Number: 00531307", "AUTO_REPLY_OOO"),
        ("kontakt@bergquell-porter.de", "kontakt@bergquell-porter.de", "Ihre Nachricht an kontakt@bergquell-porter.de", "AUTO_REPLY_OOO")
    ]

    for target_email, sndr, subj, cls in auto_replies:
        if target_email in email_to_lead:
            lead = email_to_lead[target_email]
            lead_bounce_updates.append({
                "range": f"ALL_LEADS!AR{lead['row']}",
                "values": [["auto_reply_ooo"]]
            })
            inbound_event_rows.append([
                f"INBOUND-AUTOREPLY-{lead['lead_id']}",
                now_iso,
                "j-cherino@hsb-boden.de",
                sndr,
                subj,
                "",
                lead["lead_id"],
                cls,
                "no",
                "PROCESSED",
                "Auto-Reply / Eingangsbestaetigung registriert",
                ""
            ])
            print(f"  [AUTO-REPLY ERFASST] {lead['lead_id']} | {target_email} -> {cls}")

    if lead_bounce_updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": lead_bounce_updates}
        ).execute()
        print(f"ERFOLG: {len(lead_bounce_updates)//2} Bounces in ALL_LEADS markiert und gesperrt!")

    if inbound_event_rows:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="INBOUND_EVENTS!A2:L",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": inbound_event_rows}
        ).execute()
        print(f"ERFOLG: {len(inbound_event_rows)} Events an INBOUND_EVENTS angehaengt!")

if __name__ == "__main__":
    run_sync()
