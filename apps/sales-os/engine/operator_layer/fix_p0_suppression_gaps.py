#!/usr/bin/env python3
"""
P0 Safety & Suppression Fix für HSB Sales OS CRM
Behebt die 2 Opt-outs ohne Sperre und die 19 Bounces ohne Sperre im Master-Sheet.
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from crm_common import services, SID, col

APPLY = "--apply" in sys.argv
PROFILE = "info"
sheets, _ = services(PROFILE)

BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / "batches"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_FILE = BACKUP_DIR / f"p0_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def run():
    print(f"=== P0 SAFETY FIX (Mode: {'APPLY (LIVE)' if APPLY else 'DRY RUN'}) ===")
    print(f"Using Google Workspace Profile: {PROFILE}")
    
    # 1. Header laden
    hdr = sheets.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!1:1").execute()["values"][0]
    ix = {h: i for i, h in enumerate(hdr)}
    
    col_id = ix["Lead-ID"]
    col_firma = ix["Firma"]
    col_email = ix["E-Mail"]
    col_optout = ix["Opt-out-Status"] # Y
    col_freigabe = ix["Versandfreigabe"] # Z
    col_bounce = ix["Bounce_Status"] # AQ
    col_suppressed = ix["Suppressed"] # AT
    col_reason = ix["Suppression_Reason"] # BJ
    
    # 2. Daten laden
    data = sheets.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!A2:BJ6425").execute().get("values", [])
    
    updates = []
    backup_data = []
    
    # Zielzeilen identifizieren
    for row_idx, r in enumerate(data, start=2):
        lead_id = r[col_id] if len(r) > col_id else ""
        firma = r[col_firma] if len(r) > col_firma else ""
        email = r[col_email] if len(r) > col_email else ""
        opt_out = (r[col_optout] if len(r) > col_optout else "").strip()
        freigabe = (r[col_freigabe] if len(r) > col_freigabe else "").strip()
        bounce = (r[col_bounce] if len(r) > col_bounce else "").strip()
        suppressed = (r[col_suppressed] if len(r) > col_suppressed else "").strip()
        reason = (r[col_reason] if len(r) > col_reason else "").strip()
        
        # Fall A: 2 Opt-outs ohne Sperre (Opt-out == 'YES', Suppressed != 'yes')
        if opt_out.lower() == "yes" and suppressed.lower() != "yes":
            backup_data.append({
                "row": row_idx,
                "lead_id": lead_id,
                "firma": firma,
                "type": "OPTOUT_UNSUPPRESSED",
                "old_values": {
                    "Versandfreigabe": freigabe,
                    "Suppressed": suppressed,
                    "Suppression_Reason": reason
                }
            })
            # Korrektur: Versandfreigabe=no, Suppressed=yes, Suppression_Reason=INBOUND_OPTOUT
            updates.append({
                "range": f"ALL_LEADS!{col(col_freigabe)}{row_idx}",
                "values": [["no"]]
            })
            updates.append({
                "range": f"ALL_LEADS!{col(col_suppressed)}{row_idx}",
                "values": [["yes"]]
            })
            updates.append({
                "range": f"ALL_LEADS!{col(col_reason)}{row_idx}",
                "values": [["INBOUND_OPTOUT"]]
            })
            print(f"[OPTOUT FIX] Row {row_idx} ({lead_id}, {firma}): Versandfreigabe=no, Suppressed=yes, Reason=INBOUND_OPTOUT")
            
        # Fall B: 12 Bounces ohne Sperre (Bounce == 'bounce_review', Suppressed == 'no')
        elif bounce == "bounce_review" and suppressed.lower() == "no":
            backup_data.append({
                "row": row_idx,
                "lead_id": lead_id,
                "firma": firma,
                "type": "BOUNCE_REVIEW_UNSUPPRESSED",
                "old_values": {
                    "Versandfreigabe": freigabe,
                    "Suppressed": suppressed,
                    "Suppression_Reason": reason
                }
            })
            # Korrektur: Suppressed=yes, Versandfreigabe=no
            updates.append({
                "range": f"ALL_LEADS!{col(col_freigabe)}{row_idx}",
                "values": [["no"]]
            })
            updates.append({
                "range": f"ALL_LEADS!{col(col_suppressed)}{row_idx}",
                "values": [["yes"]]
            })
            if not reason:
                updates.append({
                    "range": f"ALL_LEADS!{col(col_reason)}{row_idx}",
                    "values": [["INBOUND_BOUNCE"]]
                })
            print(f"[BOUNCE FIX] Row {row_idx} ({lead_id}, {firma}): Suppressed=yes, Versandfreigabe=no")
            
        # Fall C: 5 gerettete Bounces ohne Sperre (Bounce == 'rescued', Suppressed == 'no')
        elif bounce == "rescued" and suppressed.lower() == "no":
            backup_data.append({
                "row": row_idx,
                "lead_id": lead_id,
                "firma": firma,
                "type": "RESCUED_UNSUPPRESSED",
                "old_values": {
                    "Versandfreigabe": freigabe,
                    "Suppressed": suppressed,
                    "Suppression_Reason": reason
                }
            })
            # Sicherer Zustand: Vor Neusendung muss die Ersatzadresse verifiziert werden! Suppressed=yes, Reason=RESCUED_PENDING_REVIEW, Versandfreigabe=no
            updates.append({
                "range": f"ALL_LEADS!{col(col_freigabe)}{row_idx}",
                "values": [["no"]]
            })
            updates.append({
                "range": f"ALL_LEADS!{col(col_suppressed)}{row_idx}",
                "values": [["yes"]]
            })
            updates.append({
                "range": f"ALL_LEADS!{col(col_reason)}{row_idx}",
                "values": [["RESCUED_PENDING_REVIEW"]]
            })
            print(f"[RESCUED FIX] Row {row_idx} ({lead_id}, {firma}): Suppressed=yes, Versandfreigabe=no, Reason=RESCUED_PENDING_REVIEW")

    print(f"\nTotal affected rows: {len(backup_data)}")
    print(f"Total cell updates queued: {len(updates)}")
    
    # Backup sichern
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    print(f"Backup saved to: {BACKUP_FILE}")
    
    if APPLY:
        print("\nExecuting batch update on Google Sheet...")
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": updates
        }
        res = sheets.spreadsheets().values().batchUpdate(spreadsheetId=SID, body=body).execute()
        print(f"BatchUpdate success: {res.get('totalUpdatedCells')} cells updated across {res.get('totalUpdatedRows')} ranges.")
    else:
        print("\nDRY RUN completed. Run with --apply to execute changes live in the CRM.")

if __name__ == "__main__":
    run()
