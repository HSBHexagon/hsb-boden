#!/usr/bin/env python3
"""
HSB Sales OS - Rollout Runner für 500 + 500 Entwürfe (.COM IMAP Postfächer).
Erstellt für Joel Cherino Diaz und Jordie Post jeweils 500 Entwürfe in All-Inkl:
- Reine Entwürfe im serverseitigen IMAP-Ordner 'Entw&APw-rfe' mit X-Unsent: 1.
- Eiserne Sicherheits-Invariante: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (kein SMTP-Versand).
- Sequentielle Tranchen (z.B. 50er Chunks) mit sofortigem Sheet-Writeback (ALL_LEADS & BATCHES).
- Server-Verifikation aller Message-IDs vor dem CRM-Status-Update.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import getaddresses
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

from com_batch_selector import select_com_eligible_leads, normalize_owner
from com_mailbox_manager import ComMailboxClient
from canonical_template_factory import render_canonical_email
from high_volume_matrix_engine import load_leads_authoritative
from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID


def verify_manifest_on_server(client: ComMailboxClient, manifest: List[Dict[str, Any]]) -> set[str]:
    """Verifiziert, dass alle neu erstellten Message-IDs auf dem All-Inkl IMAP Server existieren."""
    server_drafts = client.list_drafts(limit=10000)
    stored_ids = {str(d.get("message_id") or "").strip() for d in server_drafts}
    return {
        str(item.get("message_id"))
        for item in manifest
        if item.get("ok") is True and str(item.get("message_id") or "").strip() in stored_ids
    }


def write_tranche_to_sheets(
    service: Any,
    batch_id: str,
    owner: str,
    manifest: List[Dict[str, Any]],
    verified_ids: set[str]
) -> int:
    """Schreibt erfolgreiche Entwürfe ins Google Sheet ALL_LEADS und BATCHES zurück."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sender = "j-cherino@hsb-boden.com" if owner == "JOEL" else "j-post@hsb-boden.com"
    updates = []
    drafted_count = 0

    for item in manifest:
        mid = str(item.get("message_id") or "").strip()
        if item.get("ok") is not True or mid not in verified_ids:
            continue
        row = item["row_idx"]
        stable_id = hashlib.sha256(f"{owner}:{item['lead_id']}".encode()).hexdigest()[:24]

        # Z und AS sind menschlich dokumentierte Freigabe-/Nachweisfelder.
        # Ein erfolgreicher IMAP-Draft darf sie niemals automatisch setzen.
        fields = {
            "AN": batch_id,
            "AO": "drafted",
            "AU": "DRAFTED_COM_2026",
            "AW": mid,
            "AX": timestamp,
            "AY": timestamp,
            "BA": mid,
            "BF": f"COM-{stable_id}",
            "BG": sender,
            "BH": "OPERATOR_ROLLOUT_500"
        }
        for col, val in fields.items():
            updates.append({"range": f"ALL_LEADS!{col}{row}", "values": [[val]]})
        drafted_count += 1

    if updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

    # Append to BATCHES
    batches_row = [
        batch_id, owner, "COM_DRAFT_V2", "COM_DRAFTED",
        len(manifest), drafted_count, drafted_count, 0,
        len(manifest) - drafted_count, "", timestamp, "", "",
        str(drafted_count), str(len(manifest) - drafted_count), "100%", ""
    ]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="BATCHES!A:Q",
        valueInputOption="USER_ENTERED",
        body={"values": [batches_row]}
    ).execute()

    return drafted_count


def process_owner_rollout(
    owner: str,
    target_count: int = 500,
    chunk_size: int = 50,
    dry_run: bool = False
) -> Dict[str, Any]:
    norm_owner = normalize_owner(owner)
    print("=" * 80)
    print(f" STARTE ROLLOUT FÜR {norm_owner} (Ziel: {target_count} Entwürfe in {chunk_size}er Tranchen)")
    print("=" * 80)

    sheets_service = get_sheets_service()
    client = None if dry_run else ComMailboxClient(norm_owner)

    # Hole vorhandene Entwürfe aus dem Postfach, um Duplikate garantiert auszuschließen
    existing_mailbox_emails: set[str] = set()
    if not dry_run and client:
        print("⏳ Lese bestehende Entwürfe aus All-Inkl Postfach...")
        draft_headers = client.list_drafts(limit=10000)
        for d in draft_headers:
            for _, addr in getaddresses([str(d.get("to") or "")]):
                if addr:
                    existing_mailbox_emails.add(addr.strip().lower())
        print(f"✅ {len(existing_mailbox_emails)} bestehende Entwurfs-Empfänger im Postfach gefunden.")

    print("⏳ Lade Leads aus Google Sheet 'ALL_LEADS'...")
    leads = load_leads_authoritative(require_live=True)

    candidates = select_com_eligible_leads(leads, owner=norm_owner, limit=len(leads))
    filtered_candidates = [
        c for c in candidates
        if str(c.get("Email") or "").strip().lower() not in existing_mailbox_emails
    ]
    pool = filtered_candidates[:target_count]

    if len(pool) < target_count:
        print(f"❌ Nicht genügend berechtigte Leads gefunden: {len(pool)} von {target_count} benötigt.")
        return {"status": "INSUFFICIENT_LEADS", "found": len(pool), "drafted": 0}

    print(f"✅ Exakt {len(pool)} qualifizierte Leads für {norm_owner} ausgewählt.")
    print(f"   Zeilenbereich: Zeile {pool[0]['_row']} ({pool[0]['Lead_ID']}) bis Zeile {pool[-1]['_row']} ({pool[-1]['Lead_ID']})")

    total_drafted = 0
    total_chunks = (len(pool) + chunk_size - 1) // chunk_size
    now_tag = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")

    for chunk_idx in range(total_chunks):
        chunk_leads = pool[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]
        batch_id = f"COM-{norm_owner}-500-{now_tag}-T{chunk_idx + 1:02d}"
        print(f"\n--- [{norm_owner}] Tranche {chunk_idx + 1}/{total_chunks} ({len(chunk_leads)} Leads) -> Batch {batch_id} ---")

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
                "flyer_filename": email_data["flyer_filename"],
                "sender": f"j-cherino@hsb-boden.com" if norm_owner == "JOEL" else "j-post@hsb-boden.com"
            })

        if dry_run or not client:
            print(f"  [DRY-RUN] Simuliere Injektion für {len(batch_items)} Entwürfe...")
            manifest = [{"ok": True, "message_id": f"<dryrun-{i}@hsb-boden.com>", "lead_id": it["lead_id"], "row_idx": it["row_idx"]} for i, it in enumerate(batch_items)]
            verified_ids = {item["message_id"] for item in manifest}
            drafted = len(manifest)
        else:
            print(f"  ⏳ Injiziere {len(batch_items)} Entwürfe via IMAP SSL in All-Inkl 'Entw&APw-rfe'...")
            manifest = client.create_drafts_batch(batch_items)
            ok_count = sum(1 for m in manifest if m.get("ok") is True)
            print(f"  ✅ IMAP APPEND abgeschlossen: {ok_count}/{len(batch_items)} OK.")

            print("  ⏳ Verifiziere Message-IDs auf All-Inkl IMAP Server...")
            verified_ids = verify_manifest_on_server(client, manifest)
            print(f"  ✅ Server-Verifikation: {len(verified_ids)}/{len(batch_items)} Entwürfe bestätigt.")

            print("  ⏳ Schreibe CRM-Status in ALL_LEADS & BATCHES...")
            drafted = write_tranche_to_sheets(sheets_service, batch_id, norm_owner, manifest, verified_ids)
            print(f"  ✅ Google Sheet aktualisiert ({drafted} Entwürfe als DRAFTED verbucht).")

        total_drafted += drafted
        print(f"  Zwischenstand {norm_owner}: {total_drafted}/{len(pool)} Entwürfe fertig.")
        if not dry_run and chunk_idx < total_chunks - 1:
            time.sleep(1.0)  # Sanfte Pause zwischen den IMAP-Tranchen

    print("\n" + "=" * 80)
    print(f" ROLLOUT FÜR {norm_owner} ABGESCHLOSSEN: {total_drafted}/{target_count} Entwürfe erfolgreich erstellt!")
    print("=" * 80)
    return {"status": "SUCCESS", "found": len(pool), "drafted": total_drafted}


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS 500+500 COM Draft Rollout")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH", help="Owner: JOEL, JORDI oder BOTH")
    parser.add_argument("--count", type=int, default=500, help="Anzahl Entwürfe je Owner (Default: 500)")
    parser.add_argument("--chunk-size", type=int, default=50, help="Tranchengröße für IMAP & Sheet-Flush (Default: 50)")
    parser.add_argument("--apply", action="store_true", help="Scharf schalten: Erstellt reale Entwürfe und schreibt ins Sheet")
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("⚠️  HINWEIS: DRY-RUN AKTIV (--apply nicht angegeben). Keine echten Entwürfe, kein Sheet-Write.")

    owners = ["JOEL", "JORDI"] if args.owner == "BOTH" else [args.owner]
    results = {}
    for o in owners:
        results[o] = process_owner_rollout(
            owner=o,
            target_count=args.count,
            chunk_size=args.chunk_size,
            dry_run=dry_run
        )

    print("\n" + "#" * 80)
    print(" GESAMTERGEBNIS DES 1.000ER ROLLOUTS:")
    for o, res in results.items():
        print(f"  * {o}: Status={res['status']}, Erstellt={res.get('drafted', 0)}")
    print("#" * 80)


if __name__ == "__main__":
    main()
