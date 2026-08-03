# Projektablauf und Conversion-Orientierung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine eigenständige, belegbare Projektablauf-Seite bereitstellen, die bestehende Navigation darauf umstellen und die zentrale Telefonnummer im Header direkt nutzbar machen.

**Architecture:** Die neue Astro-Seite nutzt ausschließlich bestehende Layout- und CTA-Komponenten. Die bestehende Startseitenübersicht bleibt erhalten und erhält einen Detail-Link; Navigation und Header greifen auf die zentralen Daten aus `src/data` zurück. Es werden keine neuen Claims, Dependencies, Cloudflare-Bindings oder externen Konten eingeführt.

**Tech Stack:** Astro 6, TypeScript, Tailwind CSS 4, Vitest, Cloudflare Pages Preview über bestehende GitHub Actions.

## Global Constraints

- Kein Merge und kein Production-Deploy ohne separate Freigabe.
- Keine DNS-, Secret-, Cloudflare- oder CRM-Änderung.
- Keine erfundenen Zertifikate, Referenzen, Personen, Zahlen oder Leistungsversprechen.
- Bestehende Projektinhalte nur strukturieren; keine neue fachliche Systemempfehlung.
- Vor Abschluss müssen `npm run test:run`, `npm run check` und `npm run build` erfolgreich sein.

---

### Task 1: Regressionstest für Route und Verlinkung

**Files:**
- Create: `tests/project-flow-navigation.test.ts`

**Interfaces:**
- Consumes: Quelltexte aus `src/pages`, `src/data` und `src/components/layout`.
- Produces: Regressionstest für Route, kanonische Navigation, Startseiten-Detail-Link und zentrale Telefonverwendung.

- [ ] **Step 1: Failing test erstellen**
- [ ] **Step 2: Draft-PR öffnen und erwarteten Fehler wegen fehlender Route/Links bestätigen**
- [ ] **Step 3: Test nach der Implementierung erneut ausführen lassen**

### Task 2: Eigenständige Projektablauf-Seite

**Files:**
- Create: `src/pages/projektablauf/index.astro`

**Interfaces:**
- Consumes: `BaseLayout`, `PageHero`, `CTASection`.
- Produces: Indexierbare Route `/projektablauf/` mit fünf nachvollziehbaren Phasen und klarer Kontaktweiterleitung.

- [ ] **Step 1: Seite mit vorhandenen, belegbaren Prozessschritten erstellen**
- [ ] **Step 2: Keine HowTo- oder LocalBusiness-Strukturdaten ergänzen**
- [ ] **Step 3: Mobile und semantische Lesbarkeit über bestehende Klassen sicherstellen**

### Task 3: Navigation und Startseiten-Weiterführung

**Files:**
- Modify: `src/data/navigation.ts`
- Modify: `src/pages/index.astro`

**Interfaces:**
- Consumes: Neue Route `/projektablauf/`.
- Produces: Kanonischer Navigationslink und sichtbarer Detail-Link aus der bestehenden Prozessübersicht.

- [ ] **Step 1: Hauptnavigation von `/#projektablauf` auf `/projektablauf/` umstellen**
- [ ] **Step 2: Unter der bestehenden Vier-Schritte-Übersicht einen sekundären Link zur Detailseite ergänzen**
- [ ] **Step 3: Bestehende Startseiteninhalte und Claims unverändert lassen**

### Task 4: Klickbare zentrale Telefonnummer

**Files:**
- Modify: `src/components/layout/Header.astro`

**Interfaces:**
- Consumes: `site.phone` aus `src/data/site.ts`.
- Produces: `tel:`-Link im Desktop-Header und mobilen Menü ohne duplizierte Telefonnummer.

- [ ] **Step 1: `site` importieren und `phoneHref` aus der zentralen Nummer ableiten**
- [ ] **Step 2: Desktop-Telefonlink vor dem Haupt-CTA ergänzen**
- [ ] **Step 3: Mobilen Telefonlink im Menü ergänzen**

### Task 5: Verifikation und PR-Gate

**Files:**
- No source additions beyond Tasks 1–4.

**Interfaces:**
- Consumes: GitHub Actions auf dem Draft-PR.
- Produces: Reviewbarer PR mit Build-, Test-, Check-, Security-, Lighthouse- und Preview-Evidenz.

- [ ] **Step 1: `npm run test:run` über CI bestätigen**
- [ ] **Step 2: `npm run check` und `npm run build` über CI bestätigen**
- [ ] **Step 3: Cloudflare Pages Preview ausschließlich durch den bestehenden PR-Workflow erzeugen lassen**
- [ ] **Step 4: PR nicht mergen und keinen Production-Workflow starten**
