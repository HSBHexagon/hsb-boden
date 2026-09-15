---
plan_id: 2026-08-27-hsb-sales-os-final-closure
title: HSB Sales OS — Final Implementation Plan & True Closure
status: approved
orchestrator: oma-director
execution_framework: superpowers:subagent-driven-development
quality_mode: RALPH
reasoning_effort: xhigh
---

# HSB Sales OS — Final Implementation Plan & True Closure

**Goal:** Ensure Joel and Jordi can reliably open HSB Sales OS, select owner, request 1/25/100/150 contacts, prepare batches, automatically generate EML draft ZIP packages in bounded sequential chunks, recover cleanly from mid-stream failures/reloads without duplicates, approve and confirm batches, and reconcile post-send status with `REAL_EXTERNAL_PROSPECT_SEND_COUNT=0`.

**Execution Methodology:** `superpowers:subagent-driven-development` with sequential serialization for shared state and whole-branch independent review.

**Architecture Principles:**
- `REUSE_BEFORE_REWRITE = YES`
- `YAGNI = YES`
- `DRY = YES`
- `FAIL_CLOSED = YES`
- `ONE_CANONICAL_IMPLEMENTATION_PER_CAPABILITY = YES`
- `NO_SPECULATIVE_REFACTOR = YES`

---

## 1. Subsystem Specifications & Interface Contracts

### 1.1 Apps Script Core & Actions (`apps_script/Actions.gs`, `apps_script/HSB_SALES_OS.gs`)
- **`exportBatchAsEmlZip(batchId, startIndex)`**:
  - *Input:* `batchId: string`, `startIndex: number`
  - *Behavior:* Obtains `LockService.getDocumentLock().tryLock(30000)`. Filters leads for `batchId`. Reads slice `[startIndex : startIndex + 10]`. Deterministically names ZIP as `${batchId}_teil${partNumber}.zip`. Reuses existing Drive file if present. Creates RFC-822 EML blobs with Base64 attachment of verified flyer master.
  - *Output:* `{ batch_id, total, written, part_index, part_total, complete, next_index, parts: [{name, url, count, size_mb}], folder_url, asset_sha256 }`
- **`confirmBatchSent(batchId, startIndex)`**:
  - *Input:* `batchId: string`, `startIndex: number`
  - *Behavior:* Reads leads for `batchId` in chunks of 20 (`CONFIRM_CHUNK_SIZE`). Delegates each lead to `processInboundEvent({ event_id: 'OPCONFIRM-' + id + '-' + lead.Lead_ID, event_type: 'SENT', lead_id: lead.Lead_ID })`.
  - *Output:* `{ batch_id, total, verarbeitet, neu_bestaetigt, bereits_gesendet, complete, next_index }`
- **`processInboundEvent(event)`**:
  - *Input:* `event: { event_id, event_type: 'SENT'|'REPLY'|'BOUNCE'|'OPT_OUT', lead_id?, message_id?, inReplyTo?, email?, owner? }`
  - *Behavior:* For `event_type === 'SENT'`, strictly correlates via explicit `lead_id` or `Internet_Message_ID`. Unstable IDs (`Outlook_Message_ID`, `Draft_ID`, or email alone) go fail-closed to `NEEDS_REVIEW`. Duplicate signals for already-sent leads return `ALREADY_SENT_IGNORED` without extra activity log rows. Stamps `Sent_At` on batch row via `stampBatchSentAt_`.

### 1.2 Sidebar UI Contract (`apps_script/Sidebar.html`)
- **`emlExport(batchId, startIndex)`**:
  - *Client State:* `exportLaufend[batchId]`, `exportPakete[batchId]`, `exportFortschritt[batchId]`
  - *Behavior:* Sets `exportLaufend = true`. Calls `google.script.run.withSuccessHandler(...).withFailureHandler(...).uiExportEml(batchId, von)`. On success, if `!d.complete`, automatically triggers `emlExport(batchId, d.next_index)`. On failure, releases lock and displays a retry button resuming at `von`.
- **`versandBestaetigen(batchId, startIndex)`**:
  - *Behavior:* Sequential confirmation loop calling `uiConfirmBatchSent(batchId, von)`. Updates progress UI and refreshes batch list on completion.
- **Failure Handlers:** All 12 RPC invocations (`uiGetSetupState`, `uiEnsureColumns`, `uiQualify`, `uiPrepareBatch`, `uiGetBatches`, `uiApproveBatch`, `uiGetDue`, `uiSetStatus`, `uiSearch`, `uiConfirmBatchSent`, `uiExportEml`, `uiJordi100`) have active `.withFailureHandler(...)`.

### 1.3 Graph Delegated Draft Tool (`engine/graph_drafts.py`)
- **OAuth 2.0 Device Code Authorization:** Uses `urn:ietf:params:oauth:grant-type:device_code` with scope `https://graph.microsoft.com/Mail.ReadWrite offline_access`.
- **Token Cache:** `~/.hsb_graph_token_cache.json` (chmod 0600) for silent refresh.
- **Draft Creation:** POST `/me/messages` with MIME payload. Validates `/me` mailbox matches expected owner via `identitaet_pruefen()`.

---

## 2. Step-by-Step Task Breakdown & TDD Verification

### Task 1: Verify Core Apps Script Unit & Regression Suite
- **Files:** `apps_script/Actions.gs`, `apps_script/Code.gs`, `apps_script/Sidebar.html`, `apps_script/HSB_SALES_OS.gs`, `tests/test_apps_script.js`
- **Interface:** `test_apps_script.js` running 290 automated checks
- **Command:** `node tests/test_apps_script.js`
- **Expected Output (GREEN):** `ERGEBNIS: 290 bestanden, 0 fehlgeschlagen von 290` | `REAL_EXTERNAL_SEND_COUNT=0`

### Task 2: Verify Python Engine & Matrix Suite
- **Files:** `engine/hsb_core.py`, `engine/sheet_loader.py`, `engine/graph_drafts.py`, `tests/test_matrix.py`, `tests/test_graph_drafts.py`
- **Commands:**
  1. `python3 tests/test_matrix.py`
  2. `python3 tests/test_graph_drafts.py`
- **Expected Output (GREEN):**
  - `ERGEBNIS: 91 bestanden, 0 fehlgeschlagen von 91`
  - `ERGEBNIS: 22 bestanden, 0 fehlgeschlagen von 22`

### Task 3: Operator Journey Proofs (JOEL & JORDI N=1, 25, 100, 150) & Verifier Suite
- **Files:** `tests/verifier_suite.js`, `tests/test_apps_script.js`
- **Command:** `node tests/verifier_suite.js`
- **Operator Matrix Assertions:**
  - JORDI N=1: PASS
  - JORDI N=17: PASS
  - JORDI N=25: PASS
  - JORDI N=100: PASS
  - JORDI N=150: PASS
  - JOEL N=1: PASS
  - JOEL N=17: PASS
  - JOEL N=25: PASS
  - JOEL N=100: PASS
  - JOEL N=150: PASS
- **Multi-Gate Invariants:**
  - Gate 4 Concurrency: OVERLAPPING_LEAD_IDS = 0, Lock timeout fail-closed
  - Gate 5 Idempotency: Zero duplicate batch rows, zero duplicate drafts, zero duplicate activities
  - Gate 6 Inbound: Reply/Bounce/Opt-out processed, unknown events fail-closed to NEEDS_REVIEW
  - Gate 7 Asset Gate: Byte SHA-256 validation for Jordi (`e0aa76c1...`) and Joel (`2bccadac...`)
  - Safety Invariant: `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`

### Task 4: Source ↔ Deploy Synchronization
- **Files:** `engine/build_single.py`, `apps_script/HSB_SALES_OS.gs`, `deploy/HSB_SALES_OS.js`, `deploy/Sidebar.html`
- **Action:** Rebuild canonical bundle and copy to deploy directory:
  1. `python3 engine/build_single.py`
  2. `cp apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js`
  3. `cp apps_script/Sidebar.html deploy/Sidebar.html`
  4. Prove `SOURCE_DEPLOY_DIFF=0` across all production files.

### Task 5: Documentation & Release State Finalization
- **Files:** `PROJECT_STATE.md`, `README_OPERATING.md`
- **Action:** Record the exact verified operating state, deployment prerequisites, and reconciliation status.

---

## 3. Commit Boundaries & Operational Release Strategy
1. **Commit 1:** `fix(hsb-sales-os): EML sequential chunking, failure handlers, and post-send reconciliation`
   - Scope: `apps_script/*`, `tests/test_apps_script.js`, `engine/graph_drafts.py`, `tests/test_graph_drafts.py`
2. **Commit 2:** `build(hsb-sales-os): synchronize deploy bundle and update verification documentation`
   - Scope: `deploy/*`, `PROJECT_STATE.md`, `README_OPERATING.md`, `.gitignore`
3. **Deployment Step (Controlled Operator Gate):**
   - Execute `./deploy.sh` with authenticated clasp credentials (`cherinodiaz@outlook.com`).
