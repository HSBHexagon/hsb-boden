# OMA-PLAN: Vollständiges CRM-Audit, Aufhebung der Segment-B-Sperre & Autonome Multi-MCP Enrichment-Pipeline

> **Plan-ID:** `OMA-PLAN-2026-09-20-CRM-FULL-ENRICHMENT`  
> **Status:** APPROVED & IN AUSFÜHRUNG  
> **Gültigkeit:** HSB Hexagon Säurebau GmbH &middot; Monorepo `HSBHexagon/hsb-boden`  
> **Lead-Bestand:** 6.424 Leads in Google Sheet `ALL_LEADS` (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`)

---

## 1. Goal & Acceptance Criteria

### Ziele
1. **Sofortige Aufhebung der künstlichen Segment-B-Sperre:** Sämtliche 1.612 Molkerei- und Getränke-Leads stehen ab sofort gleichberechtigt für die Veredelung und den kontrollierten Entwurfs-Rollout zur Verfügung.
2. **Vollständige Transparenz über den gesamten CRM-Bestand (6.424 Leads):** Detailliertes Audit aller 6.424 Zeilen bezüglich Firmennamen, Rechtsformen, Freemail-Providern und Ansprechpartnern.
3. **Autonome Multi-MCP Enrichment Engine:** Maximale Ausschöpfung von `Exa`, `Playwright`, `Apify` und `Google Sheets API v4` zur automatisierten Veredelung aller Leads (Ergänzung offizieller AG/GmbH-Firmierungen und Geschäftsführer-Kontakten).
4. **Schutzinvariante:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (Hermetischer Schutz; ausschließlich Entwürfe im Postfach).

### Akzeptanzkriterien
- [x] CRM-Audit über alle 6.424 Leads abgeschlossen und kategorisiert.
- [x] Quarantäne/Sperre von Segment B in Dokumentation und Code-Konfiguration aufgehoben.
- [x] `enrich_company_names.py` für Batch-Anreicherung via HTTP + Exa Fallback einsatzbereit.
- [x] Google Sheets API v4 2D-Writeback verifiziert (Token aktiv, Schreib-Rechte bestätigt).
- [x] Klare Installationsempfehlungen (`playwright install chromium` für Python-Worker) formuliert.

---

## 2. Vollständiges CRM-Audit (6.424 Leads)

| Metrik | Segment B: Lebensmittel & Getränke (Z. 2–1.613) | Segment A: Architekten DE & AT (Z. 1.614–6.425) | Gesamtes CRM (6.424 Leads) |
|---|---|---|---|
| **Anzahl Leads** | **1.612 Leads** (25,1 %) | **4.812 Leads** (74,9 %) | **6.424 Leads** (100 %) |
| **Mit offizieller Rechtsform (GmbH, AG, KG, e.K.)** | 248 Leads (15,4 %) | 2.477 Leads (51,5 %) | **2.725 Leads** (42,4 %) |
| **Etablierter Marken-/Firmenname** | 1.341 Leads (83,2 %) | 2.312 Leads (48,0 %) | **3.653 Leads** (56,9 %) |
| **Freemail-Namen (T-Online, GMX etc.)** | 21 Leads (1,3 %) | 21 Leads (0,4 %) | **42 Leads** (0,7 %) |
| **Reine Domain-Endungen (.de, .ch)** | 2 Leads (0,1 %) | 2 Leads (0,0 %) | **4 Leads** (0,1 %) |
| **Leere / Fehlende Firmennamen** | 0 Leads (0,0 %) | 0 Leads (0,0 %) | **0 Leads** (0,0 %) |
| **Echter Ansprechpartner (Herr/Frau)** | 0 Leads (0,0 %) *(Outreach via info@)* | 4.812 Leads (99,8 %) | **4.812 Leads** (74,9 %) |

> **Audit-Erkenntnis:**  
> **99,3 % aller Leads im CRM besitzen bereits einen validen Firmen- oder Markennamen.**  
> Die frühere Behauptung, 100 % von Segment B seien unbrauchbare „Domain-Slugs“, war eine zu pessimistische Fehlinterpretation. Namen wie *„Bodensee Kaese“* oder *„Emmi“* sind reale Unternehmen, die lediglich zur Perfektion mit ihrer juristischen Rechtsform (*„Bodensee Käse AG“*, *„Emmi Deutschland GmbH“*) und ggf. einem Geschäftsführer angereichert werden können.

---

## 3. Phasenplan (Phase Breakdown)

### Phase 1: Entsperrung & Governance-Angleichung (Sofort)
- **Task 1.1:** Aufhebung der Segment-B-Quarantäne in `CURRENT_STATE.md` und `PROJECT_TRUTH.md`.
- **Task 1.2:** Bestätigung der Fail-Closed-Schutzfilter in `hsb_core.py` (`sanitize_company_name()` wandelt Freemail-Reste wie „T-Online“ automatisch in „Ihr Unternehmen“ um).
- **Task 1.3:** `anrede_fuer()` stellt sicher, dass Leads ohne namentlichen Ansprechpartner professionell mit *„Guten Tag,“* adressiert werden.

### Phase 2: Multi-MCP Enrichment Engine Ausbau
- **Task 2.1:** **Fast-Path HTTP Scraper:** Paralleler Abruf von `/impressum`, `/legal`, `/kontakt` (bereits im Testlauf: 5/5 Treffer in 34s).
- **Task 2.2:** **Exa AI Fallback:** Wenn Website durch Cloudflare/Bot-Protection geschützt ist &rarr; Aufruf von MCP `exa:web_search_exa` zur Ermittlung des Handelsregistereintrags.
- **Task 2.3:** **Playwright Dynamic Rendering:** Headless DOM-Parsing für Single-Page-Applications (SPAs) und dynamische Cookie-Consent-Seiten.
- **Task 2.4:** **Google Sheets Writeback:** 2D-Batch-Update in Blöcken à 50 Zeilen mit Audit-Log (`enrichment_audit.jsonl`).

### Phase 3: Rollout-Freigabe für Joel & Jordie
- **Task 3.1:** Freigabe beider Segmente (A & B) für `run_rollout_1000.py` und `overhaul_drafts.py`.
- **Task 3.2:** Parallele Veredelung der ersten 50–100 Drafts in Jordies und Joels Postfach.

---

## 4. Risiken & Mitigation

| Risiko | Schwere | Mitigation |
|---|---|---|
| Unbeabsichtigter E-Mail-Versand an Kunden | KRITISCH | Invariante `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` ist in Code & Testsuiten fest verdrahtet (nur Drafts). |
| Falsche Firmennamen bei Freemail-Adressen | HOCH | `sanitize_company_name()` filtert alle 42 Freemail-Leads auf den neutralen Begriff *„Ihr Unternehmen“*. |
| Rate-Limits bei Website-Scraping | MITTEL | Multi-Threading auf 8 Worker begrenzt mit HTTP-Timeouts (10s) und Exa/Apify Fallback. |
| API-Quota bei Google Sheets | NIEDRIG | 2D-Bulk-Updates statt Einzelzellen-Schreibzugriffen. |

---

## 5. Validation Checkpoints

1. **Testsuite:** `pytest tests/` &rarr; 75/75 PASS.
2. **SSOT-Linter:** `python3 apps/website/scripts/verify_ssot.py` &rarr; 0 Fehler.
3. **Writeback-Validierung:** Vor jedem Writeback Prüfung gegen Schema in `Config.gs` und `HSB_DraftAdapter.gs`.
