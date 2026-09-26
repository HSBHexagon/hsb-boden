# HSB Sales OS - Production Closure & 100-Draft Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vollständige produktive Bereitstellung von je 100 hochwertigen 2026-Standard Akquise-Entwürfen für Joel Cherino Diaz (`j-cherino@hsb-boden.com`) und Jordie Post (`j-post@hsb-boden.com`), atomarer Abgleich mit dem Google Sheet `ALL_LEADS`, technische Cloudflare-Domain-Bewertung und plattformübergreifende Synchronisation für alle KI-Modelle.

**Architecture:** Python 3.14 Engine (`run_com_batch.py`, `com_mailbox_manager.py`, `canonical_template_factory.py`) mit nativer KASServer IMAP-SSL Injektion in `Entw&APw-rfe`, 2D-Matrix Bulk Writeback ins Google Sheet `ALL_LEADS` und plattformübergreifender Dokumentation.

**Tech Stack:** Python 3.14, IMAP-SSL (993), SMTP-SSL (465), Google Sheets API v4, Git, GitHub Actions.

## Global Constraints

- Absender ist zwingend `j-cherino@hsb-boden.com` (Joel) bzw. `j-post@hsb-boden.com` (Jordie Post).
- Geschäftsführer (§ 35a GmbHG) in Signatur und Impressum ist ausnahmslos `Jordie Post` (mit "-ie").
- Empfänger-E-Mail-Adressen werden **niemals** auf `.com` verändert (nur Original-Adressen).
- Antwort-Routing via `Reply-To: .de` leitet Kundenantworten direkt in das Microsoft 365 Exchange Postfach.
- Kanonischer Flyer (241 KB, SHA-256 verifiziert) wird an jeden Entwurf angehängt.
- Im Google Sheet `ALL_LEADS` werden Spalten `Drafted_At`, `Batch_Status = DRAFTED_COM_2026` und `Draft_ID` atomar aktualisiert.

---

### Task 1: Template-Enrichment Härtung

**Files:**
- Modify: `apps/sales-os/engine/canonical_template_factory.py:60-70`
- Test: `apps/sales-os/tests/test_canonical_templates.py`

- [x] **Step 1: Sanitize Company Name Integration**
  In `canonical_template_factory.py` wird `sanitize_company_name` aus `hsb_core` genutzt, damit bei Freemail-Adressen (z. B. `t-online.de`) der echte Firmenname erhalten bleibt statt auf „Ihr Unternehmen“ zurückzufallen.
- [x] **Step 2: Testlauf**
  `pytest apps/sales-os/tests -k "canonical or com_mailbox"` -> 100% PASS.

---

### Task 2: Erzeugung von 100 Entwürfen für Joel Cherino Diaz (`.com`)

**Files:**
- Target Mailbox: `j-cherino@hsb-boden.com`
- Target Sheet: `ALL_LEADS` (ID: `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`)

- [ ] **Step 1: Dry-Run Prüfung für 100 Leads (Joel)**
  Befehl: `python3 apps/sales-os/engine/run_com_batch.py --owner JOEL --count 100`
  Erwartung: 100 qualifizierte Leads ausgewählt, Firmennamen und Anreden fehlerfrei.
- [ ] **Step 2: Scharfschaltung & IMAP-Injektion (Joel)**
  Befehl: `python3 apps/sales-os/engine/run_com_batch.py --owner JOEL --count 100 --apply`
  Erwartung: 100 Entwürfe in KASServer `Entw&APw-rfe` injiziert, Sheet `ALL_LEADS` aktualisiert.
- [ ] **Step 3: Verifikation des Postfachstands**
  Befehl: `python3 apps/sales-os/engine/com_mailbox_manager.py --status`
  Erwartung: `j-cherino@hsb-boden.com` zeigt 149 Entwürfe (49 bisherige + 100 neue).

---

### Task 3: Erzeugung von 100 Entwürfen für Jordie Post (`.com`)

**Files:**
- Target Mailbox: `j-post@hsb-boden.com`
- Target Sheet: `ALL_LEADS` (ID: `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`)

- [ ] **Step 1: Dry-Run Prüfung für 100 Leads (Jordie)**
  Befehl: `python3 apps/sales-os/engine/run_com_batch.py --owner JORDI --count 100`
  Erwartung: 100 qualifizierte Leads ausgewählt, GF `Jordie Post` in Impressum & Signatur.
- [ ] **Step 2: Scharfschaltung & IMAP-Injektion (Jordie)**
  Befehl: `python3 apps/sales-os/engine/run_com_batch.py --owner JORDI --count 100 --apply`
  Erwartung: 100 Entwürfe in KASServer `Entw&APw-rfe` injiziert, Sheet `ALL_LEADS` aktualisiert.
- [ ] **Step 3: Verifikation des Postfachstands**
  Befehl: `python3 apps/sales-os/engine/com_mailbox_manager.py --status`
  Erwartung: `j-post@hsb-boden.com` zeigt 110 Entwürfe (10 bisherige + 100 neue).

---

### Task 4: Cloudflare-Architekturbewertung für `hsb-boden.com`

**Dokumentation:**
- Analyse des DNS-, DMARC- und Web-Routing-Nutzen bei Migration der Nameserver zu Cloudflare.
- Gegenüberstellung der Risiken (DNS-Propagation, SPF/DKIM-Fehlkonfiguration bei Mail-Routing).
- Handlungsempfehlung für den Betreiber.

---

### Task 5: Plattformübergreifende Synchronisation (GitHub Repos)

**Files:**
- Sync Monorepo `hsb-boden` und Standalone `hsb-sales-os`
- Git Commit & Push zu `origin/main`
