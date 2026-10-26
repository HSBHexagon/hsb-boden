import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

# Mock google modules prior to importing modules that depend on google API
sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

import test_in_google_sheet


class TestInGoogleSheetUnit(unittest.TestCase):
    def build_mock_responses(self):
        mock_service = MagicMock()

        # Gate 1 & Gate 4: spreadsheets().get()
        mock_service.spreadsheets().get().execute.side_effect = [
            # Gate 1
            {
                'sheets': [
                    {'properties': {'title': name, 'sheetId': i}}
                    for i, name in enumerate([
                        "ALL_LEADS", "DASHBOARD", "README", "CONTROL_CENTER",
                        "INBOUND_EVENTS", "ACTIVITIES", "BATCHES"
                    ])
                ]
            },
            # Gate 4: conditional formats meta
            {
                'sheets': [{
                    'properties': {'title': 'ALL_LEADS'},
                    'conditionalFormats': [
                        {
                            'booleanRule': {
                                'condition': {
                                    'type': 'CUSTOM_FORMULA',
                                    'values': [{'userEnteredValue': '=$AO2="sent"'}]
                                },
                                'format': {'backgroundColor': {'red': 0.9, 'green': 0.94, 'blue': 0.992}}
                            }
                        },
                        {
                            'booleanRule': {
                                'condition': {
                                    'type': 'TEXT_EQ',
                                    'values': [{'userEnteredValue': 'sent'}]
                                },
                                'format': {'backgroundColor': {'blue': 0.98}}
                            }
                        }
                    ]
                }]
            }
        ]

        appended_event_id = []
        is_deleted = [False]

        def append_side_effect(*args, **kwargs):
            body = kwargs.get('body', {})
            values = body.get('values', [[]])
            if values and values[0]:
                appended_event_id.append(values[0][0])
            m = MagicMock()
            m.execute.return_value = {'updates': {'updatedRange': 'INBOUND_EVENTS!A10:H10'}}
            return m

        def batch_update_side_effect(*args, **kwargs):
            is_deleted[0] = True
            m = MagicMock()
            m.execute.return_value = {}
            return m

        mock_service.spreadsheets().values().append.side_effect = append_side_effect
        mock_service.spreadsheets().batchUpdate.side_effect = batch_update_side_effect

        def get_side_effect(*args, **kwargs):
            m = MagicMock()
            range_arg = kwargs.get('range', '')
            if range_arg == "DASHBOARD!A4:D8":
                m.execute.return_value = {'values': [
                    ['Total', '6424', '3212', '3212'],
                    ['Row 5'], ['Row 6'], ['Row 7'],
                    ['Sent', '100', '50', '50']
                ]}
            elif range_arg == "INBOUND_EVENTS!A10:H10":
                if not is_deleted[0]:
                    eid = appended_event_id[0] if appended_event_id else "TEST-ROUNDTRIP"
                    m.execute.return_value = {'values': [[eid, '', '', '', '', '', 'TEST-LEAD-0000', '']]}
                else:
                    m.execute.return_value = {'values': []}
            else:
                m.execute.return_value = {'values': []}
            return m

        mock_service.spreadsheets().values().get.side_effect = get_side_effect

        def batch_get_side_effect(*args, **kwargs):
            m = MagicMock()
            ranges = kwargs.get('ranges', [])
            if ranges == ["ALL_LEADS!A1:BD1", "ALL_LEADS!A1:A6500", "ALL_LEADS!AA2:AA6425"]:
                m.execute.return_value = {
                    'valueRanges': [
                        {'values': [['lead_id', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'email'] + ['x']*17 + ['owner'] + ['x']*13 + ['send_status', 'send_datum', 'x', 'reply_status', 'x', 'x', 'batch_status', 'x', 'x', 'x', 'x', 'x', 'internet_message_id', 'x', 'x', 'last_error']]},
                        {'values': [['lead_id']] + [['lead_' + str(i)] for i in range(6424)]},
                        {'values': [['Joel']] * 3212 + [['Jordi']] * 3212}
                    ]
                }
            elif ranges == ["ALL_LEADS!AA2:AA6425", "ALL_LEADS!AO2:AO6425", "ALL_LEADS!AP2:AP6425", "ALL_LEADS!AU2:AU6425"]:
                m.execute.return_value = {
                    'valueRanges': [
                        {'values': [['JOEL']] * 40 + [['JORDI']] * 20 + [['JOEL']] * 5824},
                        {'values': [['sent']] * 60 + [['drafted']] * 5824},
                        {'values': [['2026-01-01']] * 60 + [['']] * 5824},
                        {'values': [['SENT']] * 60 + [['PREPARED']] * 5824},
                    ]
                }
            elif ranges == ["ALL_LEADS!AN52:BD151", "ALL_LEADS!AN3214:BD3313"]:
                m.execute.return_value = {
                    'valueRanges': [
                        {'values': [['x', 'drafted'] + ['x']*11 + ['user@domain.com']] * 100},
                        {'values': [['x', 'drafted'] + ['x']*7 + ['FLOW_RUN_123'] + ['x']*5] * 100}
                    ]
                }
            elif ranges == ["DASHBOARD!C3", "README!A6"]:
                m.execute.return_value = {
                    'valueRanges': [
                        {'values': [['Jordi Post']]},
                        {'values': [['Jordi Post in README']]}
                    ]
                }
            elif ranges == ["ALL_LEADS!AN152:BD1151", "ALL_LEADS!AN3534:BD4533"]:
                m.execute.return_value = {
                    'valueRanges': [
                        {'values': [['x', 'drafted', 'x', 'x', 'x', 'x', 'x', 'DRAFTED', 'x', 'AAMk_123']] * 1000},
                        {'values': [['x', 'drafted', 'x', 'x', 'x', 'x', 'x', 'DRAFTED', 'x', 'FLOW_RUN_123']] * 1000}
                    ]
                }
            else:
                m.execute.return_value = {'valueRanges': []}
            return m

        mock_service.spreadsheets().values().batchGet.side_effect = batch_get_side_effect

        return mock_service

    def test_run_in_sheet_tests_passes_all_gates(self):
        mock_svc = self.build_mock_responses()
        with patch('test_in_google_sheet.get_sheets_service', return_value=mock_svc):
            result = test_in_google_sheet.run_in_sheet_tests()
            self.assertTrue(result, "All gates should pass in the test suite")
            get_count = mock_svc.spreadsheets().values().get.call_count
            batch_get_count = mock_svc.spreadsheets().values().batchGet.call_count
            print(f"\nOptimized API Calls -> values().get(): {get_count}, values().batchGet(): {batch_get_count}")


if __name__ == "__main__":
    unittest.main()
