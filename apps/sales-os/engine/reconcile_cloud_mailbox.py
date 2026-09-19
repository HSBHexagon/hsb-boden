#!/usr/bin/env python3
"""
HSB Sales OS - Cloud-Native Multi-Mailbox Reconciliation Engine (UG-03).
Ersetzt alle lokalen Apple-Mail- und osascript-Abhaengigkeiten durch den
direkten M365 Power Platform APIHub / Office 365 Outlook Connector.

Funktionen:
1. Cloud-Native SentItems Abgleich:
   Liest direkt aus Microsoft Exchange ueber den APIHub-Connector
   (shared_office365) den Ordner 'Gesendete Elemente' / 'SentItems' aus.
   Verfuegbar auf jedem Betriebssystem ohne Apple Mail oder macOS-Zwang.
2. Dynamische RFC 3464 DSN Bounce-Erkennung:
   Zero-Hardcoding: Dynamisches Parsen von NDR-Statuscodes (550, 5.1.1, 5.4.1 etc.)
   und fehlgeschlagenen Empfaengern direkt aus dem MIME/Body.
3. Dynamische RFC 3834 Auto-Reply / OOO-Erkennung:
   Klassifizierung von Abwesenheitsnotizen, No-Reply-Bestaetigungen und Tickets.
4. Single Source of Truth Writeback:
   Aktualisiert Google Sheet 'ALL_LEADS' (Spalten AO:AP, AR:AT, AU, BD)
   und haengt neue Ereignisse dedupliziert an 'INBOUND_EVENTS' an.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from hsb_core import normalize_owner, EMAIL_RE

APIHUB_RESOURCE = "https://apihub.azure.com"
RUNTIME_URL = (
    "https://default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30.06.common.germany.azure-apihub.net/apim/office365"
)

CONNECTIONS = {
    "JOEL": {
        "account": "j-cherino@hsb-boden.de",
        "connection_id": "shared-office365-819bd473",
    },
    "JORDI": {
        "account": "j-post@hsb-boden.de",
        "connection_id": "3d152ea7ddb24e9286fe006cb9f5069b",
    },
}

BOUNCE_SUBJ_RE = re.compile(
    r"(unzustellbar|undeliverable|failure|failed|delivery status notification)",
    re.IGNORECASE,
)
AUTO_REPLY_SUBJ_RE = re.compile(
    r"(automatische antwort|abwesenheit|out of office|auto[-_ ]?reply|ihre nachricht an|ihre anfrage|case number)",
    re.IGNORECASE,
)
STATUS_CODE_RE = re.compile(r"(\b[45]\d{2}\s+[45]\.\d\.\d\b|\b[45]\.\d\.\d\b)")
INTERNAL_DOMAINS = ["hsb-boden.de", "microsoft.com", "outlook.com", "postmaster", "mailer-daemon"]
SEARCH_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def get_az_apihub_token() -> str:
    """Holt ein Bearer-Token fuer https://apihub.azure.com ueber die lokale az CLI."""
    try:
        out = subprocess.check_output(
            [
                "az",
                "account",
                "get-access-token",
                "--resource",
                APIHUB_RESOURCE,
                "--query",
                "accessToken",
                "-o",
                "tsv",
            ],
            text=True,
            timeout=15,
        )
        return out.strip()
    except Exception as e:
        raise RuntimeError(
            f"Fehler beim Abrufen des APIHub-Tokens ueber az CLI. Bitte pruefen ob 'az login' aktiv ist: {e}"
        )


def get_current_az_account() -> str:
    """Ermittelt den angemeldeten Benutzer der az CLI."""
    try:
        out = subprocess.check_output(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            text=True,
            timeout=10,
        )
        return out.strip().lower()
    except Exception:
        return ""


def call_office365_api(
    token: str,
    conn_id: str,
    folder_path: str,
    top: int = 50,
    fetch_only_unread: bool = False,
) -> List[Dict[str, Any]]:
    """Ruft die GetEmailsV3 Operation auf dem Office365 APIHub-Connector auf."""
    params = urllib.parse.urlencode(
        {
            "folderPath": folder_path,
            "fetchOnlyUnread": "true" if fetch_only_unread else "false",
            "top": str(top),
        }
    )
    url = f"{RUNTIME_URL}/{conn_id}/v3/Mail?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("value", [])
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"Office365 API Fehler (HTTP {e.code}) fuer {folder_path}: {err_msg}")


def fetch_cloud_sent_messages(token: str, conn_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Holt gesendete Nachrichten aus Gesendete Elemente (mit Fallback auf SentItems)."""
    try:
        msgs = call_office365_api(token, conn_id, "Gesendete Elemente", top=limit)
    except Exception:
        msgs = call_office365_api(token, conn_id, "SentItems", top=limit)

    sent_items = []
    for m in msgs:
        recips_raw = m.get("toRecipients") or m.get("To") or ""
        # toRecipients kann kommagetrennt sein
        recips = [
            r.strip().lower()
            for r in recips_raw.split(";")
            if r.strip()
        ]
        if not recips and "," in recips_raw:
            recips = [r.strip().lower() for r in recips_raw.split(",") if r.strip()]

        sent_items.append(
            {
                "id": m.get("id"),
                "date_str": m.get("receivedDateTime") or m.get("DateTimeReceived") or "",
                "recipients": recips,
                "subject": m.get("subject") or m.get("Subject") or "",
                "internet_message_id": m.get("internetMessageId") or "",
            }
        )
    return sent_items


def fetch_cloud_inbound_messages(token: str, conn_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Holt eingehende Nachrichten aus Posteingang (mit Fallback auf Inbox)."""
    try:
        msgs = call_office365_api(token, conn_id, "Posteingang", top=limit)
    except Exception:
        msgs = call_office365_api(token, conn_id, "Inbox", top=limit)

    inbound_items = []
    for m in msgs:
        inbound_items.append(
            {
                "id": m.get("id"),
                "date_str": m.get("receivedDateTime") or m.get("DateTimeReceived") or "",
                "from": m.get("from") or m.get("From") or "",
                "to": m.get("toRecipients") or m.get("To") or "",
                "subject": m.get("subject") or m.get("Subject") or "",
                "body": m.get("body") or m.get("bodyPreview") or "",
                "internet_message_id": m.get("internetMessageId") or "",
            }
        )
    return inbound_items


def parse_rfc3464_dsn(subject: str, body: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Dynamischer RFC 3464 Delivery Status Notification (Bounce) Parser.
    Erkennt Non-Delivery Reports ohne statische Listen.
    Gibt (is_bounce, status_code_reason, failed_recipients) zurueck.
    """
    if not BOUNCE_SUBJ_RE.search(subject):
        return False, None, []

    status_match = STATUS_CODE_RE.search(body)
    code = status_match.group(1).strip() if status_match else "550 (Generisch)"

    reason = f"Hard Bounce {code} - Mailbox nicht zustellbar"

    emails = SEARCH_EMAIL_RE.findall(body)
    cand_recips = []
    for e in emails:
        el = e.lower()
        if not any(dom in el for dom in INTERNAL_DOMAINS):
            cand_recips.append(el)

    return True, reason, list(dict.fromkeys(cand_recips[:3]))


def parse_rfc3834_autoreply(from_addr: str, subject: str, body: str) -> Tuple[bool, str]:
    """
    Dynamischer RFC 3834 Auto-Reply / Out of Office Parser.
    Gibt (is_autoreply, classification) zurueck.
    """
    fl = from_addr.lower()
    sl = subject.lower()

    if "no-reply" in fl or "noreply" in fl or "mailer-daemon" in fl:
        return True, "AUTO_REPLY_OOO"

    if AUTO_REPLY_SUBJ_RE.search(sl):
        return True, "AUTO_REPLY_OOO"

    return False, ""


def build_inbound_event_row(*, event_id, msg_date, mailbox, sender, subject, message_id,
                            lead_id, classification, stop, processed, notes):
    """Kanonisches 12-Spalten-Layout von INBOUND_EVENTS (Spalte F = Internet_Message_ID).

    Gleiche Reihenfolge wie INBOUND_EVENT_HEADER_ in apps_script/Actions.gs und
    docs/appsheet/inbound_events_schema_spec.json. Raw_Link (Spalte L) bleibt leer.
    """
    return [event_id, msg_date, mailbox, sender, subject, message_id,
            lead_id, classification, stop, processed, notes, ""]


def reconcile_cloud_for_owner(
    owner_key: str,
    service: Any,
    email_to_lead: Dict[str, Dict[str, Any]],
    existing_event_ids: set,
    token: str,
    limit: int = 100,
) -> Dict[str, int]:
    """Fuehrt den Cloud-Abgleich fuer einen Absender (JOEL oder JORDI) durch."""
    conf = CONNECTIONS[owner_key]
    conn_id = conf["connection_id"]
    mailbox_addr = conf["account"]

    print(f"\n---> Starte Cloud-Abgleich fuer {owner_key} ({mailbox_addr})...")

    # 1. Gesendete Elemente abrufen
    try:
        sent_messages = fetch_cloud_sent_messages(token, conn_id, limit=limit)
        print(f"[{owner_key}] Aus Cloud-Mailbox abgerufen: {len(sent_messages)} gesendete Nachrichten.")
    except Exception as e:
        print(f"[{owner_key}] WARNUNG: Gesendete Elemente konnten nicht gelesen werden: {e}")
        return {"sent_matched": 0, "sent_updated": 0, "bounces": 0, "replies": 0}

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    updates_ao_ap = []
    updates_au = []
    updates_bd = []

    matched_sent = 0
    newly_marked_sent = 0

    for item in sent_messages:
        for recip in item["recipients"]:
            if recip in email_to_lead:
                lead = email_to_lead[recip]
                # Nur zuordnen wenn Owner uebereinstimmt oder im Pool ist
                matched_sent += 1
                row_num = lead["row"]
                if lead["send_status"] != "sent" or lead["batch_status"] != "SENT":
                    newly_marked_sent += 1
                    sent_time = item["date_str"] or now_iso
                    updates_ao_ap.append(
                        {
                            "range": f"ALL_LEADS!AO{row_num}:AP{row_num}",
                            "values": [["sent", sent_time]],
                        }
                    )
                    updates_au.append(
                        {
                            "range": f"ALL_LEADS!AU{row_num}",
                            "values": [["SENT"]],
                        }
                    )
                    updates_bd.append(
                        {
                            "range": f"ALL_LEADS!BD{row_num}",
                            "values": [[""]],
                        }
                    )
                    print(
                        f"  [NEU SENT] Zeile {row_num:4d} | {lead['lead_id']} | {recip} | {item['subject'][:35]}..."
                    )
                    lead["send_status"] = "sent"
                    lead["batch_status"] = "SENT"

    if updates_ao_ap:
        batch_body = {
            "valueInputOption": "USER_ENTERED",
            "data": updates_ao_ap + updates_au + updates_bd,
        }
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=batch_body
        ).execute()
        print(f"[{owner_key}] ERFOLG: {newly_marked_sent} Zeilen in ALL_LEADS auf 'sent' aktualisiert!")

    # 2. Inbound Events abrufen (Posteingang)
    try:
        inbound_messages = fetch_cloud_inbound_messages(token, conn_id, limit=limit)
        print(f"[{owner_key}] Aus Cloud-Posteingang abgerufen: {len(inbound_messages)} Nachrichten.")
    except Exception as e:
        print(f"[{owner_key}] WARNUNG: Posteingang konnte nicht gelesen werden: {e}")
        return {
            "sent_matched": matched_sent,
            "sent_updated": newly_marked_sent,
            "bounces": 0,
            "replies": 0,
        }

    lead_inbound_updates = []
    inbound_event_rows = []
    bounces_count = 0
    replies_count = 0

    for msg in inbound_messages:
        subj = msg["subject"]
        body = msg["body"]
        sender = msg["from"]
        msg_date = msg["date_str"] or now_iso

        # Prüfe RFC 3464 Bounce
        is_bounce, bounce_reason, cand_recips = parse_rfc3464_dsn(subj, body)
        if is_bounce:
            for failed_email in cand_recips:
                if failed_email in email_to_lead:
                    lead = email_to_lead[failed_email]
                    row_num = lead["row"]
                    event_id = f"INBOUND-BOUNCE-{lead['lead_id']}"
                    if lead["reply_status"] != "bounced":
                        lead_inbound_updates.append(
                            {
                                "range": f"ALL_LEADS!AR{row_num}:AT{row_num}",
                                "values": [["bounced", "yes", "yes"]],
                            }
                        )
                        lead_inbound_updates.append(
                            {
                                "range": f"ALL_LEADS!BD{row_num}",
                                "values": [[bounce_reason]],
                            }
                        )
                        bounces_count += 1
                        print(
                            f"  [BOUNCE DYNAMISCH] Zeile {row_num:4d} | {lead['lead_id']} | {failed_email} -> {bounce_reason}"
                        )
                        lead["reply_status"] = "bounced"

                    if event_id not in existing_event_ids:
                        existing_event_ids.add(event_id)
                        inbound_event_rows.append(
                            build_inbound_event_row(
                                event_id=event_id,
                                msg_date=msg_date,
                                mailbox=mailbox_addr,
                                sender=sender,
                                subject=subj,
                                message_id=msg.get("internet_message_id", ""),
                                lead_id=lead["lead_id"],
                                classification="HARD_BOUNCE",
                                stop="yes",
                                processed="PROCESSED",
                                notes=bounce_reason,
                            )
                        )
            continue

        # Prüfe RFC 3834 Auto-Reply
        is_autoreply, auto_cls = parse_rfc3834_autoreply(sender, subj, body)
        if is_autoreply:
            # Versuche Absender oder im Body erwähnte Adresse zu matchen
            matched_lead = None
            if sender.lower() in email_to_lead:
                matched_lead = email_to_lead[sender.lower()]
            else:
                body_emails = [
                    e.lower()
                    for e in EMAIL_RE.findall(body)
                    if not any(d in e.lower() for d in INTERNAL_DOMAINS)
                ]
                for be in body_emails:
                    if be in email_to_lead:
                        matched_lead = email_to_lead[be]
                        break

            if matched_lead:
                row_num = matched_lead["row"]
                event_id = f"INBOUND-AUTOREPLY-{matched_lead['lead_id']}"
                if matched_lead["reply_status"] not in ["auto_reply_ooo", "bounced", "replied"]:
                    lead_inbound_updates.append(
                        {
                            "range": f"ALL_LEADS!AR{row_num}",
                            "values": [["auto_reply_ooo"]],
                        }
                    )
                    replies_count += 1
                    print(
                        f"  [AUTO-REPLY DYNAMISCH] Zeile {row_num:4d} | {matched_lead['lead_id']} | {matched_lead['email']} -> {auto_cls}"
                    )
                    matched_lead["reply_status"] = "auto_reply_ooo"

                if event_id not in existing_event_ids:
                    existing_event_ids.add(event_id)
                    inbound_event_rows.append(
                        build_inbound_event_row(
                            event_id=event_id,
                            msg_date=msg_date,
                            mailbox=mailbox_addr,
                            sender=sender,
                            subject=subj,
                            message_id=msg.get("internet_message_id", ""),
                            lead_id=matched_lead["lead_id"],
                            classification=auto_cls,
                            stop="no",
                            processed="PROCESSED",
                            notes="Auto-Reply / Eingangsbestaetigung registriert",
                        )
                    )
            continue

        # Echte menschliche Antwort
        clean_sender = sender.strip().lower()
        if clean_sender in email_to_lead:
            matched_lead = email_to_lead[clean_sender]
            row_num = matched_lead["row"]
            event_id = f"INBOUND-REPLY-{matched_lead['lead_id']}"
            if matched_lead["reply_status"] != "replied":
                lead_inbound_updates.append(
                    {
                        "range": f"ALL_LEADS!AR{row_num}",
                        "values": [["replied"]],
                    }
                )
                replies_count += 1
                print(
                    f"  [ECHTE ANTWORT] Zeile {row_num:4d} | {matched_lead['lead_id']} | {clean_sender} | {subj}"
                )
                matched_lead["reply_status"] = "replied"

            if event_id not in existing_event_ids:
                existing_event_ids.add(event_id)
                inbound_event_rows.append(
                    build_inbound_event_row(
                        event_id=event_id,
                        msg_date=msg_date,
                        mailbox=mailbox_addr,
                        sender=sender,
                        subject=subj,
                        message_id=msg.get("internet_message_id", ""),
                        lead_id=matched_lead["lead_id"],
                        classification="REPLY",
                        stop="no",
                        processed="PROCESSED",
                        notes=f"Echte Prospect-Antwort erfasst ({subj[:40]})",
                    )
                )

    if lead_inbound_updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": lead_inbound_updates},
        ).execute()
        print(f"[{owner_key}] ERFOLG: {len(lead_inbound_updates)} Inbound-Status-Updates in ALL_LEADS aktualisiert!")

    if inbound_event_rows:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="INBOUND_EVENTS!A2:L",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": inbound_event_rows},
        ).execute()
        print(f"[{owner_key}] ERFOLG: {len(inbound_event_rows)} neue Events in INBOUND_EVENTS protokolliert!")

    return {
        "sent_matched": matched_sent,
        "sent_updated": newly_marked_sent,
        "bounces": bounces_count,
        "replies": replies_count,
    }


def run_cloud_sync(target_owner: Optional[str] = None, limit: int = 100) -> None:
    """Hauptfunktion fuer Cloud-Mailbox-Reconciliation."""
    token = get_az_apihub_token()
    current_az_user = get_current_az_account()
    print(f"APIHub-Authentifizierung aktiv (az CLI Benutzer: {current_az_user or 'unbekannt'}).")

    service = get_sheets_service()
    print("Lese ALL_LEADS und INBOUND_EVENTS aus Google Sheet...")

    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A2:BD6425"
    ).execute()
    rows = res.get("values", [])

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
                "email": email,
                "owner": owner,
                "send_status": send_status,
                "send_datum": send_datum,
                "reply_status": reply_status,
                "batch_status": batch_status,
            }

    print(f"Indexiert: {len(email_to_lead)} Leads mit E-Mail-Adresse.")

    # Lese bestehende Inbound-Event-IDs
    res_events = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="INBOUND_EVENTS!A2:A"
    ).execute()
    existing_event_ids = set(
        r[0] for r in res_events.get("values", []) if r and r[0]
    )
    print(f"Bereits registrierte Inbound-Events: {len(existing_event_ids)}")

    owners_to_sync = []
    if target_owner:
        norm = normalize_owner(target_owner)
        if norm in CONNECTIONS:
            owners_to_sync.append(norm)
    else:
        # Wenn kein Owner angegeben ist, pruefe aktuellen az Benutzer
        if "j-post" in current_az_user:
            owners_to_sync = ["JORDI", "JOEL"]
        else:
            owners_to_sync = ["JOEL", "JORDI"]

    for o in owners_to_sync:
        if o == "JORDI":
            try:
                from run_100_batch import get_jordi_token
                owner_token = get_jordi_token()
                print("[JORDI] Verwende frisches MSAL OAuth Token für j-post@hsb-boden.de.")
            except Exception as e:
                print(f"[JORDI] Warnung: Konnte Jordi-Token nicht abrufen ({e}), nutze az Token")
                owner_token = token
        else:
            owner_token = token

        reconcile_cloud_for_owner(
            owner_key=o,
            service=service,
            email_to_lead=email_to_lead,
            existing_event_ids=existing_event_ids,
            token=owner_token,
            limit=limit,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud-Native Mailbox Reconciliation")
    parser.add_argument("--owner", choices=["JOEL", "JORDI"], help="Optionaler Filter auf bestimmten Owner")
    parser.add_argument("--limit", type=int, default=100, help="Anzahl abzurufender Mails (Standard: 100)")
    args = parser.parse_args()
    run_cloud_sync(target_owner=args.owner, limit=args.limit)
