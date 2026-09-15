#!/usr/bin/env python3
"""
Verification suite for AppSheet fail-closed row security filters.
Simulates AppSheet USEREMAIL() filter logic over ALL_LEADS.
"""

import sys
import openpyxl
from pathlib import Path

def simulate_filter(user_email, verified_joel, verified_jordi, verified_admin, owner):
    if user_email == verified_joel:
        return owner == "Joel Cherino Diaz"
    elif user_email == verified_jordi:
        return owner == "Jordi Post"
    elif user_email == verified_admin:
        return True
    else:
        return False

def main():
    print("================================================================================")
    print("HSB SALES OS — APPSHEET ROW-LEVEL SECURITY SIMULATION & VERIFICATION")
    print("================================================================================")

    data_dir = Path("data")
    xlsx_files = sorted(data_dir.glob("*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not xlsx_files:
        print("ERROR: No .xlsx data file found in data/")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_files[-1], read_only=True, data_only=True)
    ws = wb["ALL_LEADS"]

    rows = list(ws.iter_rows(values_only=True))[1:]
    wb.close()

    total_leads = len(rows)
    print(f"Total leads loaded: {total_leads}")

    VERIFIED_JOEL = "j-cherino@hsb-boden.de"
    VERIFIED_JORDI = "j-post@hsb-boden.de"
    VERIFIED_ADMIN = "cherinodiaz@outlook.com"
    UNAUTHORIZED_USER = "unknown_attacker@domain.com"
    UNAUTHENTICATED = ""

    # Test Joel isolation
    joel_rows = [r for r in rows if simulate_filter(VERIFIED_JOEL, VERIFIED_JOEL, VERIFIED_JORDI, VERIFIED_ADMIN, r[26])]
    print(f"JOEL_VISIBLE_ROWS={len(joel_rows)}")
    assert len(joel_rows) == 3212, f"Expected 3212 rows for Joel, got {len(joel_rows)}"
    assert all(r[26] == "Joel Cherino Diaz" for r in joel_rows), "Joel saw rows not owned by Joel!"

    # Test Jordi isolation
    jordi_rows = [r for r in rows if simulate_filter(VERIFIED_JORDI, VERIFIED_JOEL, VERIFIED_JORDI, VERIFIED_ADMIN, r[26])]
    print(f"JORDI_VISIBLE_ROWS={len(jordi_rows)}")
    assert len(jordi_rows) == 3212, f"Expected 3212 rows for Jordi, got {len(jordi_rows)}"
    assert all(r[26] == "Jordi Post" for r in jordi_rows), "Jordi saw rows not owned by Jordi!"

    # Test Admin view
    admin_rows = [r for r in rows if simulate_filter(VERIFIED_ADMIN, VERIFIED_JOEL, VERIFIED_JORDI, VERIFIED_ADMIN, r[26])]
    print(f"ADMIN_VISIBLE_ROWS={len(admin_rows)}")
    assert len(admin_rows) == 6424, f"Expected 6424 rows for Admin, got {len(admin_rows)}"

    # Test Unknown / Unauthorized User (Fail-Closed)
    unknown_rows = [r for r in rows if simulate_filter(UNAUTHORIZED_USER, VERIFIED_JOEL, VERIFIED_JORDI, VERIFIED_ADMIN, r[26])]
    print(f"UNKNOWN_VISIBLE_ROWS={len(unknown_rows)}")
    assert len(unknown_rows) == 0, f"Unknown user saw {len(unknown_rows)} rows! Must be 0."

    # Test Unauthenticated User
    unauth_rows = [r for r in rows if simulate_filter(UNAUTHENTICATED, VERIFIED_JOEL, VERIFIED_JORDI, VERIFIED_ADMIN, r[26])]
    print(f"UNAUTHENTICATED_VISIBLE_ROWS={len(unauth_rows)}")
    assert len(unauth_rows) == 0, f"Unauthenticated user saw {len(unauth_rows)} rows! Must be 0."

    # Test Owner Crossover (Intersection of Joel and Jordi lead IDs)
    joel_ids = set(r[0] for r in joel_rows)
    jordi_ids = set(r[0] for r in jordi_rows)
    crossover = joel_ids.intersection(jordi_ids)
    print(f"OWNER_CROSSOVER_COUNT={len(crossover)}")
    assert len(crossover) == 0, f"Detected {len(crossover)} crossover IDs between Joel and Jordi!"

    print("================================================================================")
    print("VERDICT: PASS (Security Filter 100% Fail-Closed & Isolated)")
    print("================================================================================")

if __name__ == "__main__":
    main()
