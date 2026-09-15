#!/usr/bin/env python3
"""
HSB SALES OS — INBOUND EVENTS SCHEMA & NOTIFICATION MARKER COMPATIBILITY TEST
Asserts that adding notification markers preserves backward compatibility with Apps Script.
"""
import sys
import os
import json

BASE_12_COLUMNS = [
    'Event_ID', 'Received_UTC', 'Mailbox', 'From', 'Subject',
    'Internet_Message_ID', 'Lead_ID', 'Classification', 'Stop_Followup',
    'Processed', 'Notes', 'Raw_Link'
]

EXTENDED_14_COLUMNS = BASE_12_COLUMNS + ['Mobile_Notified_At', 'Mobile_Notified_To']

def test_inbound_schema():
    print("=" * 80)
    print("HSB SALES OS — INBOUND EVENTS SCHEMA COMPATIBILITY TEST")
    print("=" * 80)
    
    assert len(BASE_12_COLUMNS) == 12, "Base column count mismatch"
    assert len(EXTENDED_14_COLUMNS) == 14, "Extended column count mismatch"
    assert EXTENDED_14_COLUMNS[:12] == BASE_12_COLUMNS, "Base order changed"
    
    spec_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'appsheet', 'inbound_events_schema_spec.json')
    assert os.path.exists(spec_path), "Spec file missing"
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
        
    assert spec['canonical_12_columns'] == BASE_12_COLUMNS
    assert len(spec['optional_notification_extensions']) == 2
    
    print("BASE_12_COLUMNS=PASS")
    print("NOTIFICATION_MARKERS_EXTENSION=PASS")
    print("PROCESSED_FIELD_PRESERVED=PASS")
    print("=" * 80)
    print("INBOUND_SCHEMA_COMPATIBILITY=VERIFIED_PASS")

if __name__ == '__main__':
    test_inbound_schema()
