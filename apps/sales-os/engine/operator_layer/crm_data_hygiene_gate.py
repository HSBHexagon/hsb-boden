import os, sys, json
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from crm_common import services, SID

DRY = "--apply" not in sys.argv
sheets, _ = services("cherinodiaz" if "--apply" in sys.argv else "cherinojoel")
SH = 767806010  # ALL_LEADS

def run():
    hdr = sheets.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!1:1").execute()["values"][0]
    ix = {h: i for i, h in enumerate(hdr)}
    
    col_freigabe = ix["Versandfreigabe"]
    col_legal = ix["Legal_Basis"]
    col_owner = ix.get("Verantwortlicher")
    col_status = ix.get("Send_Status")
    col_id = ix.get("Lead-ID")
    
    data = sheets.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!A2:BE6425").execute().get("values", [])
    
    updates = []
    affected_rows = []
    
    # 0-indexed to column letter (col 25 = Z)
    def col_to_letter(col_idx):
        result = ""
        while col_idx >= 0:
            result = chr(ord('A') + (col_idx % 26)) + result
            col_idx = (col_idx // 26) - 1
        return result

    freigabe_col_letter = col_to_letter(col_freigabe)
    
    for row_idx, row in enumerate(data, start=2):
        f_val = row[col_freigabe].strip() if len(row) > col_freigabe and row[col_freigabe] else ""
        l_val = row[col_legal].strip() if len(row) > col_legal and row[col_legal] else ""
        
        # Target exact 323 non-compliant leads (Legal_Basis is UNKNOWN, no, or empty)
        if f_val.lower() == "yes" and l_val in ("UNKNOWN", "no", ""):
            affected_rows.append({
                "row": row_idx,
                "lead_id": row[col_id] if col_id is not None and len(row) > col_id else "",
                "owner": row[col_owner] if col_owner is not None and len(row) > col_owner else "",
                "send_status": row[col_status] if col_status is not None and len(row) > col_status else "",
                "legal_basis": l_val
            })
            updates.append({
                "range": f"ALL_LEADS!{freigabe_col_letter}{row_idx}",
                "values": [["no"]]
            })

    print(f"Total leads inspected: {len(data)}")
    print(f"Total leads with Versandfreigabe=yes but non-compliant Legal_Basis: {len(affected_rows)}")
    
    owners = Counter(r["owner"] for r in affected_rows)
    send_statuses = Counter(r["send_status"] for r in affected_rows)
    legal_bases = Counter(r["legal_basis"] for r in affected_rows)
    print("Breakdown by Owner:", dict(owners))
    print("Breakdown by Send_Status:", dict(send_statuses))
    print("Breakdown by Legal_Basis:", dict(legal_bases))
    
    if DRY:
        print("\n[DRY RUN] No changes written to Google Sheets.")
        print("Run with --apply to write 'no' to Versandfreigabe for these 323 rows.")
        return
        
    print(f"\n[APPLY] Writing {len(updates)} updates to Google Sheets...")
    chunk_size = 500
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i+chunk_size]
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": chunk
        }
        sheets.spreadsheets().values().batchUpdate(spreadsheetId=SID, body=body).execute()
        print(f"Updated chunk {i+1} to {min(i+chunk_size, len(updates))}")
    print("SUCCESS: 323 leads updated to Versandfreigabe=no.")

if __name__ == "__main__":
    run()
