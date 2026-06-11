# Home Design Final Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die HSB-Startseite gestalterisch finalisieren, Stilbrueche entfernen und Desktop/Mobile sichtbar konsistenter machen.

**Architecture:** Globale Typo-, Radius-, CTA- und Oberflaechenregeln werden in `global.css` stabilisiert. Danach werden Hero, Problem-/Leistungs-/Trust-Module auf dieselbe Designlogik gezogen und abschliessend im Build und in der Preview geprueft.

**Tech Stack:** Astro, Tailwind Utilities, globale CSS-Tokens, Cloudflare Preview

---

### Task 1: Globale Stilregeln stabilisieren

**Files:**
- Modify: `src/styles/global.css`

- [ ] Eine konsistente Radius-, Button- und Typologik fuer die Startseite festziehen.
- [ ] Pseudo-premium Effekte reduzieren und echte Interaktionssauberkeit vorziehen.

### Task 2: Einstieg und Rhythmus korrigieren

**Files:**
- Modify: `src/pages/index.astro`
- Modify: `src/components/layout/Header.astro`

- [ ] Hero-Hierarchie, Abstaende und CTA-Gewichtung beruhigen.
- [ ] Schneller beweisen, was HSB macht und fuer wen.
- [ ] Top-Fold auf Mobile und Desktop visuell ausgewogener machen.

### Task 3: Mittelteil vereinheitlichen

**Files:**
- Modify: `src/components/sections/SchmerzpunkteSection.astro`
- Modify: `src/components/sections/ServiceGrid.astro`
- Modify: `src/components/sections/IndustryGrid.astro`

- [ ] Gleiches Karten- und Spacing-System durchziehen.
- [ ] Ueberinszenierte Labels entfernen oder auf belastbare Begriffe zurueckbauen.

### Task 4: Trust-Flaechen glaubwuerdiger machen

**Files:**
- Modify: `src/components/sections/ProofMediaSection.astro`
- Modify: `src/components/references/ReferenceMapPreview.astro`
- Modify: `src/components/references/ReferenceCard.astro`
- Modify: `src/components/sections/ManufacturerProof.astro`

- [ ] Trust ueber echte Systemlogik und klare Einordnung statt ueber dekorative Tech-Anmutung erzeugen.
- [ ] Sichtbare Beweisfuehrung staerken, ohne Freigabe-/Anonymisierungsregeln zu verletzen.

### Task 5: Abschlusstakt und Verifikation

**Files:**
- Modify: `src/components/sections/HomepageFAQSection.astro`
- Modify: `src/components/sections/CTASection.astro`

- [ ] Unteres Drittel sauber in den Gesamtton integrieren.
- [ ] `npm run test:run`
- [ ] `npm run check`
- [ ] `npm run build`
- [ ] Preview bzw. lokales Ergebnis visuell auf Header, Hero, Referenzen und CTA pruefen.
