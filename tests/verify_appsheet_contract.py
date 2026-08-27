#!/usr/bin/env python3
"""
Verification suite for AppSheet data contract and Lead_ID key stability.
Ensures ALL_LEADS satisfies all requirements to serve as canonical AppSheet table.
Uses fast XML/openpyxl streaming.
"""

import sys
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def main():
    print("================================================================================")
    print("HSB SALES OS — APPSHEET DATA CONTRACT & KEY STABILITY VERIFICATION")
    print("================================================================================")

    data_dir = Path("data")
    xlsx_files = sorted(data_dir.glob("*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not xlsx_files:
        print("ERROR: No .xlsx data file found in data/")
        sys.exit(1)

    latest_file = xlsx_files[-1]
    print(f"Reading workbook: {latest_file.name}")

    import openpyxl
    wb = openpyxl.load_workbook(latest_file, read_only=True, data_only=True)
    ws = wb["ALL_LEADS"]

    total_leads = 0
    null_count = 0
    lead_ids = []
    joel_count = 0
    jordi_count = 0

    id_regex = re.compile(r"^HSB-\d{8}-\d{5}$")
    invalid_ids = []

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header = row
            assert header[0] == "Lead-ID", f"Expected 'Lead-ID' in col 0, got {header[0]}"
            assert header[26] == "Verantwortlicher", f"Expected 'Verantwortlicher' in col 26, got {header[26]}"
            continue
        
        lead_id = row[0]
        owner = row[26]

        if lead_id is None or str(lead_id).strip() == "":
            null_count += 1
        else:
            lead_ids.append(str(lead_id))
            if not id_regex.match(str(lead_id)):
                invalid_ids.append(str(lead_id))

        if owner == "Joel Cherino Diaz":
            joel_count += 1
        elif owner == "Jordi Post":
            jordi_count += 1

        total_leads += 1

    wb.close()

    print(f"Total Leads in ALL_LEADS: {total_leads}")
    assert total_leads == 6424, f"Expected 6424 leads, found {total_leads}"

    print(f"LEAD_ID_NULL_COUNT={null_count}")
    assert null_count == 0, f"Found {null_count} null Lead-IDs"

    duplicate_count = len(lead_ids) - len(set(lead_ids))
    print(f"LEAD_ID_DUPLICATE_COUNT={duplicate_count}")
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate Lead-IDs"

    print(f"INVALID_ID_FORMAT_COUNT={len(invalid_ids)}")
    assert len(invalid_ids) == 0, f"Found {len(invalid_ids)} invalid Lead-IDs"

    print(f"JOEL_COUNT={joel_count}")
    print(f"JORDI_COUNT={jordi_count}")
    assert joel_count == 3212, f"Expected 3212 Joel leads, got {joel_count}"
    assert jordi_count == 3212, f"Expected 3212 Jordi leads, got {jordi_count}"

    print("================================================================================")
    print("VERDICT: PASS (AppSheet Data Contract 100% Validated)")
    print("================================================================================")

if __name__ == "__main__":
    main()
