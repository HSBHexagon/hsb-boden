# Outbound Unsubscribe System (Underlined Link, Styled Button & Web Landing Page) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a prominent, high-contrast, dual-channel unsubscribe mechanism across all outreach emails (featuring a clearly visible underlined link and styled button leading to a dedicated website landing page at `https://www.hsb-boden.de/abmelden`, plus an instant `mailto:` reply option), synchronized across Python engines, Google Apps Script, and the Astro website.

**Architecture:** 
1. **Web Surface:** A dedicated, clean, GDPR-compliant unsubscribe landing page at `apps/website/src/pages/abmelden/index.astro` supporting instant confirmation via `?email=...` query parameter.
2. **Email Template Surface:** A prominent, responsive HTML unsubscribe block integrated into signatures and footers across Python engines (`run_100_batch.py`, `batch_engine.py`) and Google Apps Script (`HSB_DraftAdapter.gs`, `Actions.gs`).
3. **Governance & Sync:** Automated build bundling (`build_single.py`), deployment via clasp, and 100% test coverage with Pytest and Node.js.

**Tech Stack:** Astro, HTML/CSS (email-safe tables and inline styles), Python 3.14, Google Apps Script (JavaScript ES6), Pytest, Node.js.

## Global Constraints
- `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`: No external prospect emails sent during test/build cycles.
- Canonical flyer name remains `HSB-HEXAGON-Industrieboeden-Flyer.pdf` (no personal flyer names).
- All email styling must be 100% email-client safe (inline CSS, table layout, no external stylesheet dependencies, high contrast).
- All existing tests in `test_apps_script.js` (362 tests) and `pytest` (75 tests) must remain 100% green.

---

### Task 1: Dedicated Website Unsubscribe Landing Page
**Files:**
- Create: `apps/website/src/pages/abmelden/index.astro`
- Modify: `apps/website/src/pages/robots.txt.ts` (allow or exclude indexing)

**Interfaces:**
- Consumes: Query parameters `email` and `lead` from outreach email links.
- Produces: Visual confirmation that the email address is unsubscribed from all future HSB outreach.

- [ ] **Step 1: Create Astro Unsubscribe Page**
  Create `apps/website/src/pages/abmelden/index.astro` with clean typography, company branding, and instant confirmation.

- [ ] **Step 2: Verify Astro Build or Preview**
  Verify that the page builds without TypeScript/Astro compilation errors.

---

### Task 2: High-Visibility Unsubscribe Block in Python Signature Engines
**Files:**
- Modify: `apps/sales-os/engine/run_100_batch.py:56-85`
- Modify: `apps/sales-os/engine/batch_engine.py:340-380`
- Modify: `apps/sales-os/engine/run_ultimate_test.py:45-75`
- Modify: `apps/sales-os/tests/test_signatur_abmeldelink.py`

**Interfaces:**
- Consumes: `owner_display`, `mailbox`, `mobile`, `lead_email` (optional), `lead_id` (optional).
- Produces: HTML string containing both a styled button / underlined link to `https://www.hsb-boden.de/abmelden` and a `mailto:` fallback.

- [ ] **Step 1: Update Test Assertions in `test_signatur_abmeldelink.py`**
  Add assertions for the prominent underlined link (`https://www.hsb-boden.de/abmelden`) and button structure.

- [ ] **Step 2: Implement Enhanced Signature in `run_100_batch.py`, `batch_engine.py`, and `run_ultimate_test.py`**
  Replace plain text / faint link with high-contrast, underlined link and styled button.

- [ ] **Step 3: Run Pytest to Verify**
  Ensure all Python tests pass.

---

### Task 3: Unsubscribe Component in Google Apps Script
**Files:**
- Modify: `apps/sales-os/apps_script/HSB_DraftAdapter.gs:147-185`
- Modify: `apps/sales-os/apps_script/Actions.gs:150-165`

**Interfaces:**
- Consumes: `ownerDisplay`, `mailbox`, `mobile`.
- Produces: Synchronized email HTML signature with the new prominent unsubscribe button/link.

- [ ] **Step 1: Update `signaturHtml_` in `HSB_DraftAdapter.gs`**
  Add the web link to `https://www.hsb-boden.de/abmelden` with underlined button styling and mailto fallback.

- [ ] **Step 2: Update Plaintext & HTML Fallback in `Actions.gs`**
  Ensure consistent messaging in `renderEmail_()`.

---

### Task 4: Rebuild Apps Script Bundle & Clasp Push
**Files:**
- Run: `python3 apps/sales-os/engine/build_single.py`
- Copy to: `apps/sales-os/deploy/`
- Push: `cd apps/sales-os/deploy && clasp push --force`

**Interfaces:**
- Consumes: Source `.gs` files.
- Produces: Updated `HSB_SALES_OS.gs` (pushed live to Google Apps Script).

- [ ] **Step 1: Run `build_single.py`**
- [ ] **Step 2: Sync deploy directory**
- [ ] **Step 3: Run `clasp push --force`**

---

### Task 5: End-to-End Verification Across All Test Suites
**Files:**
- Test: `pytest`
- Test: `node apps/sales-os/tests/test_apps_script.js`
- Test: `node apps/sales-os/tests/test_flowconnect.js`

**Interfaces:**
- Consumes: All updated codebases.
- Produces: 100% green test passes with zero regressions.

- [ ] **Step 1: Run Pytest suite**
- [ ] **Step 2: Run Apps Script test suite**
- [ ] **Step 3: Verify sample rendered draft output**
