# 100 Drafts Joel + Jordi mit HSB-Logo und Live-Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Erstellung von jeweils 100 personalisierten Outlook-Entwürfen für Joel Cherino Diaz und Jordi Post (insgesamt 200) mit offiziellem HSB-Logo in der Signatur, PDF-Flyer-Anhang und lückenloser Status-Rückschreibung in Google Sheet & AppSheet.

**Architecture:** 
1. HTML-Signaturerweiterung mit responsivem HSB-Logo (`https://www.hsb-boden.de/brand/hsb-boden-logo.png`, 148x48 px), § 35a GmbHG Angaben und § 7 UWG Opt-out.
2. Robuste Batch-Engine mit Pacing (0.4s Delays) und bytegenauer Anhangverifikation (`HSB-HEXAGON-Industrieboeden-Flyer.pdf`, ~1,53 MB).
3. Direktes Writeback der `Draft_ID`, `Drafted_At` und `Batch_Status = DRAFTED` ins Google Sheet `ALL_LEADS` und Synchronisation mit Apps Script (`clasp push`).

**Tech Stack:** Python 3, Microsoft Power Automate HTTP SAS Trigger (Joel), Azure ApiHub Logic Flow Connector via MSAL Bearer Token (Jordi), Google Apps Script / Clasp, Google Sheets API / XLSX.

## Global Constraints
- `REAL_EXTERNAL_SEND_COUNT = 0`: Ausschließlich Entwurfserstellung in Outlook (`DraftEmail`). Niemals unautorisierter externer Mailversand.
- Empfängersichtbarer Anhangname zwingend `HSB-HEXAGON-Industrieboeden-Flyer.pdf`.
- Vollständige GmbH-Angaben nach § 35a GmbHG (Sitz Gronau, AG Coesfeld HRB 21481, GF Jordi Post) und § 7 UWG Abmeldehinweis.
- Logo-Ausrichtung in Outlook Desktop kompatibel (feste Dimensionen width="148" height="48", display="block", alt-Text).

---

### Task 1: HTML-Signatur mit HSB-Logo aktualisieren

**Files:**
- Modify: `apps_script/HSB_DraftAdapter.gs:144-164`
- Modify: `engine/run_ultimate_test.py:40-58`

**Interfaces:**
- Produces: `signaturHtml_(ownerDisplay, mailbox, mobile)` returning HTML string with logo lockup.

- [ ] **Step 1: Signatur in `apps_script/HSB_DraftAdapter.gs` um Logo-Block erweitern**
- [ ] **Step 2: Signatur in `engine/run_ultimate_test.py` synchronisieren**
- [ ] **Step 3: Syntax und HTML-Rendering validieren**

---

### Task 2: 100+100 Batch-Runner mit Google Sheet Status-Rückschreibung erstellen

**Files:**
- Create: `engine/run_100_batch.py`

**Interfaces:**
- Consumes: `FLYERS` from `hsb_core.py`, XLSX/Sheet data from `sheet_loader.py`.
- Produces: Live Power Automate calls, `run_batch(owner, count=100)` returning execution stats.

- [ ] **Step 1: `engine/run_100_batch.py` auf Basis von `run_ultimate_test.py` für 100 Leads pro Person aufsetzen**
- [ ] **Step 2: Automatisches Sheet-Writeback (oder Status-Export) für `ALL_LEADS` integrieren**
- [ ] **Step 3: Testlauf mit Dry-Run / Preflight ausführen**

---

### Task 3: 100 Entwürfe für Joel Cherino Diaz ausführen

**Files:**
- Execute: `engine/run_100_batch.py JOEL 100`

- [ ] **Step 1: 100 Leads für Joel filtern und verifizieren**
- [ ] **Step 2: Power Automate SAS-Aufrufe mit Flyer und Signatur-Logo absetzen**
- [ ] **Step 3: 100% Erfolgsquote und Draft-IDs verifizieren**

---

### Task 4: 100 Entwürfe für Jordi Post ausführen

**Files:**
- Execute: `engine/run_100_batch.py JORDI 100`

- [ ] **Step 1: Frisches MSAL-Token für Jordi holen**
- [ ] **Step 2: 100 Leads für Jordi filtern und Power Automate Connector-Aufrufe absetzen**
- [ ] **Step 3: 100% Annahmequote (HTTP 202 Succeeded) verifizieren**

---

### Task 5: Apps Script aktualisieren und Live-Deployment sichern

**Files:**
- Modify: `apps_script/HSB_DraftAdapter.gs`
- Deploy: `clasp push --force`

- [ ] **Step 1: Apps Script Code mit Clasp nach Google hochladen**
- [ ] **Step 2: Status-Rückschreibung und Konsistenz im Sheet prüfen**
- [ ] **Step 3: Abschlussbericht und Übergabedokumentation erstellen**
