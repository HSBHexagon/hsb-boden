# CRM Operator-Schicht + Postfach-Automatik — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Das bestehende Sheet `HSB CRM MASTER 6424 – Sales OS` lesbar machen (Sichtbarkeit, Pipeline-Spalte, Filteransichten), Vokabulare härten und Versand/Antwort/Abmeldung/Bounce automatisch aus beiden Outlook-Postfächern fortschreiben.

**Architecture:** Sheets-API-Skripte (idempotent, Dry-Run) für Format und Validierung; Apps-Script-Web-App als einziger Schreiber für Postfachereignisse; Power-Automate-Flows (Trigger V3 mit Ordner) als Ereignisquelle. Kein Header wird geändert, neue Spalten nur am Ende.

**Tech Stack:** Python 3 + google-api-python-client (Tokens des Workspace-MCP, Profil `cherinojoel`), Apps Script (`deploy/HSB_GraphAdapter.js`), Power Automate (FlowAgent MCP).

**Spec:** `docs/superpowers/specs/2026-09-17-crm-sheet-operator-layer-design.md`

## Global Constraints
- Sheet-ID nur aus `apps/sales-os/PROJECT_STATE.md`; keine IDs/Secrets in Git.
- Vor jedem Schreibzugriff: Drive-Kopie + CSV je Tab + SHA-256-Manifest unter `~/KI-System/08_System/backups/<datum>-hsb-crm-sheet/`.
- Header `ALL_LEADS!A1:BD1` bleibt byte-identisch; neue Spalten ab BE.
- Kein automatischer Versand; nie `Versandfreigabe=yes` per Automatik.
- Datenänderungen (Task 4) nur nach Owner-Freigabe je Regel, mit Dry-Run-Ausgabe.

---

### Task 1: Backup mit Manifest
- [x] Drive-Kopie `HSB CRM MASTER 6424 – Sales OS – BACKUP-2026-09-17` (Drive API `files.copy`)
- [x] CSV-Export aller 34 Tabs nach `~/KI-System/08_System/backups/20260917-hsb-crm-sheet/` + `MANIFEST.sha256`
- [x] Verifikation: 34 Dateien, Zeilenzahlen = Analyse (ALL_LEADS 6425)

### Task 2: Sichtbarkeit (`engine/apply_sheet_formatting.py` → Modus `operator-layer`)
- [x] Skript schreiben: CLIP, Gruppe AD:BD (collapsed), S:W hidden, Freeze 1/2, Breiten, Validierungen (nicht strikt), bedingte Formate für Pipeline, Filteransichten ×4
- [x] Dry-Run: Liste der Requests ausgeben, keine Schreibung
- [x] Ausführen; Verifikation per `crm_analyze.py` (wrap=CLIP, group vorhanden, filterViews=4, Header identisch)

### Task 3: Pipeline-Spalte BE
- [x] `BE1="Pipeline"`, `BE2=ARRAYFORMULA(...)` gemäß Spec-Reihenfolge; Farben per bedingter Formatierung
- [x] Verifikation: Verteilung BE über alle Zeilen = Verteilung aus `Send_Status`/`Suppressed`/`Reply_Status` (Neu ≈ 5.730−Entwurf…, Versendet=159, Bounce=20, Abgemeldet=0)

### Task 4: Datenmodell-Reparatur (Owner-Gate)
- [x] Dry-Run: 20 Lead-IDs mit `Legal_Basis=yes`; 20 mit `Reply_Status=bounced` ohne `Bounce_Status`
- [ ] Nach Freigabe: `yes`→`OWNER_APPROVED`; `Bounce_Status=hard`; Dashboard-Formel korrigieren
- [ ] Verifikation: `Legal_Basis` nur noch 4 Werte; Dashboard „Opt-Outs / Bounces" = 20

### Task 5: Apps-Script-Web-App „Inbound"
- [ ] `deploy/HSB_GraphAdapter.js` um `doPost` + `classifyInbound_` + `writebackInbound_` erweitern; Shared-Secret aus Script-Properties
- [ ] Unit-Tests (bestehende Apps-Script-Testsuite, 135 Tests) + neue Tests für Klassifikation/Idempotenz
- [ ] Deployment als Web-App (bestehendes Deployment aktualisieren, keine neue ID); URL nur in Script-Properties/Power Automate, nicht in Git

### Task 6: Power-Automate-Flows (Joel), danach Jordi
- [ ] Flow `HSB Sales OS Inbound – Gesendet (Joel)`: Trigger V3 Ordner SentItems → HTTP POST
- [ ] Flow `HSB Sales OS Inbound – Posteingang (Joel)`: Trigger V3 Ordner Inbox → HTTP POST
- [ ] Rückabgleich-Flow (manuell) ab 2026-09-04 für beide Ordner
- [ ] Jordi: Connection anlegen lassen, Flows duplizieren (Co-Owner)

### Task 7: End-to-End-Verifikation
- [ ] Testfälle 1–3 aus Spec mit eigener Adresse; Vorher/Nachher-Zählungen; `apps/sales-os/tests` grün; Header-Diff leer
- [ ] Doku: `PROJECT_STATE.md`, `README_OPERATING.md` (neue Automatik), `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, Handoff


## Ausführungsnotiz 2026-09-17
- Task 1–3 erledigt und verifiziert (Header A1:BD1 byte-identisch; Pipeline: Neu 3.953 · Entwurf 2.125 · Freigegeben 186 · Versendet 140 · Bounce 20).
- Task 5/6 **vereinfacht**: `processInboundEvent()`, `doPost` und der Graph-Abgleich je Nutzer existierten bereits. Ergänzt: `hsbAutoReconcile()` + zeitgesteuerter Trigger (15 min) + drei Menüpunkte + erweiterte Opt-out-Stichwörter (`deploy/HSB_GraphAdapter.js`, `deploy/HSB_SALES_OS.js`), per `clasp push` live, Remote gegengeprüft. Power-Automate-Flows damit **optional** (Echtzeit-Ausbau), nicht nötig.
- Task 4 offen (Owner-Gate): 20× `Legal_Basis=yes`→`OWNER_APPROVED`; 20× `Bounce_Status=hard`; **neu gefunden:** 224× `Legal_Basis=no` und 99× `UNKNOWN` bei `Versandfreigabe=yes` — Entscheidung nötig, ob die Freigabe dort auf `no` gesetzt wird (VERSAND/READY_CANDIDATES filtern sie bereits aus).
- Task 7 offen: Joel + Jordi richten im Sheet „Mit Outlook verbinden" + „Automatischen Abgleich einrichten" ein; danach Testfälle 1–3.
