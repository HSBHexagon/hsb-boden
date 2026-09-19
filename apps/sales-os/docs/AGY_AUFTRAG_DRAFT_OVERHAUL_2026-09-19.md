# AGY-Auftrag: HSB Sales OS — Entwurfs-Veredelung (Pilot 50), Inbound-Worker & Autonomes Ökosystem

**Datum:** 2026-09-19  
**Rolle:** Team Director (`oma-director`)  
**Modus:** `ultrawork` &middot; **Qualitätsstandard:** Ralph-Orchestrierung mit verpflichtenden Freigabe-Gates  
**Mandant:** HSB Hexagon Säurebau GmbH  
**System of Record (SSOT):** Google Sheet CRM `ALL_LEADS` (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`)  
**Harte Sicherheitsinvariante:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (Strikte Entwurfs-Governance, kein externer Versand ohne menschliche Freigabe)

---

## 1. Startbefehl (Neues Terminal-Fenster via osascript)

```bash
osascript -e 'tell application "Terminal" to do script "cd /Users/joelcherinodiaz/Projekte/hsb-boden && agy --dangerously-skip-permissions --agent oma-director --effort high -i \"/oma:mode ultrawork\nLies apps/sales-os/docs/AGY_AUFTRAG_DRAFT_OVERHAUL_2026-09-19.md und führe die Entwurfs-Veredelung und Inbound-Automatisierung autonom aus.\""'
```

---

## 2. Unverrückbare Bedingungen & Invarianten (Hard Guardrails)

1. **`REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`:**  
   Es werden ausschließlich Entwürfe im Postfach erzeugt (`DraftEmail`). Es darf unter keinen Umständen ein unautorisierter Versand (`SendEmailV2`, `Mail.Send`, etc.) an externe Kontakte stattfinden.
2. **CRM `ALL_LEADS` ist die einzige Wahrheit (SSOT):**  
   Alle Änderungen (Firmennamen, Ansprechpartner, Draft-IDs, Bounces, Opt-outs) werden atomar über das Profil `cherinodiaz` in das Google Sheet zurückgeschrieben.
3. **Kanonische Signatur & Assets:**  
   - Logo: 102x75 bicubic Rendering (`https://www.hsb-boden.de/brand/hsb-boden-logo.png`)
   - Prominente Abmeldetabelle mit `<u>Hier abmelden</u>` verlinkt auf `https://www.hsb-boden.de/abmelden`
   - §35a GmbHG Pflichtangaben
   - Kanonischer Vektor-Flyer: `HSB-HEXAGON-Industrieboeden-Flyer.pdf` (246.960 Bytes, SHA-256: `6ac5ed1112c88768ac56950faab8802ceaa2817913f35a7b95e73ee79c3431d8`)
4. **Keine Massenlöschung von Kundenentwürfen:**  
   Die echten Lead-Entwürfe in Joels Postfach werden tranchenweise in-place überarbeitet, nicht blind gelöscht.

---

## 3. Ausgangslage & Bereits vollzogene Schritte

- **Branch:** `feat/b2b-copy-purge` (PR #405 auf GitHub geöffnet).
- **Bereits gelöscht:** 4 Entwicklungs-Dummys (`test@example.com`, 3x Knopftest) wurden per APIHub `DELETE` aus Joels Postfach entfernt.
- **Bereitstehende Werkzeuge:**
  - `apps/sales-os/engine/ingest_bounces.py`: Inbound Bounce/NDR Ingestion Engine
  - `apps/sales-os/engine/ingest_optouts.py`: Inbound NLP/Regex Opt-Out Ingestion Engine
  - `apps/sales-os/engine/enrich_company_names.py`: Pre-Send DNS/MX-Prüfung & Impressums-Scraper mit Host/Bank/Parking-Blacklist
  - `apps/sales-os/engine/overhaul_drafts.py`: In-Place Draft Overhaul Runner

---

## 4. Konkreter Ausführungsauftrag an oma-director

1. **Phase 1: Inbound-Worker Initialisierung & Sync:**
   - Führe `python3 apps/sales-os/engine/ingest_bounces.py --owner ALL --limit 100 --apply` aus.
   - Führe `python3 apps/sales-os/engine/ingest_optouts.py --owner ALL --limit 100 --apply` aus.
   - Verifiziere den Status in `ALL_LEADS` und `INBOUND_EVENTS`.

2. **Phase 2: Pilot-Veredelung der ersten 50 Entwürfe in Joels Postfach:**
   - Führe `python3 apps/sales-os/engine/overhaul_drafts.py --limit 50 --apply` aus.
   - Ersetzt die veralteten Entwürfe schrittweise (400 ms Pacing) durch veredelte Entwürfe:
     - Offizieller Firmenname (z. B. `Napf-Chäsi AG`, `Molkerei Biedermann`, `InterCheese AG`)
     - Nischenspezifische AGI S 40 Copy
     - Prominentes Abmeldesystem & Logo
     - Kanonischer neutraler 241 KB Flyer
   - Synchronisiere neue `Draft_ID`, `Drafted_At`, `Internet_Message_ID` in `ALL_LEADS`.

3. **Phase 3: Ralph Quality Gates & Abschlussprüfung:**
   - Führe `pytest apps/sales-os/tests/` (75/75 PASS erwartet) aus.
   - Führe `node apps/sales-os/tests/test_apps_script.js` (362/362 PASS erwartet) aus.
   - Führe `node apps/sales-os/tests/test_flowconnect.js` (30/30 PASS erwartet) aus.
   - Dokumentiere das Ergebnis und lege den visuellen Prüfbericht für Joel vor.
