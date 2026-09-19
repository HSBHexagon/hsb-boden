# Lead Data Quality & Company Name Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vollständige Beseitigung aller fehlerhaften Domain-Slugs und Freemail-Artefakte im 6.424-Lead-Datensatz (`ALL_LEADS`) durch automatisierte Anreicherung (Impressum-Scraper & API) und saubere Segment-Trennung (Pristine vs. Quarantäne).

**Architecture:** Zweistufige Architektur: (1) Sofortige Umleitung des operativen Rollouts auf das zu 99,8% saubere Architekten-Segment (4.824 Leads mit echten Namen & Firmen); (2) Asynchroner Batch-Enrichment-Worker für das unqualifizierte Lebensmittel-/Getränke-Segment (1.600 Leads) mit Impressum-Extraktion und Google-Sheet-Writeback.

**Tech Stack:** Python 3.14, Beautiful Soup / Playwright / HTTP-Scraper, Google Sheets API v4, Pydantic / dataclasses.

## Global Constraints
- `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`: Kein externer E-Mail-Versand.
- Unberührtheit versendeter Zeilen (`Send_Status = sent`).
- Kein ungeprüfter Domain-Name darf jemals als `Firma` in Entwürfe fließen (`sanitize_company_name()` bleibt als technisches Gate fail-closed aktiv).

---

## 1. Daten-Audit: Der fundamentale Unterschied der beiden Segmente

Eine tiefgehende Prüfung aller 6.424 Zeilen im Google Sheet `ALL_LEADS` hat die exakte Ursache für schlechte Entwürfe („Industrieböden für T-Online“, „für Ch“, „für Waters“) offengelegt:

| Merkmal | Segment B: Lebensmittel & Getränke (Zeilen 2–1601) | Segment A: Architekten DE & AT (Zeilen 1602–6425) |
|---|---|---|
| **Anzahl Leads** | **1.600 Leads** (24,9% des Bestands) | **4.824 Leads** (75,1% des Bestands) |
| **Quelle** | Gescrapte Listen (Molkerei CH, Getränke DE/CH) | Handelsregister / Architektenkammern |
| **Echter Ansprechpartner** | **0 von 1.600 (0,0 %)** | **4.812 von 4.824 (99,8 %)** (z. B. „Herr Jürgen Willen“) |
| **Firmennamen-Qualität** | **100 % Domain-Slugs** (`Bodensee Kaese`, `Ch`, `Waters`, `Gmx`, `Aol`) | **99,8 % Offizielle Firmen** (z. B. `Willen Associates GmbH`) |
| **Status im Rollout** | **Sofortige Quarantäne / Enrichment nötig** | **Produktionsreif & hochqualitativ** |

---

## 2. Aufgaben-Aufschlüsselung (Bite-Sized Tasks)

### Task 1: Operative Sofort-Maßnahme – Rollout-Partitionierung absichern
**Files:**
- Modify: `apps/sales-os/engine/run_rollout_1000.py`

**Interfaces:**
- Consumes: Google Sheet `ALL_LEADS` Zeilen 1602+ (Architekten)
- Produces: 1.000 sichere, echt personalisierte Entwürfe mit realen Firmen und Ansprechpartnern

- [ ] **Step 1: Partition für Joel auf das saubere Architekten-Segment umstellen**
  Statt Zeilen 1152–1651 (die noch im fehlerhaften Getränke-Segment liegen) wird Joel auf **Zeilen 1652 bis 2151** umgestellt.
  Jordie verarbeitet **Zeilen 4534 bis 5033** (ebenfalls im sauberen Architekten-Segment).
- [ ] **Step 2: Dry-Run Validierung ausführen**
  Prüfen, dass 100% der ausgewählten 1.000 Leads einen echten Ansprechpartner (`Herr/Frau`) und eine echte Rechtsform (`GmbH`, `PartG`, etc.) besitzen.

---

### Task 2: Entwicklung des Impressum- & Firmen-Enrichment-Engines
**Files:**
- Create: `apps/sales-os/engine/enrich_company_names.py`
- Test: `apps/sales-os/tests/test_enrich_company_names.py`

**Interfaces:**
- Consumes: Lead-Dicts aus `high_volume_matrix_engine.py` (Zeilen 2–1601)
- Produces: Bereinigte Firmennamen + extrahierte Geschäftsführer/Inhaber aus Website-Impressum

- [ ] **Step 1: Test für Impressums-Extraktion schreiben**
  Unit-Test mit typischen Impressums-HTML-Mustern (z. B. `Angaben gemäß § 5 TMG`, `Handelsregister: HRB ...`, `Geschäftsführer: ...`).
- [ ] **Step 2: Scraper-Engine implementieren**
  Ermittelt über die Website-Domain (oder MX-Domain) die Impressums-URL (`/impressum`, `/legal`, `/contact`), parst den juristischen Firmennamen und den Geschäftsführer.
- [ ] **Step 3: Confidence-Scoring integrieren**
  - Score >= 90%: Offizieller HRB-/Handelsregister-Name gefunden &rarr; automatischer Writeback.
  - Score < 90%: Markierung als `NEEDS_MANUAL_REVIEW`.

---

### Task 3: 2D-Bulk-Writeback der angereicherten Firmendaten
**Files:**
- Modify: `apps/sales-os/engine/enrich_company_names.py`

**Interfaces:**
- Consumes: Enriched Firmennamen
- Produces: Google Sheet `ALL_LEADS` Update Spalte B (`Firma`) & Spalte G (`Ansprechpartner`)

- [ ] **Step 1: Batch-Writeback für die 1.600 Leads ausführen**
  Schreibt in 50er-Blöcken die validierten Firmennamen und Ansprechpartner zurück.
- [ ] **Step 2: Freemail-Leads isolieren**
  Die 63 Freemail-Leads erhalten ein explizites Review-Flag und werden nicht automatisch angeschrieben.

---

### Task 4: Company-Quality-Gate in den Batch-Runner integrieren
**Files:**
- Modify: `apps/sales-os/engine/hsb_core.py`
- Modify: `apps/sales-os/engine/run_100_batch.py`

**Interfaces:**
- Consumes: `lead["Company"]`
- Produces: `EligibilityResult(eligible=False, reasons=["DOMAIN_SLUG_DETECTED"])`

- [ ] **Step 1: Gate-Regel in `check_eligibility()` schärfen**
  Ein Lead wird blockiert (`eligible=False`), wenn `Company` kürzer als 3 Zeichen ist, einer Freemail-Domain gleicht oder mit der E-Mail-Domain identisch ist.
- [ ] **Step 2: Test-Suite ausführen**
  Sicherstellen, dass alle Tests grün bleiben.
