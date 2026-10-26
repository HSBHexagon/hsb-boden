import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

# Mock google module before importing test_in_google_sheet
sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

import test_in_google_sheet

class MockSpreadsheetsService:
    def __init__(self, tracker):
        self.tracker = tracker

    def get(self, spreadsheetId=None, ranges=None, fields=None):
        self.tracker.call_counts["get"] += 1
        mock = MagicMock()
        if ranges:
            mock.execute.return_value = {
                "sheets": [
                    {
                        "properties": {"title": "ALL_LEADS", "sheetId": 1},
                        "conditionalFormats": [
                            {
                                "booleanRule": {
                                    "condition": {
                                        "type": "CUSTOM_FORMULA",
                                        "values": [{"userEnteredValue": '=$AO2="sent"'}],
                                    },
                                    "format": {
                                        "backgroundColor": {
                                            "red": 0.91,
                                            "green": 0.937,
                                            "blue": 0.992,
                                        }
                                    },
                                }
                            },
                            {
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": "sent"}],
                                    },
                                    "format": {
                                        "backgroundColor": {
                                            "red": 0.75,
                                            "green": 0.89,
                                            "blue": 1.0,
                                        }
                                    },
                                }
                            },
                        ],
                    }
                ]
            }
        else:
            mock.execute.return_value = {
                "sheets": [
                    {"properties": {"title": "ALL_LEADS", "sheetId": 1}},
                    {"properties": {"title": "DASHBOARD", "sheetId": 2}},
                    {"properties": {"title": "README", "sheetId": 3}},
                    {"properties": {"title": "CONTROL_CENTER", "sheetId": 4}},
                    {"properties": {"title": "INBOUND_EVENTS", "sheetId": 5}},
                    {"properties": {"title": "ACTIVITIES", "sheetId": 6}},
                    {"properties": {"title": "BATCHES", "sheetId": 7}},
                ]
            }
        return mock

    def values(self):
        return MockValuesService(self.tracker)

    def batchUpdate(self, spreadsheetId=None, body=None):
        self.tracker.call_counts["batchUpdate"] += 1
        mock = MagicMock()
        mock.execute.return_value = {}
        return mock

class MockValuesService:
    def __init__(self, tracker):
        self.tracker = tracker

    def get(self, spreadsheetId=None, range=None, valueRenderOption=None):
        self.tracker.call_counts["values_get"] += 1
        mock = MagicMock()
        if range == "ALL_LEADS!A1:BD1":
            headers = ["lead_id"] + [""] * 7 + ["email"] + [""] * 17 + ["owner"] + [""] * 13 + ["send_status", "send_datum"] + [""] * 1 + ["reply_status"] + [""] * 2 + ["batch_status"] + [""] * 5 + ["internet_message_id"] + [""] * 2 + ["last_error"]
            mock.execute.return_value = {"values": [headers]}
        elif range == "ALL_LEADS!A1:A6500":
            mock.execute.return_value = {"values": [["header"]] + [["id"]] * 6424}
        elif range == "ALL_LEADS!AA2:AA6425":
            mock.execute.return_value = {"values": [["Joel"]] * 3212 + [["Jordi"]] * 3212}
        elif range == "ALL_LEADS!AN52:BD151":
            row = [""] * 14
            row[1] = "drafted"
            row[13] = "msg@id"
            mock.execute.return_value = {"values": [row] * 100}
        elif range == "ALL_LEADS!AN3214:BD3313":
            row = [""] * 10
            row[1] = "drafted"
            row[9] = "FLOW_RUN_123"
            mock.execute.return_value = {"values": [row] * 100}
        elif range == "DASHBOARD!C3":
            mock.execute.return_value = {"values": [["Jordi Post"]]}
        elif range == "README!A6":
            mock.execute.return_value = {"values": [["Jordi Post - Owner"]]}
        elif range == "DASHBOARD!A4:D8":
            mock.execute.return_value = {
                "values": [
                    ["Kontakte gesamt", "6424", "3212", "3212"],
                    ["", "", "", ""],
                    ["", "", "", ""],
                    ["", "", "", ""],
                    ["Versendet", "60", "20", "40"],
                ]
            }
        elif range and "INBOUND_EVENTS!A100:H100" in range:
            if self.tracker.deleted:
                mock.execute.return_value = {"values": []}
            else:
                event_id = getattr(self.tracker, "current_event_id", "TEST-ROUNDTRIP-123")
                mock.execute.return_value = {"values": [[event_id, "", "", "", "", "", "TEST-LEAD-0000", ""]]}
        elif range and "INBOUND_EVENTS!" in range:
            event_id = getattr(self.tracker, "current_event_id", "TEST-ROUNDTRIP-123")
            mock.execute.return_value = {"values": [[event_id, "", "", "", "", "", "TEST-LEAD-0000", ""]]}
        elif range == "ALL_LEADS!AN152:BD1151":
            row = [""] * 10
            row[1] = "drafted"
            row[7] = "DRAFTED"
            row[9] = "AAMk123"
            mock.execute.return_value = {"values": [row] * 1000}
        elif range == "ALL_LEADS!AN3534:BD4533":
            row = [""] * 10
            row[1] = "drafted"
            row[7] = "DRAFTED"
            row[9] = "FLOW_RUN_123"
            mock.execute.return_value = {"values": [row] * 1000}
        else:
            mock.execute.return_value = {"values": [["dummy"]]}
        return mock

    def batchGet(self, spreadsheetId=None, ranges=None):
        self.tracker.call_counts["values_batchGet"] += 1
        mock = MagicMock()
        value_ranges = []
        for r in ranges:
            if r == "ALL_LEADS!AA2:AA6425":
                value_ranges.append({"values": [["Joel"]] * 40 + [["Jordi"]] * 20})
            elif r == "ALL_LEADS!AO2:AO6425":
                value_ranges.append({"values": [["sent"]] * 60})
            elif r == "ALL_LEADS!AP2:AP6425":
                value_ranges.append({"values": [["2026-01-01"]] * 60})
            elif r == "ALL_LEADS!AU2:AU6425":
                value_ranges.append({"values": [["SENT"]] * 60})
            elif r == "ALL_LEADS!A1:BD1":
                headers = ["lead_id"] + [""] * 7 + ["email"] + [""] * 17 + ["owner"] + [""] * 13 + ["send_status", "send_datum"] + [""] * 1 + ["reply_status"] + [""] * 2 + ["batch_status"] + [""] * 5 + ["internet_message_id"] + [""] * 2 + ["last_error"]
                value_ranges.append({"values": [headers]})
            elif r == "ALL_LEADS!A1:A6500":
                value_ranges.append({"values": [["header"]] + [["id"]] * 6424})
            elif r == "ALL_LEADS!AN52:BD151":
                row = [""] * 14
                row[1] = "drafted"
                row[13] = "msg@id"
                value_ranges.append({"values": [row] * 100})
            elif r == "ALL_LEADS!AN3214:BD3313":
                row = [""] * 10
                row[1] = "drafted"
                row[9] = "FLOW_RUN_123"
                value_ranges.append({"values": [row] * 100})
            elif r == "DASHBOARD!C3":
                value_ranges.append({"values": [["Jordi Post"]]})
            elif r == "README!A6":
                value_ranges.append({"values": [["Jordi Post - Owner"]]})
            elif r == "ALL_LEADS!AN152:BD1151":
                row = [""] * 10
                row[1] = "drafted"
                row[7] = "DRAFTED"
                row[9] = "AAMk123"
                value_ranges.append({"values": [row] * 1000})
            elif r == "ALL_LEADS!AN3534:BD4533":
                row = [""] * 10
                row[1] = "drafted"
                row[7] = "DRAFTED"
                row[9] = "FLOW_RUN_123"
                value_ranges.append({"values": [row] * 1000})
            else:
                value_ranges.append({"values": []})
        mock.execute.return_value = {"valueRanges": value_ranges}
        return mock

    def append(self, spreadsheetId=None, range=None, valueInputOption=None, insertDataOption=None, body=None):
        self.tracker.call_counts["values_append"] += 1
        if body and body.get("values"):
            self.tracker.current_event_id = body["values"][0][0]
        mock = MagicMock()
        mock.execute.return_value = {"updates": {"updatedRange": "INBOUND_EVENTS!A100:H100"}}
        return mock

class MockSheetsService:
    def __init__(self):
        self.call_counts = {
            "get": 0,
            "values_get": 0,
            "values_batchGet": 0,
            "values_append": 0,
            "batchUpdate": 0,
        }
        self.current_event_id = None
        self.deleted = False

    def spreadsheets(self):
        return MockSpreadsheetsService(self)

def test_run_in_sheet_tests_mocked():
    mock_svc = MockSheetsService()
    # Intercept batchUpdate to set deleted flag
    orig_sp = mock_svc.spreadsheets
    def spreadsheets_override():
        sp = orig_sp()
        orig_bu = sp.batchUpdate
        def batchUpdate_wrapper(spreadsheetId=None, body=None):
            mock_svc.deleted = True
            return orig_bu(spreadsheetId=spreadsheetId, body=body)
        sp.batchUpdate = batchUpdate_wrapper
        return sp
    mock_svc.spreadsheets = spreadsheets_override

    with patch("test_in_google_sheet.get_sheets_service", return_value=mock_svc):
        success = test_in_google_sheet.run_in_sheet_tests()
        assert success is True
        total_calls = sum(mock_svc.call_counts.values())
        print("\n=== OPTIMIZED API CALL COUNTS ===")
        for k, v in mock_svc.call_counts.items():
            print(f"  {k}: {v}")
        print(f"Total API roundtrips: {total_calls}")

if __name__ == "__main__":
    test_run_in_sheet_tests_mocked()
