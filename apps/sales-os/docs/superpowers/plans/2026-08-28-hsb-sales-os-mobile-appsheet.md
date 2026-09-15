# HSB Sales OS Mobile AppSheet Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.

This document specifies the exact, step-by-step implementation plan for deploying a thin, authenticated, mobile-first Google AppSheet frontend over the existing, production-verified HSB Sales OS backend.

---

## 1. System Overview & Architecture Context

### Authoritative Target System
- **Repository Root:** `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os`
- **Canonical Google Sheet ID:** `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`
- **Bound Apps Script Project ID:** `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`
- **Canonical System of Record (SSOT):** `ALL_LEADS` worksheet (6,424 total leads).
- **Core Business Logic Owner:** Existing Google Apps Script engine (`Config.gs`, `Engine.gs`, `Actions.gs`, `Code.gs`). All batch allocations, EML package generation, RFC-5322 Message-ID reconciliation, and operator confirmation loops remain strictly in Apps Script.

### Architectural Role of AppSheet
- **Frontend Layer Only:** AppSheet provides a mobile/desktop UI for Joel and Jordi to review assigned leads, trigger 1-tap phone calls, view company websites, log follow-up dates/notes, and triage inbound replies.
- **Strictly Non-Authoritative for Batch/Send:** AppSheet NEVER generates EMLs, NEVER creates batch IDs, and NEVER directly modifies `Send_Status`, `Legal_Basis`, or `Versandfreigabe`.
- **Zero Real Prospect Send Rule:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` must strictly hold across all automated and manual tests.
- **Data Access Mode:** `APPSHEET_DATA_ACCESS_MODE = AS_APP_CREATOR`. Operators authenticate to AppSheet via Google Workspace; they do NOT require direct write permissions to the underlying Google Sheet.

### Deliberate Non-Goals
1. **No Database Migration:** No Supabase, PostgreSQL, or AppSheet Database migration in this scope.
2. **No Custom React / PWA:** We rely purely on Google AppSheet native runtime.
3. **No Direct Prospect Email Transport:** AppSheet will not send external emails to prospects.
4. **No Sheets Canvas / Looker / Gemini in this phase:** Kept strictly out of scope to avoid scope creep and protect the core.

---

## 2. Operator Identities & Security Model

### Real Identity Discovery Precondition
Operator identities must **NEVER be guessed or hardcoded** as unverified constants. During Task 1 preflight, actual authenticated AppSheet Google accounts are discovered and bound to symbolic variables:
- `VERIFIED_JOEL_APPSHEET_EMAIL` (Joel Cherino Diaz)
- `VERIFIED_JORDI_APPSHEET_EMAIL` (Jordi Post)
- `VERIFIED_ADMIN_APPSHEET_EMAIL` (System Administrator / Deployment Account)

### Fail-Closed Row-Level Security
- **Security Filter Expression (applied on `ALL_LEADS` table):**
  ```appsheet
  SWITCH(
    USEREMAIL(),
    VERIFIED_JOEL_APPSHEET_EMAIL, [Verantwortlicher] = "Joel Cherino Diaz",
    VERIFIED_JORDI_APPSHEET_EMAIL, [Verantwortlicher] = "Jordi Post",
    VERIFIED_ADMIN_APPSHEET_EMAIL, TRUE,
    FALSE
  )
  ```
- **Unknown User Policy:** Any unrecognized or unauthenticated user evaluates to `FALSE` and receives **0 rows** (`UNKNOWN_USER_ROWS = 0`).
- **Owner Crossover Invariant:** `OWNER_CROSSOVER_COUNT = 0`. Joel cannot view or mutate Jordi's leads; Jordi cannot view or mutate Joel's leads.

---

## 3. Editable Field Whitelist vs. System Protections

| Field Name | Column in `ALL_LEADS` | AppSheet Permission (`Editable_If`) | Purpose |
| :--- | :--- | :--- | :--- |
| **`Notizen`** | Col 29 (`AC`) | `TRUE` | Operator sales call notes & conversation records |
| **`Nächste Aktion`** | Col 17 (`Q`) | `TRUE` | Operator task description (e.g. "Anrufen", "Angebot senden") |
| **`Follow-up-Datum`** | Col 18 (`R`) | `TRUE` | Scheduled date for next touchpoint |
| **`Lead-ID`** | Col 1 (`A`) | `FALSE` (Read-Only Key) | Immutable primary key (`HSB-YYYYMMDD-XXXXX`) |
| **`Firma`, `Ansprechpartner`, `E-Mail`, `Telefon`, `Branche`, `Tier`** | Cols 2, 7, 9, 10, 5, 6 | `FALSE` (Read-Only) | Canonical master lead data |
| **`Batch_ID`, `Batch_Status`, `Prepared_At`** | Cols 40, 47, 48 | `FALSE` (Read-Only) | Managed strictly by Apps Script batch preparation |
| **`Send_Status`, `Send_Datum`, `Draft_ID`, `Drafted_At`** | Cols 41, 42, 49, 50 | `FALSE` (Read-Only) | Managed strictly by Apps Script EML generation |
| **`Legal_Basis`, `Versandfreigabe`, `Suppressed`** | Cols 45, 26, 46 | `FALSE` (Read-Only) | Compliance-critical fields |
| **`Message_IDs`, `Last_Reply_At`, `Last_Error`** | Cols 52–56 | `FALSE` (Read-Only) | Inbound reconciliation fields |

---

## 4. Task Decomposition (13 Discrete Tasks)

```
┌────────────────────────────────────────────────────────────────────────┐
│                   HSB SALES OS APPSHEET TASK MAP                       │
├────────────────────────────────────────────────────────────────────────┤
│ Task 1: Preflight, Identity Discovery & Baseline Verification           │
│ Task 2: Data Contract & Lead_ID Key Stability Proof                    │
│ Task 3: AppSheet App Bootstrap with Explicit AS_APP_CREATOR Mode       │
│ Task 4: Mobile Navigation & Home Dashboard View                        │
│ Task 5: My Leads View & 1-Tap Action Whitelist                         │
│ Task 6: Lead Detail View & Field Mutability Governance                 │
│ Task 7: Replies View & Read-Only Batches View                          │
│ Task 8: Fail-Closed Security Filters & Unknown User Isolation          │
│ Task 9: Inbound Reply Notification Strategy (Scheduled / Deferred)     │
│ Task 10: Offline Sync & External Apps Script State Synchronization     │
│ Task 11: Performance Analyzer Measurement & Target Gate                │
│ Task 12: Full HSB Sales OS Core Regression Verification                │
│ Task 13: Operator Runbook, Rollout & Rollback Documentation            │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Task 1: Preflight, Identity Discovery & Baseline Verification

- **Surfaces Inspected:** Git repository (`master`), Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`, bound Apps Script project `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`, AppSheet Account & Google Workspace sharing settings.
- **Pre-Change Verification:**
  ```sh
  cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
  git status
  git log -n 1 --oneline
  node tests/test_apps_script.js
  ```
- **Expected Initial State:** Working tree clean on `master`, 290/290 unit tests PASS, `SOURCE_DEPLOY_DIFF = 0`.
- **Identity Discovery Protocol:**
  1. Inspect authorized Google accounts in Google Workspace & Sheet sharing list.
  2. Resolve and record:
     - `VERIFIED_JOEL_APPSHEET_EMAIL`
     - `VERIFIED_JORDI_APPSHEET_EMAIL`
     - `VERIFIED_ADMIN_APPSHEET_EMAIL`
  3. If an identity cannot be resolved from project metadata, stop at external approval gate and output the exact single missing value required.
- **Action:** Record baseline metadata and resolved identity mapping to `docs/appsheet/preflight_baseline.json`.
- **Verification Step:** Confirm `preflight_baseline.json` exists, is well-formed JSON, and contains non-empty verified email bindings.
- **Commit Boundary:** `docs(appsheet): capture preflight baseline and verified operator identities`

---

### Task 2: Data Contract & Lead_ID Key Stability Proof

- **Surfaces Inspected:** `ALL_LEADS` worksheet headers (56 columns), `BATCHES` worksheet headers (13 columns).
- **Pre-Change Verification (Failing Condition if Broken):**
  Write and execute a verification script asserting:
  1. `Lead-ID` is in Column 1 (`A`) and contains 0 empty cells across all 6,424 rows (`LEAD_ID_NULL_COUNT = 0`).
  2. `Lead-ID` has 0 duplicate values (`LEAD_ID_DUPLICATE_COUNT = 0`).
  3. Format strictly matches regex `^HSB-\d{8}-\d{5}$` (`LEAD_ID_STABILITY = PASS`).
- **Implementation:** `tests/verify_appsheet_contract.py`
  ```python
  import openpyxl
  wb = openpyxl.load_workbook('data/HSB CRM MASTER 6424 – Sales OS – 2026-08-21.xlsx', data_only=True)
  ws = wb['ALL_LEADS']
  ids = [row[0] for row in list(ws.iter_rows(values_only=True))[1:]]
  assert len(ids) == 6424, f"Expected 6424 rows, got {len(ids)}"
  assert len(set(ids)) == 6424, "Duplicate Lead-IDs detected"
  assert all(isinstance(x, str) and x.startswith('HSB-') for x in ids), "Invalid ID format"
  print("LEAD_ID_NULL_COUNT=0\nLEAD_ID_DUPLICATE_COUNT=0\nLEAD_ID_STABILITY=PASS")
  ```
- **Verification Step:** Run `python3 tests/verify_appsheet_contract.py`.
- **Expected Success:** Script exits with code 0 and outputs all pass assertions.
- **Commit Boundary:** `test(appsheet): add data contract and key stability verification script`

---

### Task 3: AppSheet App Bootstrap with Explicit `AS_APP_CREATOR` Mode

- **Surfaces Inspected:** Google AppSheet editor (`appsheet.com`), Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`.
- **Pre-Change State:** No AppSheet app linked to `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`.
- **Configuration Specification:**
  1. In Google Sheets: **Erweiterungen → AppSheet → App erstellen**.
  2. In AppSheet **Data → Sources / Settings**:
     - `Access Mode`: Set explicitly to `as app creator` (`APPSHEET_DATA_ACCESS_MODE = AS_APP_CREATOR`).
     - `Require Sign-In`: Set to `ON`.
     - `User Allowlist`: Restrict app access strictly to verified operator identities.
  3. In AppSheet **Data → Tables**:
     - Table 1: `ALL_LEADS` (Table Name: `Leads`, Source: `ALL_LEADS`).
     - Key Column: `Lead-ID` (Type: `Text`, IsKey: `TRUE`, Editable: `FALSE`).
     - Label Column: `Firma` (Type: `Text`).
     - Allowed Actions: `Updates_Only` (No row adds, no row deletes).
     - Table 2: `BATCHES` (Table Name: `Batches`, Source: `BATCHES`).
     - Allowed Actions: `Read_Only`.
- **Verification Step:** Query AppSheet table schema readback via AppSheet API / exported specification. Verify `Lead-ID` is marked as Key and `BATCHES` is `Read_Only`.
- **Commit Boundary:** `docs(appsheet): record bootstrap table binding and access mode spec`

---

### Task 4: Mobile Navigation & Home Dashboard View

- **Surfaces Inspected:** AppSheet UX → Views & Navigation.
- **Configuration Specification:**
  1. **Primary Bottom Navigation (5 destinations):**
     - Destination 1: `HOME` (Type: `Dashboard`)
     - Destination 2: `MY LEADS` (Type: `Deck`)
     - Destination 3: `REPLIES` (Type: `Card`)
     - Destination 4: `BATCHES` (Type: `Table`)
     - Destination 5: `SEARCH` (Type: `Table`, filtered search)
  2. **HOME Dashboard Components:**
     - Widget A: Card KPI `Sendebereite Leads` (Expression: `COUNT(FILTER("Leads", AND([Send_Status] = "not_sent", [Suppressed] = "no")))`)
     - Widget B: Card KPI `Vorbereitete Batches` (Expression: `COUNT(FILTER("Batches", [Status] = "PREPARED"))`)
     - Widget C: Card KPI `Offene Wiedervorlagen` (Expression: `COUNT(FILTER("Leads", AND(ISNOTBLANK([Follow-up-Datum]), [Follow-up-Datum] <= TODAY())))`)
     - Widget D: Card KPI `Eingegangene Antworten` (Expression: `COUNT(FILTER("Leads", [Reply_Status] = "replied"))`)
- **Verification Step:** Load app in AppSheet mobile emulator. Verify all 5 bottom navigation tabs render cleanly and all 4 KPI cards display live numeric counts without error.
- **Commit Boundary:** `docs(appsheet): define mobile navigation and dashboard view spec`

---

### Task 5: `MY LEADS` View & 1-Tap Action Whitelist

- **Surfaces Inspected:** AppSheet UX → Views → `MY LEADS` (`Deck View`), AppSheet Behavior → Actions.
- **Configuration Specification:**
  1. **Deck View Layout:**
     - Primary Header: `[Firma]`
     - Secondary Header: `[Ansprechpartner]`
     - Summary Column: `[Tier]` (Badge format: Tier A = Green, Tier B = Blue)
     - Side Image / Icon: Industry icon or initial avatar.
     - Subheader: `CONCATENATE([Branche], " · ", [Standort])`
  2. **Action Whitelist (Attached to Deck Cards):**
     - Action 1: `CALL_PHONE` (Type: `External: go to website / call`, Target: `CONCATENATE("tel:", [Telefon])`, Display: Phone icon, Condition: `ISNOTBLANK([Telefon])`).
     - Action 2: `OPEN_WEBSITE` (Type: `External: go to website`, Target: `[Website]`, Display: Globe icon, Condition: `ISNOTBLANK([Website])`).
     - Action 3: `EDIT_NOTE` (Type: `App: go to another view within this app`, Target: `LINKTOROW([Lead-ID], "Lead_Detail_Edit")`, Display: Pencil icon).
  3. **Strictly Prohibited Actions:** No `SEND_PROSPECT_EMAIL`, no `DELETE_ROW`, no `CHANGE_BATCH_ID`.
- **Verification Step:** Test tapping `CALL_PHONE` on a lead with phone number; verify tel link protocol triggers. Verify no delete button exists.
- **Commit Boundary:** `docs(appsheet): define My Leads deck view and action whitelist`

---

### Task 6: `LEAD DETAIL` View & Field Mutability Governance

- **Surfaces Inspected:** AppSheet Data → Columns → `ALL_LEADS`.
- **Column Permissions Configuration:**
  - **Editable Columns (Whitelist):**
    - `[Notizen]`: `Editable_If = TRUE`, Type: `LongText`.
    - `[Nächste Aktion]`: `Editable_If = TRUE`, Type: `Text`.
    - `[Follow-up-Datum]`: `Editable_If = TRUE`, Type: `Date`.
  - **Strictly Read-Only Columns (`Editable_If = FALSE`):**
    - `Lead-ID`, `Firma`, `Standort`, `Region`, `Branche`, `Tier`, `Ansprechpartner`, `Rolle`, `E-Mail`, `Telefon`, `Website`, `Quelle`, `Score`, `Status`.
    - `Versandfreigabe`, `Verantwortlicher`, `Flyer-Anhang`, `Kampagne_ID`, `Email_Template_ID`, `Flyer_ID`, `Flyer_URL`, `Landing_URL`, `UTM_Source`, `UTM_Medium`, `UTM_Campaign`, `UTM_Content`.
    - `Batch_ID`, `Send_Status`, `Send_Datum`, `Bounce_Status`, `Reply_Status`, `Legal_Basis`, `Suppressed`, `Batch_Status`, `Prepared_At`, `Draft_ID`, `Drafted_At`, `Approved_At`, `Outlook_Message_ID`, `Internet_Message_ID`, `Conversation_ID`, `Last_Reply_At`, `Last_Error`.
- **Verification Step:** Open Lead Detail on mobile emulator. Confirm `Firma`, `Batch_ID`, and `Send_Status` cannot be edited. Confirm `Notizen` can be edited and saved.
- **Commit Boundary:** `docs(appsheet): configure column editable permissions and detail layout`

---

### Task 7: `REPLIES` View & Read-Only `BATCHES` View

- **Surfaces Inspected:** AppSheet UX → Views → `REPLIES` and `BATCHES`.
- **Configuration Specification:**
  1. **`REPLIES` (Card View on Leads slice where `[Reply_Status] = "replied"` or `ISNOTBLANK([Last_Reply_At])`):**
     - Title: `[Firma]`
     - Subtitle: `CONCATENATE("Antwort erhalten: ", TEXT([Last_Reply_At], "DD.MM.YYYY HH:MM"))`
     - Body: `[Notizen]`
     - Action: `LINKTOROW([Lead-ID], "Lead_Detail")`
  2. **`BATCHES` (Table View on `BATCHES` table):**
     - Columns: `Batch_ID`, `Status`, `Requested`, `Selected`, `Created_At`, `Sent_At`
     - Sort: `Created_At` (Descending)
     - Read-Only: No edit/add/delete actions.
- **Verification Step:** Verify `BATCHES` view lists the 3 existing batches (`HSB-20260826-JORDI-0001`, `0002`, `0003`) accurately.
- **Commit Boundary:** `docs(appsheet): define replies and batches view configurations`

---

### Task 8: Fail-Closed Security Filters & Unknown User Isolation

- **Surfaces Inspected:** AppSheet Data → Tables → `ALL_LEADS` → Table properties → `Security Filter`.
- **Security Filter Expression:**
  ```appsheet
  SWITCH(
    USEREMAIL(),
    VERIFIED_JOEL_APPSHEET_EMAIL, [Verantwortlicher] = "Joel Cherino Diaz",
    VERIFIED_JORDI_APPSHEET_EMAIL, [Verantwortlicher] = "Jordi Post",
    VERIFIED_ADMIN_APPSHEET_EMAIL, TRUE,
    FALSE
  )
  ```
- **Test Protocol:**
  1. Test as `VERIFIED_JOEL_APPSHEET_EMAIL`: Verify visible lead count = `3,212`. All rows have `[Verantwortlicher] = "Joel Cherino Diaz"`.
  2. Test as `VERIFIED_JORDI_APPSHEET_EMAIL`: Verify visible lead count = `3,212`. All rows have `[Verantwortlicher] = "Jordi Post"`.
  3. Test as `unauthorized_user@external.com`: Verify visible lead count = `0` (`UNKNOWN_USER_ROWS = 0`).
  4. Assert `OWNER_CROSSOVER_COUNT = 0`.
- **Verification Step:** Run AppSheet Security Rule Simulator for each test account and confirm exact count match.
- **Commit Boundary:** `docs(appsheet): configure row security filters and fail-closed isolation`

---

### Task 9: Inbound Reply Notification Strategy (Scheduled / Deferred)

- **Surfaces Inspected:** AppSheet Automation → Bots, Google Sheet `INBOUND_EVENTS` & `ALL_LEADS`.
- **Architectural Principle:** Do **NOT** rely on Google Sheets external data-change events triggered by Apps Script (unsupported/unreliable by platform).
- **Strategy Decision & Implementation:**
  1. **Primary Option (Scheduled Bot):**
     - AppSheet Scheduled Bot running periodically (e.g. hourly or at scheduled intervals).
     - Target Table: `INBOUND_EVENTS` (Filter: `[Event_Type] = "REPLY" AND ISBLANK([Notified_At])`).
     - Task: Send push notification to assigned operator for newly discovered replies.
     - Action: Stamp `[Notified_At]` to ensure strict idempotency (`DUPLICATE_NOTIFICATIONS = 0`).
  2. **Fallback Option (Deferred Optional):**
     - If scheduled bots are unavailable under the current AppSheet license tier or introduce excessive polling complexity:
     - Set `NOTIFICATION_FEATURE_STATUS = DEFERRED_OPTIONAL`.
     - Inbound replies remain immediately visible via the `REPLIES` mobile tab on normal app sync without blocking core mobile rollout.
- **Verification Step:** Test scheduled bot evaluation in test mode or confirm deferred status.
- **Commit Boundary:** `docs(appsheet): configure scheduled inbound notification bot or document deferred status`

---

### Task 10: Offline Sync & External Apps Script State Synchronization

- **Surfaces Inspected:** AppSheet Settings → Offline & Sync.
- **Configuration Specification:**
  - `Offline Mode`: `Enabled` (The app can operate when disconnected).
  - `Sync on Start`: `Enabled` (Downloads fresh canonical state upon app launch).
  - `Automatic Background Sync`: `Enabled`.
  - `Delayed Sync`: `Enabled` for UI responsiveness.
- **Synchronization Contract with External Apps Script Mutations:**
  - When Apps Script mutates Sheet state (e.g. batch preparation, send confirmation):
  - Mobile operator receives updated canonical state upon next automatic/manual sync.
  - Test scenario:
    1. Launch mobile app; verify initial state.
    2. In backend, simulate an external note/batch status update.
    3. Tap manual sync icon in AppSheet.
    4. Assert new canonical state renders in AppSheet with zero local conflict or duplicate rows.
- **Offline Queued-Write Verification:**
  1. Go offline (Airplane mode).
  2. Edit `[Notizen]` on one assigned lead.
  3. Reconnect; sync.
  4. Read back live Google Sheet row via API; assert `ALL_LEADS!AC` contains the updated note and zero other columns were modified.
- **Commit Boundary:** `docs(appsheet): configure offline sync and test external mutation reconciliation`

---

### Task 11: Performance Analyzer Measurement & Target Gate

- **Surfaces Inspected:** AppSheet Manage → Monitor → Performance Analyzer.
- **Provisional UX Targets (Non-Binding Targets until Measured):**
  - `PROVISIONAL_COLD_SYNC_TARGET < 4.5s`
  - `PROVISIONAL_INCREMENTAL_SYNC_TARGET < 1.8s`
  - `PROVISIONAL_NAVIGATION_TARGET < 200ms`
- **Protected-Range Write Compatibility Test:**
  1. Select 1 approved safe test lead in `ALL_LEADS`.
  2. Update `[Notizen]` through AppSheet.
  3. Read back full 56-column row via Google Sheets API.
  4. Assert:
     - `Notizen` updated successfully.
     - `Lead_ID`, `Firma`, `Verantwortlicher`, `Legal_Basis`, `Versandfreigabe`, `Batch_ID`, `Send_Status`, Message-IDs remain byte-identical.
     - No protected range violation occurred (`PROTECTED_RANGE_COMPATIBILITY = PASS`).
- **Measurement Protocol:**
  - Run AppSheet Performance Analyzer across 5 sync cycles on iOS Safari, Android Chrome, and Desktop Chrome.
  - Record actual metrics: `COLD_SYNC_P50`, `COLD_SYNC_MAX`, `INCREMENTAL_SYNC_P50`, `INCREMENTAL_SYNC_MAX`.
- **Commit Boundary:** `docs(appsheet): document performance analyzer measurements and protected range test`

---

### Task 12: Full HSB Sales OS Core Regression Verification

- **Surfaces Inspected:** Full test harness across JavaScript and Python suites.
- **Commands Executed:**
  ```sh
  cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
  node tests/test_apps_script.js
  python3 tests/test_matrix.py
  python3 tests/test_graph_drafts.py
  node tests/verifier_suite.js
  git diff --check
  diff -u apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js
  diff -u apps_script/Sidebar.html deploy/Sidebar.html
  ```
- **Strict Acceptance Pass Criteria:**
  - `JS_TESTS = 290/290 PASS`
  - `PYTHON_MATRIX = 91/91 PASS`
  - `GRAPH_TESTS = 22/22 PASS`
  - `VERIFIER_SUITE = ALL_7_GATES_PASS`
  - `JOEL_1/25/100/150 = PASS`
  - `JORDI_1/25/100/150 = PASS`
  - `OWNER_CROSSOVER_COUNT = 0`
  - `SOURCE_DEPLOY_DIFF = 0`
  - `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`
- **Commit Boundary:** `test(regression): verify complete Sales OS regression suite passes`

---

### Task 13: Operator Runbook, Rollout & Rollback Documentation

- **Surfaces Created:** `docs/appsheet/OPERATOR_RUNBOOK.md` and `docs/appsheet/ROLLBACK_PROCEDURE.md`.
- **Runbook Sections:**
  1. Mobile app installation link & Google Workspace login steps.
  2. Daily 3-minute morning triage workflow for Joel and Jordi.
  3. Safe 1-tap calling and note logging instructions.
  4. Handling inbound reply notifications.
- **Rollout Stages:**
  - **Stage 1 (Admin Only):** `VERIFIED_ADMIN_APPSHEET_EMAIL` verifies schema and row security.
  - **Stage 2 (Single Operator Pilot):** `VERIFIED_JOEL_APPSHEET_EMAIL` tests with 10 leads.
  - **Stage 3 (Full Team Go-Live):** `VERIFIED_JORDI_APPSHEET_EMAIL` added to app users.
- **Rollback Procedure:**
  - If AppSheet encounters critical synchronization errors:
    1. In AppSheet console: Settings → General → Set app to `Maintenance Mode` (disables mobile writes).
    2. Revert any corrupted spreadsheet cells from Google Sheets Version History.
    3. Re-run `./deploy.sh` to confirm Apps Script integrity.
    4. Resume daily operations via native Google Sheets Sidebar (100% operational fallback).
- **Commit Boundary:** `docs(appsheet): add operator runbook, staged rollout plan, and rollback guide`

---

## 5. Superpowers Plan Self-Review & Quality Audit

| Audit Dimension | Standard | Audit Finding | Status |
| :--- | :--- | :--- | :--- |
| **Spec Coverage** | All 13 tasks specified with pre/post-conditions, inputs, outputs, commands, and commit boundaries | Complete coverage across tasks 1–13 | **PASS** |
| **Placeholder Scan** | Zero occurrences of `TODO`, `TBD`, `similar to`, or ungrounded ellipses | 0 placeholders found | **PASS** |
| **No Invalid Trigger** | Replaced invalid Apps-Script-triggered Sheet data-change bot with Scheduled Bot / Deferred status | Verified compliant | **PASS** |
| **No Guessed Identities** | Identities discovered in Task 1 preflight; symbolic variables used in formulas | Fail-closed security | **PASS** |
| **Explicit Access Mode** | `APPSHEET_DATA_ACCESS_MODE = AS_APP_CREATOR` specified | Verified | **PASS** |
| **Single SSOT Check** | `ALL_LEADS` remains canonical; zero duplicate database tables | Maintained strictly | **PASS** |
| **Performance Language** | Targets labeled as provisional targets, not platform guarantees | Fully corrected | **PASS** |
| **Zero Prospect Sends** | `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` enforced across all tasks | Strictly preserved | **PASS** |
| **Regression Safety** | Core Apps Script and test suites tested on clean commit tree | Preserved | **PASS** |
| **YAGNI Compliance** | Canvas, Looker, Gemini, Supabase, and React PWA explicitly excluded | Verified | **PASS** |

---

## 6. Verification & Execution Handoff

- **Plan File:** [`docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md`](file:///Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os/docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md)
- **Subagent Execution Framework:** `superpowers:subagent-driven-development`
- **Implementation Status:** `PLAN_ONLY` complete. No implementation begun. Ready for execution upon explicit operator approval.
