# HSB Sales OS Mobile AppSheet Hardening & Activities Contract Supplement

> **Superpowers Implementation Plan Supplement**  
> **Status:** `PLAN_ONLY = YES` | `IMPLEMENTATION_FORBIDDEN = YES`  
> **Scope:** Hardening supplement to the approved plan (`docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md`, commit `a3e3f86`).  
> **Core Architecture:** `PRIMARY_MOBILE_SURFACE = APPSHEET`, `CANONICAL_SSOT = GOOGLE_SHEET` (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`), `CORE_BACKEND = EXISTING_APPS_SCRIPT` (`1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`).  
> **Hard Invariants:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`. No new CRM, no database migration (no Supabase/PostgreSQL), no PWA, no Sheets Canvas, no Looker, no Gemini.

---

## 1. Executive Summary & Authoritative Findings

### Load-Bearing Problem Statement: `ACTIVITIES` Contract Mismatch
The live Google Sheet header for `ACTIVITIES` defines 12 columns:
`Activity_ID` | `Lead_ID` | `Timestamp` | `Owner` | `Activity_Type` | `Channel` | `Result` | `Template_ID` | `Batch_ID` | `Note` | `Next_Action` | `Next_Action_Date`

However, the existing Apps Script writer (`logActivity_` in `Engine.gs`, `Actions.gs`, `Code.gs`) writes 5 positional columns:
`[nowIso_(), batchId, type, message, user]`

This causes a severe production schema shift starting at Column A:
- **Col A (`Activity_ID`):** Populated with Timestamp string (`nowIso_()`)
- **Col B (`Lead_ID`):** Populated with `Batch_ID` (or empty string `''`)
- **Col C (`Timestamp`):** Populated with `Type` (e.g. `'QUALIFY'`, `'PREPARED'`)
- **Col D (`Owner`):** Populated with `Message` (description string)
- **Col E (`Activity_Type`):** Populated with `User` (`Session.getActiveUser().getEmail()` or `'unbekannt'`)
- **Cols F–L:** Blank

### Purpose of this Supplement
1. Establish a canonical 12-column append contract for all future `ACTIVITIES` writes via TDD.
2. Provide a non-destructive normalization procedure for historical audit rows (zero data loss).
3. Connect `ACTIVITIES[Lead_ID]` to `ALL_LEADS[Lead-ID]` in AppSheet via native `Ref` / reverse-reference (`REF_ROWS`) for an inline activity timeline on the mobile `Lead Detail` view (no full-table `SELECT`/`FILTER` scans).
4. Add AppSheet-originated audit logging for safe human edits (`Notizen`, `Nächste Aktion`, `Follow-up-Datum`) with strict idempotency.
5. Reconcile `INBOUND_EVENTS` notification markers (`Mobile_Notified_At`, `Mobile_Notified_To`) without breaking existing 12-column indexing.
6. Formalize the 56-column `ALL_LEADS` field ownership matrix and enforce primary operator identities.

---

## 2. Architecture & Data Model Matrix

### A. Canonical 12-Column `ACTIVITIES` Contract

| Col Index | Header Name | Data Type | Key / Ref | Allowed Values / Format | Populated By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 (A)** | `Activity_ID` | Text | Primary Key | `^ACT-\d{8}-[A-Z0-9]{5,10}$` | Apps Script UUID / Timestamp Hash |
| **2 (B)** | `Lead_ID` | Text | Ref → `ALL_LEADS[Lead-ID]` | `^HSB-\d{8}-\d{5}$` or `''` (batch-only) | Apps Script / AppSheet |
| **3 (C)** | `Timestamp` | DateTime | None | ISO-8601 (`YYYY-MM-DDTHH:mm:ss.sssZ`) | `nowIso_()` |
| **4 (D)** | `Owner` | Text | None | `"JOEL"`, `"JORDI"`, `"ADMIN"`, `"SYSTEM"` | `normalizeOwner_()` |
| **5 (E)** | `Activity_Type` | Enum | None | `BATCH_PREPARED`, `OWNER_APPROVED`, `EML_EXPORTED`, `SENT_CONFIRMED`, `INBOUND_REPLY`, `NOTE_EDITED`, `STATUS_CHANGED`, `QUALIFY` | Controlled Enum |
| **6 (F)** | `Channel` | Enum | None | `EMAIL`, `PHONE`, `MANUAL`, `SYSTEM`, `INBOUND` | Action context |
| **7 (G)** | `Result` | Enum | None | `SUCCESS`, `PENDING`, `NEEDS_REVIEW`, `BLOCKED`, `IGNORED` | Outcome status |
| **8 (H)** | `Template_ID` | Text | None | Template identifier or `''` | Campaign config |
| **9 (I)** | `Batch_ID` | Text | Ref → `BATCHES[Batch_ID]` | `^HSB-\d{8}-[A-Z]+-\d{4}$` or `''` | Batch Engine |
| **10 (J)** | `Note` | LongText | None | Detailed audit message or note delta | User / System summary |
| **11 (K)** | `Next_Action` | Text | None | Task label (e.g. "Anrufen") or `''` | Operator input |
| **12 (L)** | `Next_Action_Date` | Date | None | `YYYY-MM-DD` or `''` | Operator input |

### B. `ALL_LEADS` Field Ownership Matrix (56 Columns Summary)

| Category | Columns Included | Native Sheet Validation | AppSheet Mutability (`Editable_If`) | Ownership Semantics |
| :--- | :--- | :--- | :--- | :--- |
| **HUMAN_EDITABLE** | `Notizen` (Col 29), `Nächste Aktion` (Col 17), `Follow-up-Datum` (Col 18) | List validation on `Nächste Aktion`; Date validation on `Follow-up-Datum` | `TRUE` | Operator sales call notes & follow-up scheduling |
| **SYSTEM_MANAGED** | `Batch_ID` (Col 40), `Send_Status` (Col 41), `Send_Datum` (Col 42), `Bounce_Status` (Col 43), `Reply_Status` (Col 44), `Legal_Basis` (Col 45), `Suppressed` (Col 46), `Batch_Status` (Col 47), `Prepared_At` (Col 48), `Draft_ID` (Col 49), `Drafted_At` (Col 50), `Approved_At` (Col 51), `Outlook_Message_ID` (Col 52), `Internet_Message_ID` (Col 53), `Conversation_ID` (Col 54), `Last_Reply_At` (Col 55), `Last_Error` (Col 56), `Versandfreigabe` (Col 26), `Status` (Col 14), `Score` (Col 13) | Protected range / No manual overwrite; Dropdown on `Versandfreigabe` (yes/no) | `FALSE` (Read-Only) | Owned strictly by Apps Script Batch Engine, EML Generator & Inbound Webhooks |
| **STATIC_CANONICAL** | `Lead-ID` (Col 1), `Firma` (Col 2), `Standort` (Col 3), `Region` (Col 4), `Branche` (Col 5), `Tier` (Col 6), `Ansprechpartner` (Col 7), `Rolle` (Col 8), `E-Mail` (Col 9), `Telefon` (Col 10), `Website` (Col 11), `Quelle` (Col 12), `Verantwortlicher` (Col 27), `Flyer-Anhang` (Col 28), `Kampagne_ID` (Col 30), `Email_Template_ID` (Col 31), `Flyer_ID` (Col 32), `Flyer_URL` (Col 33), `Landing_URL` (Col 34), `UTM_*` (Cols 35–39) | Protected range | `FALSE` (Read-Only) | Master prospect record from source data |
| **AUDIT_ONLY** | `ACTIVITIES` sheet rows, `INBOUND_EVENTS` sheet rows, `SYSTEM_EVIDENCE` | Protected sheet | `FALSE` (Read-Only) | Append-only tamper-evident event log |

---

## 3. Detailed Task Decomposition (10 Discrete Tasks)

```
┌────────────────────────────────────────────────────────────────────────┐
│             HSB SALES OS MOBILE HARDENING SUPPLEMENT TASKS             │
├────────────────────────────────────────────────────────────────────────┤
│ Task 1: Audit Current ACTIVITIES Writer/Schema & Reproduce Mismatch    │
│ Task 2: Implement Canonical 12-Column ACTIVITIES Append Contract (TDD) │
│ Task 3: Non-Destructive Historical ACTIVITIES Normalization Procedure  │
│ Task 4: Configure AppSheet Lead↔Activities Ref & Inline Timeline View  │
│ Task 5: Implement AppSheet-Originated Mobile Edit Activity Logging     │
│ Task 6: Audit INBOUND_EVENTS Schema & Define Safe Notification Marker  │
│ Task 7: Harden Primary Operator Identity Mapping & Allowlist Security  │
│ Task 8: Establish ALL_LEADS 56-Column Field Ownership Governance       │
│ Task 9: Full Core Sales OS Regression & Multi-Device Sync Verification │
│ Task 10: Runbook, Rollback Procedures & Final Independent Verification │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Task 1: Audit Current `ACTIVITIES` Writer/Schema & Reproduce Mismatch

- **Surfaces Inspected:** `apps_script/Engine.gs` (lines 675–685), `apps_script/Actions.gs`, `apps_script/Code.gs`, `tests/test_apps_script.js`, Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` (`ACTIVITIES` sheet).
- **Pre-Change Verification (Failing Condition / Mismatch Proof):**
  Create `tests/audit_activities_contract.py` asserting current discrepancy:
  1. Live Sheet Header length is 12 columns.
  2. `logActivity_` in `Engine.gs` produces arrays of length 5 (`['Timestamp', 'Batch_ID', 'Type', 'Message', 'User']`).
  3. Col A contains timestamp instead of `Activity_ID`.
  4. Assert test fails against expected 12-column canonical contract.
- **Implementation:**
  Write `tests/audit_activities_contract.py` and output diagnostic evidence to `docs/appsheet/audit_activities_report.json`.
- **Verification Command:**
  ```sh
  python3 tests/audit_activities_contract.py
  ```
- **Expected Success:** Script confirms exact 5-column vs. 12-column mismatch with zero execution errors.
- **Commit Boundary:** `test(activities): add audit script and report for 5-col vs 12-col activities schema mismatch`

---

### Task 2: Implement Canonical 12-Column `ACTIVITIES` Append Contract (TDD)

- **Surfaces Modified:** `apps_script/Engine.gs`, `apps_script/Actions.gs`, `apps_script/Code.gs`, `apps_script/HSB_SALES_OS.gs`, `deploy/HSB_SALES_OS.js`.
- **Pre-Change Test:**
  Add unit test in `tests/test_apps_script.js`:
  ```javascript
  // testActivity12ColumnContract:
  // Verifies that logActivity_ appends an array with exactly 12 columns matching the canonical schema.
  ```
  Running `node tests/test_apps_script.js` fails before implementation.
- **Implementation Specification:**
  Refactor `logActivity_` in `Engine.gs`:
  ```javascript
  function appendActivityRow_(entry) {
    const sh = sheet_(CFG.SHEET_ACTIVITY);
    if (sh.getLastRow() === 0) {
      sh.appendRow([
        'Activity_ID', 'Lead_ID', 'Timestamp', 'Owner', 'Activity_Type',
        'Channel', 'Result', 'Template_ID', 'Batch_ID', 'Note',
        'Next_Action', 'Next_Action_Date'
      ]);
      sh.getRange(1, 1, 1, 12).setFontWeight('bold').setBackground('#e8eaed');
      sh.setFrozenRows(1);
    }
    const actId = entry.activityId || ('ACT-' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd') + '-' + Utilities.getUuid().substring(0, 8).toUpperCase());
    const ts = entry.timestamp || nowIso_();
    const owner = normalizeOwner_(entry.owner || 'SYSTEM');
    const row = [
      actId,
      entry.leadId || '',
      ts,
      owner,
      entry.activityType || 'SYSTEM_EVENT',
      entry.channel || 'SYSTEM',
      entry.result || 'SUCCESS',
      entry.templateId || '',
      entry.batchId || '',
      entry.note || '',
      entry.nextAction || '',
      entry.nextActionDate || ''
    ];
    sh.appendRow(row);
  }
  ```
  Update `logActivity_(batchId, type, message)` as a backward-compatible wrapper calling `appendActivityRow_`.
- **Verification Commands:**
  ```sh
  node tests/test_apps_script.js
  node tests/verifier_suite.js
  ```
- **Expected Success:** All unit tests and verifier suite pass; new activity rows have exactly 12 columns.
- **Commit Boundary:** `fix(engine): implement canonical 12-column appendActivityRow_ and update callers`

---

### Task 3: Non-Destructive Historical `ACTIVITIES` Normalization Procedure

- **Surfaces Inspected:** `ACTIVITIES` worksheet in `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` (and offline backup `data/HSB CRM MASTER 6424 – Sales OS – 2026-08-21.xlsx`).
- **Migration Strategy:**
  1. Read all existing data rows from `ACTIVITIES`.
  2. For rows with 5 legacy columns:
     - `Activity_ID` = Generate deterministic ID `ACT-LEGACY-YYYYMMDD-ROWINDEX`.
     - `Lead_ID` = If legacy `Batch_ID` matches regex `^HSB-\d{8}-\d{5}$`, assign to `Lead_ID`; otherwise set `Lead_ID = ''`.
     - `Timestamp` = Parse legacy Col A timestamp (ISO-8601).
     - `Owner` = Legacy Col E user mapped via `normalizeOwner_()`.
     - `Activity_Type` = Legacy Col C type (e.g. `'QUALIFY'`, `'PREPARED'`).
     - `Channel` = `'SYSTEM'`.
     - `Result` = `'LOGGED'`.
     - `Template_ID` = `''`.
     - `Batch_ID` = Legacy Col B if matches batch regex, else `''`.
     - `Note` = Legacy Col D message string.
     - `Next_Action` = `''`.
     - `Next_Action_Date` = `''`.
  3. Unambiguous/Unparseable rows: Keep as `Activity_Type = 'LEGACY_UNPARSED'` with full text preserved in `Note`. Zero row deletion.
- **Implementation:** `tests/normalize_historical_activities.py` (with `--dry-run` and `--apply` flags).
- **Verification Step:** Run `python3 tests/normalize_historical_activities.py --dry-run` and verify `ROWS_INPUT == ROWS_OUTPUT` with zero dropped rows.
- **Commit Boundary:** `feat(activities): add historical activity normalization tool with zero-loss verification`

---

### Task 4: Configure AppSheet Lead↔Activities Ref & Inline Timeline View

- **Surfaces Inspected:** AppSheet Data → Tables (`Activities`), UX → Views (`Lead_Detail`, `Activities_Inline`).
- **Configuration Specification:**
  1. **Table `Activities` (Source: `ACTIVITIES`):**
     - Key Column: `Activity_ID` (Type: `Text`, Editable: `FALSE`).
     - Reference Column: `Lead_ID` (Type: `Ref`, Referenced Table: `Leads`, IsPartOf: `TRUE`).
     - Columns: `Timestamp` (DateTime), `Owner` (Text), `Activity_Type` (Enum), `Channel` (Enum), `Result` (Enum), `Note` (LongText), `Next_Action` (Text), `Next_Action_Date` (Date).
  2. **Table `Leads` (`ALL_LEADS`):**
     - AppSheet automatically exposes virtual column `[Related Activities]` with expression:
       `REF_ROWS("Activities", "Lead_ID")` (High performance, avoids expensive `FILTER` scans).
  3. **Inline View `Activities_Inline` (Type: `Table` / `Deck`):**
     - Position: `ref`
     - Sort: `Timestamp` (Descending)
     - Display Columns: `Timestamp`, `Activity_Type`, `Channel`, `Note`, `Next_Action`, `Next_Action_Date`.
     - Max inline items: 5 with "View All" link.
- **Verification Step:** Export AppSheet table and view schema to `docs/appsheet/relational_activity_timeline_spec.json`.
- **Commit Boundary:** `docs(appsheet): specify Lead-Activities Ref relationship and inline timeline view`

---

### Task 5: Implement AppSheet-Originated Mobile Edit Activity Logging

- **Surfaces Inspected:** AppSheet Behavior → Actions & Automation Bots.
- **Mechanism Specification:**
  1. **AppSheet Data-Change Bot:**
     - Event Name: `Audit_Mobile_Lead_Edit`
     - Event Type: `Data Change` (Updates only on table `Leads`)
     - Condition:
       ```appsheet
       OR(
         [_THISROW_BEFORE].[Notizen] <> [_THISROW_AFTER].[Notizen],
         [_THISROW_BEFORE].[Nächste Aktion] <> [_THISROW_AFTER].[Nächste Aktion],
         [_THISROW_BEFORE].[Follow-up-Datum] <> [_THISROW_AFTER].[Follow-up-Datum]
       )
       ```
     - Task Name: `Append_Mobile_Audit_Activity`
     - Action Type: `Add a new row to another table using values from this row`
     - Target Table: `Activities`
     - Column Mappings:
       - `Activity_ID` = `CONCATENATE("ACT-MOB-", UNIQUEID())`
       - `Lead_ID` = `[_THISROW].[Lead-ID]`
       - `Timestamp` = `NOW()`
       - `Owner` = `USEREMAIL()`
       - `Activity_Type` = `"NOTE_EDITED"`
       - `Channel` = `"MANUAL"`
       - `Result` = `"SAVED"`
       - `Note` = `CONCATENATE("Mobile Edit durch ", USEREMAIL(), ": Notizen='", [_THISROW].[Notizen], "', Nächste Aktion='", [_THISROW].[Nächste Aktion], "', Follow-up='", TEXT([_THISROW].[Follow-up-Datum]), "'")`
       - `Next_Action` = `[_THISROW].[Nächste Aktion]`
       - `Next_Action_Date` = `[_THISROW].[Follow-up-Datum]`
  2. **Idempotency Guarantee:**
     - Only triggers on user-initiated mobile sync commits in AppSheet; does NOT fire on external Sheets/Apps Script mutations.
- **Verification Step:** Record action and bot definition in `docs/appsheet/mobile_edit_audit_spec.json`.
- **Commit Boundary:** `docs(appsheet): configure mobile edit audit bot and activity recording spec`

---

### Task 6: Audit `INBOUND_EVENTS` Schema & Define Safe Notification Marker

- **Surfaces Inspected:** `apps_script/Actions.gs` (inbound processing functions), `apps_script/Config.gs`, `INBOUND_EVENTS` worksheet.
- **Current Header Audit (12 Columns):**
  `Event_ID` (1), `Received_UTC` (2), `Mailbox` (3), `From` (4), `Subject` (5), `Internet_Message_ID` (6), `Lead_ID` (7), `Classification` (8), `Stop_Followup` (9), `Processed` (10), `Notes` (11), `Raw_Link` (12).
- **Code Compatibility & Extension Rule:**
  - Verify that Apps Script reads `INBOUND_EVENTS` by header name map (`colMap_`) or safe index offsets.
  - If scheduled push notifications are licensed and active:
    - Add Column 13: `Mobile_Notified_At` (DateTime)
    - Add Column 14: `Mobile_Notified_To` (Text)
  - Scheduled AppSheet Bot evaluates filter: `[Classification] = "REPLY" AND ISBLANK([Mobile_Notified_At])`.
  - Upon sending push, bot updates `Mobile_Notified_At = NOW()` and `Mobile_Notified_To = USEREMAIL()`.
  - If scheduled bot is deferred (`NOTIFICATION_FEATURE_STATUS = DEFERRED_OPTIONAL`), columns remain optional and do not block core mobile rollout.
- **Verification Step:** Validate header mapping in `tests/test_inbound_schema_compatibility.py`.
- **Commit Boundary:** `docs(appsheet): audit inbound events schema and specify mobile notification markers`

---

### Task 7: Harden Primary Operator Identity Mapping & Allowlist Security

- **Surfaces Inspected:** `docs/appsheet/operator_identities_matrix.json`, AppSheet Users & Row Security.
- **Primary Identity Allowlist Specification:**
  - `PRIMARY_JOEL_APPSHEET_IDENTITY` = `j-cherino@hsb-boden.de`
  - `PRIMARY_JORDI_APPSHEET_IDENTITY` = `j-post@hsb-boden.de`
  - `PRIMARY_ADMIN_APPSHEET_IDENTITY` = `cherinodiaz@outlook.com`
- **Strict Row Security Filter on `ALL_LEADS`:**
  ```appsheet
  SWITCH(
    USEREMAIL(),
    "j-cherino@hsb-boden.de", [Verantwortlicher] = "Joel Cherino Diaz",
    "j-post@hsb-boden.de", [Verantwortlicher] = "Jordi Post",
    "cherinodiaz@outlook.com", TRUE,
    FALSE
  )
  ```
- **Alternate Account Policy:**
  - `cherinojoel@gmail.com`, `info@hsb-boden.de`, or shared mailboxes receive `FALSE` (0 rows visible).
  - No Google Drive permissions modified during planning; permission reduction is a separate approval gate.
- **Verification Step:** Record full identity mapping in `docs/appsheet/operator_identities_matrix.json`.
- **Commit Boundary:** `docs(appsheet): formalize primary operator identities and fail-closed security rule`

---

### Task 8: Establish `ALL_LEADS` 56-Column Field Ownership Governance

- **Surfaces Created:** `docs/appsheet/FIELD_OWNERSHIP_MATRIX.md`.
- **Governance Specification:**
  - Full enumeration of Columns 1 through 56 in `ALL_LEADS`.
  - For each column, explicitly define:
    1. Header Name & Index.
    2. Data Type & Default Value.
    3. Ownership: `HUMAN_EDITABLE` vs. `SYSTEM_MANAGED` vs. `STATIC_CANONICAL` vs. `AUDIT_ONLY`.
    4. Google Sheets Native Validation (e.g. `Nächste Aktion` list validation, `Versandfreigabe` yes/no validation).
    5. AppSheet `Editable_If` rule (`TRUE` only for `Notizen`, `Nächste Aktion`, `Follow-up-Datum`; `FALSE` for all others).
- **Prohibition:** No artificial dropdowns added to `Tier` or `Verantwortlicher` without documented business justification.
- **Verification Step:** Verify `FIELD_OWNERSHIP_MATRIX.md` covers all 56 columns without gaps.
- **Commit Boundary:** `docs(appsheet): document comprehensive 56-column ALL_LEADS field ownership matrix`

---

### Task 9: Full Core Sales OS Regression & Multi-Device Sync Verification

- **Surfaces Inspected:** Core test suites across JavaScript and Python.
- **Commands Executed:**
  ```sh
  cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
  node tests/test_apps_script.js
  python3 tests/test_matrix.py
  python3 tests/test_graph_drafts.py
  node tests/verifier_suite.js
  python3 tests/test_security_filter.py
  python3 tests/test_protected_range_write.py
  git diff --check
  ```
- **Strict Invariants:**
  - `JS_TESTS = 290/290 PASS`
  - `PYTHON_MATRIX = 91/91 PASS`
  - `GRAPH_TESTS = 22/22 PASS`
  - `VERIFIER_SUITE = ALL_7_GATES_PASS`
  - `OWNER_CROSSOVER_COUNT = 0`
  - `SOURCE_DEPLOY_DIFF = 0`
  - `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`
- **Commit Boundary:** `test(regression): verify complete Sales OS regression suite passes with supplement`

---

### Task 10: Runbook, Rollback Procedures & Final Independent Verification

- **Surfaces Created:** `docs/appsheet/HARDENING_SUPPLEMENT_RUNBOOK.md` and `docs/appsheet/HARDENING_SUPPLEMENT_ROLLBACK.md`.
- **Runbook Coverage:**
  1. Operating instructions for reviewing related activities on mobile Lead Detail.
  2. Guidelines for safe mobile note logging and follow-up updates.
  3. Reconciliation of activities between AppSheet and Google Sheets.
- **Rollback Procedure:**
  1. If `ACTIVITIES` schema change causes regression: Revert `logActivity_` wrapper to 5-column fallback without affecting `ALL_LEADS`.
  2. If AppSheet `Activities` Ref causes performance degradation: Remove virtual `[Related Activities]` column; mobile app reverts to standalone lead cards.
  3. `ALL_LEADS` and Apps Script core engine remain 100% operational in all failure modes.
- **Commit Boundary:** `docs(appsheet): add hardening supplement runbook, rollback procedures and review verification`

---

## 4. Superpowers Quality & Self-Review Audit

| Review Dimension | Requirement | Finding | Verdict |
| :--- | :--- | :--- | :--- |
| **Spec Coverage** | All 10 tasks detailed with inputs, pre-conditions, failing checks, implementations, and commit boundaries | Complete coverage across tasks 1–10 | **PASS** |
| **Placeholder Scan** | Zero instances of `TODO`, `TBD`, `similar to`, or ungrounded ellipses | 0 placeholders found | **PASS** |
| **Audit Integrity** | Historical activity data preserved without deletion or invented Lead-IDs | Zero-loss deterministic migration | **PASS** |
| **No Duplicate SSOT** | `ALL_LEADS` remains canonical SSOT; `ACTIVITIES` remains audit log | Zero duplicate database tables | **PASS** |
| **Performance Model** | Uses native AppSheet `Ref` (`REF_ROWS`) instead of full-table `SELECT`/`FILTER` | Low context / low latency | **PASS** |
| **Fail-Closed Security** | Unknown users evaluate to `FALSE` (0 rows) via verified primary identities | Invariant preserved | **PASS** |
| **Zero Prospect Sends** | `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` strictly enforced | Guaranteed | **PASS** |
| **YAGNI Compliance** | No Supabase, no custom PWA, no Canvas, no Looker, no Gemini | Pure native AppSheet + Apps Script | **PASS** |

---

## 5. Plan Execution Handoff

- **Supplement Plan File:** [`docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-hardening-supplement.md`](file:///Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os/docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-hardening-supplement.md)
- **Status:** `PLAN_ONLY = YES` | `IMPLEMENTATION_FORBIDDEN = YES`
- **Ready for Review:** Plan is complete, self-contained, and ready for operator review and execution authorization.
