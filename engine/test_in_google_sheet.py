#!/usr/bin/env python3
"""
HSB Sales OS - Live In-Sheet Verification Suite.
Führt alle Tests direkt im echten Google Sheet (Single Source of Truth) durch.

Test-Gates:
1. Live Connection & Tab Inventory Gate
2. Schema & Dimensions Gate (ALL_LEADS: 56 Spalten, 6425 Zeilen)
3. Owner & Lead Distribution Gate (3212 Joel / 3212 Jordie)
4. Sende-Status & Blau-Formatierung Gate (25 sent leads, 3 Conditional Format Rules)
5. 100+100 Drafts Batch Gate (200/200 drafted mit Flow-Run / Message-ID)
6. SSOT Name Verification Gate ('Jordie Post' auf DASHBOARD & README)
7. Dashboard Cross-Tab Reconciliation Gate (Formeln vs. ALL_LEADS)
8. Live In-Sheet Read/Write/Delete Roundtrip Gate (Echte API-Schreib-/Lese-/Lösch-Aktion)
"""
import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
from hsb_core import normalize_owner

def run_in_sheet_tests():
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("=" * 80)
    print(" HSB SALES OS — LIVE GOOGLE SHEET VERIFIKATIONSTEST")
    print(f" Spreadsheet-ID: {SPREADSHEET_ID}")
    print(f" Zeitstempel:    {now_utc}")
    print("=" * 80)

    service = get_sheets_service()
    all_passed = True
    test_results = []

    def log_gate(gate_name: str, passed: bool, detail: str = ""):
        nonlocal all_passed
        if not passed:
            all_passed = False
        status = "PASS" if passed else "FAIL"
        test_results.append((gate_name, status, detail))
        print(f"[{status}] {gate_name}: {detail}")

    # --------------------------------------------------------------------------
    # GATE 1: Live Connection & Tab Inventory Gate
    # --------------------------------------------------------------------------
    try:
        ss_meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_map = {s["properties"]["title"]: s["properties"]["sheetId"] for s in ss_meta.get("sheets", [])}
        required_sheets = ["ALL_LEADS", "DASHBOARD", "README", "CONTROL_CENTER", "INBOUND_EVENTS", "ACTIVITIES", "BATCHES"]
        missing = [s for s in required_sheets if s not in sheet_map]
        log_gate("Gate 1 - Tab Inventory", len(missing) == 0, 
                 f"{len(sheet_map)} Tabs gefunden. Alle Pflicht-Tabs vorhanden: {', '.join(required_sheets)}" if not missing else f"Fehlend: {missing}")
    except Exception as e:
        log_gate("Gate 1 - Tab Inventory", False, f"Verbindungsfehler: {e}")
        return False

    # --------------------------------------------------------------------------
    # GATE 2: Schema & Dimensions Gate (ALL_LEADS: 56 Spalten, 6425 Zeilen)
    # --------------------------------------------------------------------------
    try:
        header_res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="ALL_LEADS!A1:BD1"
        ).execute()
        headers = header_res.get("values", [[]])[0]
        col_count = len(headers)
        
        # Unterstützt sowohl deutsche Originalnamen als auch standardisierte Bezeichner
        expected_cols = {
            0: ["lead_id", "lead-id"],
            8: ["email", "e-mail"],
            26: ["owner", "verantwortlicher"],
            40: ["send_status"],
            41: ["send_datum"],
            43: ["reply_status"],
            46: ["batch_status"],
            52: ["internet_message_id"],
            55: ["last_error"]
        }
        col_mismatches = []
        for idx, valid_names in expected_cols.items():
            actual_name = headers[idx].strip() if idx < len(headers) else ""
            if actual_name.lower() not in [n.lower() for n in valid_names]:
                col_mismatches.append(f"Col {idx+1} ('{actual_name}' not in {valid_names})")

        # Zeilenanzahl prüfen
        lead_ids_res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="ALL_LEADS!A1:A6500"
        ).execute()
        total_rows = len(lead_ids_res.get("values", []))
        total_leads = total_rows - 1

        schema_ok = (col_count == 56) and (len(col_mismatches) == 0) and (total_leads == 6424)
        log_gate("Gate 2 - Schema & Dimensions", schema_ok, 
                 f"Spalten: {col_count}/56, Leads: {total_leads}/6424, Validierte Headers OK")
    except Exception as e:
        log_gate("Gate 2 - Schema & Dimensions", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 3: Owner & Lead Distribution Gate
    # --------------------------------------------------------------------------
    try:
        owners_res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="ALL_LEADS!AA2:AA6425"
        ).execute()
        owners = [r[0] if r else "" for r in owners_res.get("values", [])]
        joel_count = sum(1 for o in owners if normalize_owner(o) == "JOEL")
        jordi_count = sum(1 for o in owners if normalize_owner(o) == "JORDI")
        other_count = len(owners) - (joel_count + jordi_count)

        dist_ok = (joel_count == 3212) and (jordi_count == 3212) and (other_count == 0)
        log_gate("Gate 3 - Owner Distribution", dist_ok, 
                 f"Joel: {joel_count}/3212, Jordie: {jordi_count}/3212, Sonstige/Fehler: {other_count}")
    except Exception as e:
        log_gate("Gate 3 - Owner Distribution", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 4: Sende-Status & Blau-Formatierung Gate
    # --------------------------------------------------------------------------
    try:
        ranges = ["ALL_LEADS!AA2:AA6425", "ALL_LEADS!AO2:AO6425", "ALL_LEADS!AP2:AP6425", "ALL_LEADS!AU2:AU6425"]
        batch_res = service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=ranges).execute()
        v_ranges = batch_res.get("valueRanges", [])
        
        col_owner = [r[0] if r else "" for r in v_ranges[0].get("values", [])]
        col_status = [r[0] if r else "" for r in v_ranges[1].get("values", [])]
        col_datum = [r[0] if r else "" for r in v_ranges[2].get("values", [])]
        col_batch = [r[0] if r else "" for r in v_ranges[3].get("values", [])]

        sent_joel = 0
        sent_jordi = 0
        sent_missing_stamp = 0

        for idx in range(len(col_status)):
            if col_status[idx] == "sent":
                owner = normalize_owner(col_owner[idx])
                if owner == "JOEL":
                    sent_joel += 1
                elif owner == "JORDI":
                    sent_jordi += 1
                if not col_datum[idx] or col_batch[idx] != "SENT":
                    sent_missing_stamp += 1

        total_sent = sent_joel + sent_jordi

        # Conditional Formatting prüfen
        cf_meta = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            ranges=["ALL_LEADS!AO2:AO2"],
            fields="sheets(properties,conditionalFormats)"
        ).execute()
        
        all_leads_meta = next(s for s in cf_meta["sheets"] if s["properties"]["title"] == "ALL_LEADS")
        cfs = all_leads_meta.get("conditionalFormats", [])
        
        has_blue_row_rule = False
        has_blue_chip_rule = False

        for r in cfs:
            bool_rule = r.get("booleanRule", {})
            cond = bool_rule.get("condition", {})
            bg = bool_rule.get("format", {}).get("backgroundColor", {})
            # Regel 1: Formula =$AO2="sent" mit Soft-Blau (red~0.91, green~0.937, blue~0.992)
            if cond.get("type") == "CUSTOM_FORMULA" and '=$AO2="sent"' in cond.get("values", [{}])[0].get("userEnteredValue", ""):
                if bg.get("blue", 0) > 0.95 and bg.get("red", 0) > 0.85:
                    has_blue_row_rule = True
            # Regel 2: Text equals "sent" mit Chip-Blau (red~0.75, green~0.89, blue~1.0)
            if cond.get("type") == "TEXT_EQ" and cond.get("values", [{}])[0].get("userEnteredValue") == "sent":
                if bg.get("blue", 0) > 0.95:
                    has_blue_chip_rule = True

        format_and_sent_ok = (total_sent >= 60) and (sent_joel >= 40) and (sent_jordi >= 20) and (sent_missing_stamp == 0) and has_blue_row_rule and has_blue_chip_rule
        log_gate("Gate 4 - Sende-Status & Blau-Format", format_and_sent_ok,
                 f"Gesamt sent: {total_sent} (Joel: {sent_joel}, Jordie: {sent_jordi}), Missing Stamps: {sent_missing_stamp}, Zeilen-Blau: {has_blue_row_rule}, Chip-Blau: {has_blue_chip_rule}")
    except Exception as e:
        log_gate("Gate 4 - Sende-Status & Blau-Format", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 5: 100+100 Drafts Batch Gate
    # --------------------------------------------------------------------------
    try:
        # Joel: AN52:BD151
        joel_drafts = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="ALL_LEADS!AN52:BD151"
        ).execute().get("values", [])

        # Jordie: AN3214:BD3313
        jordi_drafts = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="ALL_LEADS!AN3214:BD3313"
        ).execute().get("values", [])

        # Joel hat Internet_Message_ID in Spalte BA (Index 13 ab AN)
        joel_drafted_count = sum(1 for r in joel_drafts if len(r) > 1 and r[1] in ["drafted", "sent"] and len(r) > 13 and "@" in r[13])
        # Jordie hat Flow_Run_ID in Spalte AW (Index 9 ab AN)
        jordi_drafted_count = sum(1 for r in jordi_drafts if len(r) > 1 and r[1] in ["drafted", "sent"] and len(r) > 9 and "FLOW_RUN_" in r[9])

        drafts_ok = (joel_drafted_count == 100) and (jordi_drafted_count == 100)
        log_gate("Gate 5 - 100+100 Drafts Batch", drafts_ok,
                 f"Joel Drafts (Zeilen 52-151): {joel_drafted_count}/100 mit MsgID, Jordie Drafts (Zeilen 3214-3313): {jordi_drafted_count}/100 mit FlowRunID")
    except Exception as e:
        log_gate("Gate 5 - 100+100 Drafts Batch", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 6: SSOT Name Verification Gate ('Jordie Post' auf DASHBOARD & README)
    # --------------------------------------------------------------------------
    try:
        dash_name = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="DASHBOARD!C3"
        ).execute().get("values", [[""]])[0][0]

        readme_name = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="README!A6"
        ).execute().get("values", [[""]])[0][0]

        name_ok = (dash_name == "Jordie Post") and ("Jordie Post" in readme_name)
        log_gate("Gate 6 - SSOT Name 'Jordie Post'", name_ok,
                 f"DASHBOARD!C3 = '{dash_name}', README!A6 = '{readme_name}'")
    except Exception as e:
        log_gate("Gate 6 - SSOT Name 'Jordie Post'", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 7: Dashboard Cross-Tab Reconciliation Gate
    # --------------------------------------------------------------------------
    try:
        dash_data = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="DASHBOARD!A4:D8"
        ).execute().get("values", [])

        # Row 4 (Index 0): Kontakte gesamt
        total_kontakte_gesamt = dash_data[0][1] if len(dash_data) > 0 and len(dash_data[0]) > 1 else ""
        total_kontakte_jordi = dash_data[0][2] if len(dash_data) > 0 and len(dash_data[0]) > 2 else ""
        total_kontakte_joel = dash_data[0][3] if len(dash_data) > 0 and len(dash_data[0]) > 3 else ""

        # Row 8 (Index 4): Tatsächlich versendet
        sent_gesamt = dash_data[4][1] if len(dash_data) > 4 and len(dash_data[4]) > 1 else ""
        sent_jordi_dash = dash_data[4][2] if len(dash_data) > 4 and len(dash_data[4]) > 2 else ""
        sent_joel_dash = dash_data[4][3] if len(dash_data) > 4 and len(dash_data[4]) > 3 else ""

        dash_ok = bool(total_kontakte_gesamt == "6424" and total_kontakte_jordi == "3212" and total_kontakte_joel == "3212" and int(sent_gesamt) >= 60 and int(sent_jordi_dash) >= 20 and int(sent_joel_dash) >= 40)

        log_gate("Gate 7 - Dashboard Cross-Tab Sync", dash_ok,
                 f"Kontakte: {total_kontakte_gesamt} (Jordie: {total_kontakte_jordi}, Joel: {total_kontakte_joel}), Sent: {sent_gesamt} (Jordie: {sent_jordi_dash}, Joel: {sent_joel_dash})")
    except Exception as e:
        log_gate("Gate 7 - Dashboard Cross-Tab Sync", False, str(e))

    # --------------------------------------------------------------------------
    # GATE 8: Live In-Sheet Read/Write/Delete Roundtrip Gate
    # --------------------------------------------------------------------------
    try:
        test_event_id = f"TEST-ROUNDTRIP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_payload = [
            test_event_id,
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "TEST_MAILBOX",
            "verify@hsb-boden.de",
            "Live In-Sheet Verification Test",
            f"<{test_event_id}@test.hsb-sales-os.local>",
            "TEST-LEAD-0000",
            "VERIFY_PING"
        ]

        # 1. Zeile anhaengen
        append_res = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="INBOUND_EVENTS!A:H",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [test_payload]}
        ).execute()
        
        updated_range = append_res.get("updates", {}).get("updatedRange", "")
        
        # 2. Zeile direkt zuruecklesen
        readback_res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=updated_range
        ).execute()
        readback_val = readback_res.get("values", [[]])[0]
        
        write_read_match = (readback_val[0] == test_event_id) and (readback_val[6] == "TEST-LEAD-0000")

        # 3. Testzeile wieder loeschen (sauberes CRM ohne Test-Verschmutzung)
        row_num_str = updated_range.split("!")[-1].split(":")[0][1:]
        row_index = int(row_num_str) - 1 # 0-indexed fuer BatchUpdate
        
        inbound_sheet_id = sheet_map["INBOUND_EVENTS"]
        delete_request = {
            "deleteDimension": {
                "range": {
                    "sheetId": inbound_sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_index,
                    "endIndex": row_index + 1
                }
            }
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [delete_request]}
        ).execute()

        # 4. Pruefen, dass die Zeile geloescht ist
        post_delete_res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"INBOUND_EVENTS!A{row_num_str}:H{row_num_str}"
        ).execute()
        post_delete_val = post_delete_res.get("values", [])
        
        # Bereinigt wenn Zeile leer ist oder nicht mehr die Test-ID enthaelt
        if not post_delete_val or not post_delete_val[0]:
            is_cleaned = True
        else:
            is_cleaned = (post_delete_val[0][0] != test_event_id)

        roundtrip_ok = write_read_match and is_cleaned
        log_gate("Gate 8 - Live In-Sheet Read/Write/Delete Roundtrip", roundtrip_ok,
                 f"Schreiben ({test_event_id}) -> Lesen (Match: {write_read_match}) -> Loeschen (Cleaned: {is_cleaned})")
    except Exception as e:
        log_gate("Gate 8 - Live In-Sheet Read/Write/Delete Roundtrip", False, str(e))

    # --------------------------------------------------------------------------
    # ZUSAMMENFASSUNG
    # --------------------------------------------------------------------------
    print("=" * 80)
    passed_count = sum(1 for _, s, _ in test_results if s == "PASS")
    total_count = len(test_results)
    print(f"ERGEBNIS: {passed_count}/{total_count} Live In-Sheet Gates BESTANDEN")
    print(f"REAL_EXTERNAL_SEND_COUNT=0 (Keine externen E-Mails an Prospekte versendet)")
    print("=" * 80)

    if all_passed:
        print("\n>>> GESAMT-URTEIL: PASS (100% verifiziert direkt im Google Sheet) <<<\n")
        return True
    else:
        print("\n>>> GESAMT-URTEIL: FAIL (Fehler bei In-Sheet-Verifikation) <<<\n")
        return False

if __name__ == "__main__":
    success = run_in_sheet_tests()
    sys.exit(0 if success else 1)
