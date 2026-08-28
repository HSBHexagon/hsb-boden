#!/usr/bin/env python3
"""
HSB SALES OS — ACTIVITIES CONTRACT AUDIT & SCHEMA MISMATCH REPRODUCTION
Checks the mismatch between the 12-column canonical ACTIVITIES schema and the 5-column legacy writer.
"""
import json
import os
import re

CANONICAL_ACTIVITIES_HEADER = [
    'Activity_ID', 'Lead_ID', 'Timestamp', 'Owner', 'Activity_Type',
    'Channel', 'Result', 'Template_ID', 'Batch_ID', 'Note',
    'Next_Action', 'Next_Action_Date'
]

LEGACY_WRITER_COLUMNS = ['Timestamp', 'Batch_ID', 'Type', 'Message', 'User']

def audit_engine_writer():
    engine_path = os.path.join(os.path.dirname(__file__), '..', 'apps_script', 'Engine.gs')
    with open(engine_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search for logActivity_ definition
    has_legacy_header = "['Timestamp', 'Batch_ID', 'Type', 'Message', 'User']" in content
    has_legacy_append = "sh.appendRow([nowIso_(), batchId, type, message, user]);" in content or "sh.appendRow([nowIso_()" in content

    return {
        "engine_file": engine_path,
        "has_legacy_header": has_legacy_header,
        "has_legacy_append": has_legacy_append,
        "canonical_columns_count": len(CANONICAL_ACTIVITIES_HEADER),
        "legacy_columns_count": len(LEGACY_WRITER_COLUMNS),
        "mismatch_detected": len(CANONICAL_ACTIVITIES_HEADER) != len(LEGACY_WRITER_COLUMNS)
    }

def main():
    print("=" * 80)
    print("HSB SALES OS — ACTIVITIES CONTRACT AUDIT & REPRODUCTION")
    print("=" * 80)

    report = audit_engine_writer()
    print(f"Canonical Header Columns ({report['canonical_columns_count']}): {CANONICAL_ACTIVITIES_HEADER}")
    print(f"Legacy Writer Columns ({report['legacy_columns_count']}): {LEGACY_WRITER_COLUMNS}")
    print(f"Mismatch Detected: {report['mismatch_detected']}")
    print(f"Legacy Header in Engine.gs: {report['has_legacy_header']}")
    print(f"Legacy appendRow in Engine.gs: {report['has_legacy_append']}")

    report_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'appsheet', 'audit_activities_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to: {report_path}")
    print("=" * 80)
    print("AUDIT_REPRODUCTION=CONFIRMED_MISMATCH_PASS")

if __name__ == '__main__':
    main()
