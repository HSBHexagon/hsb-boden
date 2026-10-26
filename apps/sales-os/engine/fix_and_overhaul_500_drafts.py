#!/usr/bin/env python3
"""
HSB Sales OS - Korrektur & Veredelung der 500 + 500 Entwürfe.
Setzt den autoritativen Kunden-Sichtnamen des Anhangs auf:
HSB-HEXAGON-Industrieboeden-Flyer.pdf

Ablauf:
1. Identifiziert die 500 Entwürfe von Joel und 500 Entwürfe von Jordie anhand ihrer Message-IDs im Sheet.
2. Löscht die Entwürfe mit dem internen Dateinamen per IMAP.
3. Erzeugt die Entwürfe neu mit dem kanonischen Anhangs-Namen 'HSB-HEXAGON-Industrieboeden-Flyer.pdf'.
4. Schreibt die neuen Message-IDs ins Google Sheet ALL_LEADS zurück.
5. Prüft per Readback, dass der Anhangsname exakt 'HSB-HEXAGON-Industrieboeden-Flyer.pdf' ist.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import email
from email.policy import default
import hashlib
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from dotenv import load_dotenv
env_path = REPO_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)

from com_batch_selector import normalize_owner
from com_mailbox_manager import ComMailboxClient
from canonical_template_factory import render_canonical_email
from high_volume_matrix_engine import load_leads_authoritative
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID


def overhaul_owner(owner: str, start_row: int, end_row: int, chunk_size: int = 50):
    norm_owner = normalize_owner(owner)
    print("=" * 80)
    print(f" STARTE ENTWURFS-KORREKTUR FÜR {norm_owner} (Zeilen {start_row} bis {end_row})")
    print(" Ziel-Anhangsname: HSB-HEXAGON-Industrieboeden-Flyer.pdf")
    print("=" * 80)

    sheets_service = get_sheets_service()
    client = ComMailboxClient(norm_owner)

    print("⏳ Lade Leads aus Google Sheet 'ALL_LEADS'...")
    all_leads = load_leads_authoritative(require_live=True)
    target_leads = [
        l for l in all_leads
        if start_row <= l["_row"] <= end_row and normalize_owner(l.get("Owner")) == norm_owner
    ]
    print(f"✅ {len(target_leads)} Leads im Zielbereich gefunden.")

    # 1. Hole alle Message-IDs der alten Entwürfe aus den Leads
    old_mids = {str(l.get("Internet_Message_ID") or l.get("Draft_ID") or "").strip() for l in target_leads}
    old_mids.discard("")
    print(f"   Bestehende Message-IDs im Sheet: {len(old_mids)}")

    # 2. Lösche alte Entwürfe im IMAP-Postfach anhand der Message-IDs (High-Speed Range Fetch)
    print("⏳ Suche und lösche alte Entwürfe im All-Inkl Postfach...")
    deleted_count = 0
    norm_old_mids = {m.strip("<>").strip() for m in old_mids}
    imap = client._get_imap()
    try:
        status, _ = imap.select(client.cfg["drafts_folder"])
        typ, data = imap.fetch("1:*", "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
        seqs_to_delete = []
        for item in data:
            if isinstance(item, tuple):
                seq = item[0].split()[0].decode()
                hdr = item[1].decode("utf-8", errors="ignore")
                for line in hdr.splitlines():
                    if line.lower().startswith("message-id:"):
                        mid = line.split(":", 1)[1].strip().strip("<>").strip()
                        if mid in norm_old_mids:
                            seqs_to_delete.append(seq)
                        break
        print(f"   {len(seqs_to_delete)} passende alte Entwürfe im Postfach zur Bereinigung identifiziert.")
        if seqs_to_delete:
            for i in range(0, len(seqs_to_delete), 100):
                sub_seqs = ",".join(seqs_to_delete[i:i+100])
                imap.store(sub_seqs, "+FLAGS", r"(\Deleted)")
            imap.expunge()
            deleted_count = len(seqs_to_delete)
        print(f"✅ {deleted_count} alte Entwürfe aus dem Postfach entfernt.")
    finally:
        imap.logout()

    # 3. Erstelle die 500 Entwürfe neu mit dem kanonischen Flyer-Namen
    print(f"\n⏳ Erstelle {len(target_leads)} Entwürfe neu mit Anhang 'HSB-HEXAGON-Industrieboeden-Flyer.pdf'...")
    total_drafted = 0
    total_chunks = (len(target_leads) + chunk_size - 1) // chunk_size
    now_tag = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")

    for chunk_idx in range(total_chunks):
        chunk_leads = target_leads[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]
        batch_id = f"COM-{norm_owner}-500-{now_tag}-T{chunk_idx + 1:02d}"
        print(f"\n--- [{norm_owner}] Tranche {chunk_idx + 1}/{total_chunks} ({len(chunk_leads)} Leads) ---")

        batch_items = []
        for lead in chunk_leads:
            email_data = render_canonical_email(lead, owner=norm_owner, domain="com")
            batch_items.append({
                "lead_id": lead.get("Lead_ID"),
                "row_idx": lead.get("_row"),
                "to_email": email_data["to_address"],
                "subject": email_data["subject"],
                "body_html": email_data["body_html"],
                "flyer_path": email_data["flyer_path"],
                "flyer_filename": "HSB-HEXAGON-Industrieboeden-Flyer.pdf",
                "sender": f"j-cherino@hsb-boden.com" if norm_owner == "JOEL" else "j-post@hsb-boden.com"
            })

        manifest = client.create_drafts_batch(batch_items)
        ok_count = sum(1 for m in manifest if m.get("ok") is True)
        print(f"  ✅ IMAP APPEND: {ok_count}/{len(batch_items)} OK.")

        # Sheet Writeback
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        updates = []
        for item in manifest:
            if not item.get("ok"):
                continue
            r = item["row_idx"]
            mid = item["message_id"]
            updates.append({"range": f"ALL_LEADS!AW{r}", "values": [[mid]]})
            updates.append({"range": f"ALL_LEADS!AX{r}", "values": [[timestamp]]})
            updates.append({"range": f"ALL_LEADS!BA{r}", "values": [[mid]]})

        if updates:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates}
            ).execute()
            print(f"  ✅ Google Sheet mit neuen Message-IDs aktualisiert.")

        total_drafted += ok_count
        print(f"  Zwischenstand {norm_owner}: {total_drafted}/{len(target_leads)} Entwürfe fertig.")
        if chunk_idx < total_chunks - 1:
            time.sleep(1.0)

    # 4. Verifiziere stichprobenartig den Anhangsnamen des letzten Entwurfs
    imap = client._get_imap()
    try:
        status, _ = imap.select(client.cfg["drafts_folder"])
        typ, data = imap.search(None, "ALL")
        uids = data[0].split()
        if uids:
            typ, mdata = imap.fetch(uids[-1], "(RFC822)")
            msg = email.message_from_bytes(mdata[0][1], policy=default)
            filenames = [part.get_filename() for part in msg.walk() if part.get_filename()]
            print(f"\n🔍 VERIFIKATION LETZTER ENTWURF:")
            print(f"   Subject: {msg.get('Subject')}")
            print(f"   Gefundene Anhänge: {filenames}")
            assert "HSB-HEXAGON-Industrieboeden-Flyer.pdf" in filenames, f"FEHLER: Falscher Anhangsname: {filenames}"
            print("   ✅ BESTÄTIGT: Anhangsname lautet exakt 'HSB-HEXAGON-Industrieboeden-Flyer.pdf'!")
    finally:
        imap.logout()

    print("\n" + "=" * 80)
    print(f" KORREKTUR FÜR {norm_owner} ERFOLGREICH ABGESCHLOSSEN: {total_drafted} Entwürfe veredelt.")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS 500 Draft Overhaul & Attachment Fix")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH")
    args = parser.parse_args()

    if args.owner in ["JOEL", "BOTH"]:
        overhaul_owner("JOEL", 1225, 1724, chunk_size=50)

    if args.owner in ["JORDI", "BOTH"]:
        overhaul_owner("JORDI", 4534, 5033, chunk_size=50)


if __name__ == "__main__":
    main()
