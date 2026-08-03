# Trust- und Referenz-Publication-Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Teamprofile und ausführliche Case Studies technisch vorbereiten, ohne erfundene oder ungeprüfte Inhalte veröffentlichen zu können.

**Architecture:** Ein kleines typisiertes Trust-Content-Modell trennt Entwurf, Verifikation und Veröffentlichungsfreigabe. Filterfunktionen geben nur Datensätze aus, die freigegeben sind und die erforderlichen Nachweise besitzen. Die initialen Datenlisten bleiben leer; dadurch entstehen keine sichtbaren Platzhalter oder Claims.

**Tech Stack:** TypeScript, Zod, Vitest, bestehende Astro-Datenarchitektur.

## Constraints

- Keine sichtbaren Teamprofile, Kundenstimmen, Zertifikatslogos oder Case-Study-Kennzahlen ohne reale Daten und dokumentierte Freigabe.
- Keine erfundenen Namen, Funktionen, Bilder, Projektflächen, Zeitwerte oder Auditergebnisse.
- Bestehende freigegebene/anonymisierte Referenzlogik bleibt unverändert.
- Kein Merge oder Production-Deploy.

## Tasks

### 1. Test-first Publication-Vertrag

- Create `tests/trust-publication-gates.test.ts`.
- Unfreigegebene Teamprofile und Case Studies müssen ausgeschlossen werden.
- Freigegebene Datensätze benötigen Quellen-/Freigabenachweis.
- Kundenname, Logo und exakter Standort dürfen nur bei expliziten Einzel-Freigaben erscheinen.
- Die initialen Datenlisten enthalten keine Platzhalter.

### 2. Typisiertes Trust-Modell

- Create `src/lib/trust.ts` mit Zod-Schemas und Filterfunktionen.
- Modell für Teamprofile, Qualifikationen und Case Studies.
- Publication-Status `draft | verified | approved`.
- Separate Freigaben für Kundenname, Logo, Standort, Kennzahlen, Zitat und Bilder.

### 3. Leere kanonische Datenquelle

- Create `src/data/trustContent.ts` mit typisierten leeren Arrays.
- Keine Demo-Daten und keine erfundenen Beispiele.

### 4. Redaktions- und Owner-Runbook

- Create `docs/content/TRUST_AND_CASE_STUDY_APPROVAL_WORKFLOW.md`.
- Definiere Pflichtnachweise, Freigaben, Bildrechte und Veröffentlichungscheck.

### 5. Verifikation

- CI, Quality Assurance, Security, Lighthouse und Deploy Preview müssen grün sein.
- PR bleibt ungemergt und erzeugt keine sichtbaren Production-Inhalte.
