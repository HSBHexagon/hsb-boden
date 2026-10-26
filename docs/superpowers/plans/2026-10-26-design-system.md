# Design-System und Barrierefreiheit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Gestaltung der Website hat eine einzige Token-Quelle, erfüllt die Kontrastanforderung für Formularfelder (WCAG 2.2 AA) und wird in CI auf den relevanten Seiten gemessen.

**Architecture:** Zuerst der kleinste Fix mit dem größten Nutzen (Feldkontrast, testgetrieben), dann die Token-Konsolidierung in `global.css`, dann ein Messspike für Schriften, zuletzt die Erweiterung der Lighthouse-Abdeckung. Jede Änderung hat einen Test, der vorher rot ist.

**Tech Stack:** Astro 7, Tailwind CSS 4 (`@theme`, `@config`), `@fontsource/outfit`, Vitest, Lighthouse CI (`treosh/lighthouse-ci-action`).

**Spec:** Keine Spezifikation vorhanden. Grundlage ist der Abschnitt „Ist-Zustand“ (Stand 2026-10-26).

## Global Constraints

- Keine Website-Code-Änderung ohne Freigabe: `src/`, `public/`, `components/`, `layouts/`, `styles/`, `astro.config.*`, `wrangler.toml`, `package.json`, Lockfiles. Fast jeder Task hier berührt sie und beginnt deshalb mit „Freigabe einholen“.
- Marken-Werte bleiben unverändert, soweit nicht ausdrücklich genannt: Rot `#cb0000`, Schwarz `#161a20`, Stahl `#3d4652`, Nebel `#f3f5f7`, Linie `#d8dde3`, Signal `#f6c343`, Schrift Outfit. Eine sichtbare Änderung am Markenauftritt entscheidet der Owner; Optik-Freigabe per Screenshot-Vergleich.
- Keine neuen Abhängigkeiten ohne Freigabe (betrifft `package.json` und Lockfile).
- Keine unbelegten Zertifizierungs- oder Referenzclaims; keine Kundennamen oder Logos ohne Freigabe.
- Kein `git add .`; kein Push, kein Deploy ohne Freigabe; keine Secrets; vor Commit `python3 scripts/verify_ssot.py` mit Exit 0; vor Abschluss `npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run` in `apps/website`.

## Ist-Zustand (Belege)

| Befund | Beleg |
|---|---|
| Markenfarben stehen in `tailwind.config.mjs` (`hsb.*`); Radien, Schatten und Easing stehen als `:root`-Variablen in `global.css`; Textfarbe `#161a20` und der Verlauf im `body` sind fest eincodiert. Die JS-Konfiguration wird per `@config` geladen. | `apps/website/tailwind.config.mjs:6-21`, `src/styles/global.css:8-18`, Body-Regel |
| Tailwind 4 erkennt JS-Konfigurationen nicht mehr automatisch; `@config` ist für Kompatibilität gedacht, und `@theme` ist der vorgesehene Ort für Tokens [D2]. | [D2] |
| Kontrast (eigene Berechnung nach WCAG-Formel, 2026-10-26): Rot auf Weiß 5,93:1, Rot auf Nebel 5,43:1, Stahl auf Weiß 9,56:1, Schwarz auf Signal 10,65:1, Hellrot `#ff8a7d` auf Schwarz 7,64:1. Textpaare bestehen AA (4,5:1). | `python3`-Rechnung im Task 1, Step 1 |
| Formularfelder (`<input>`, `<select>`, `<textarea>`) in `LeadForm.astro` nutzen `border-hsb-line` (`#d8dde3`): **1,37:1** auf Weiß. WCAG 1.4.11 verlangt 3:1 für Teile, die ein Bedienelement erkennbar machen [D1]. Native Checkboxen sind browserbestimmt und ausgenommen. Dekorative Kartenränder mit derselben Farbe sind nicht betroffen. | `apps/website/src/components/forms/LeadForm.astro:27-100`; 10 Zeilen mit Feld und `border-hsb-line` |
| Schrift: `@fontsource/outfit` mit fünf Schnitten (400, 600, 700, 800, 900) per CSS-Import; Test `webperf-fonts.test.ts` prüft Head-Hints, keine externen Google-Fonts-Links. | `apps/website/src/styles/global.css:1-5`, `tests/webperf-fonts.test.ts` |
| Es gibt keinen Dunkelmodus (`color-scheme: light`); `prefers-reduced-motion` ist berücksichtigt. | `global.css:10,255` |
| Lighthouse-Konfiguration: 5 URLs, `numberOfRuns: 1`, Barrierefreiheit und SEO als `error` ab 0,95, Performance als `warn`. Die Seiten `/kontakt/`, `/danke-projektanfrage/`, `/en/`, `/fr/`, `/beanspruchungs-check/` sind gebaut, aber nicht in der Liste. | `apps/website/.lighthouserc.json`; `ls dist/` |

## Quellen (abgerufen 2026-10-26)

- [D1] WCAG 2.2, Understanding SC 1.4.11 Non-text Contrast: https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html. Stufe AA; mindestens 3:1 für visuelle Informationen, die ein Bedienelement erkennbar machen; Grenzen sind nur nötig, wenn es keinen anderen visuellen Hinweis gibt; Fokusindikatoren müssen ebenfalls 3:1 erreichen; browserbestimmte Darstellung ist ausgenommen.
- [D2] Tailwind CSS v4 Dokumentation über Context7 (`/tailwindlabs/tailwindcss.com`): `@theme` für Tokens (Farben, Schriften, Easing); `@config` und `@plugin` bleiben für Kompatibilität nutzbar und dürfen mit `@theme` gemischt werden; `corePlugins`, `safelist`, `separator` der JS-Konfiguration werden in v4 nicht mehr unterstützt.
- [D3] Astro Fonts-API über Context7 (`/withastro/docs`, Guides „Fonts“ und `astro:assets`): Konfiguration `fonts: [{ provider: fontProviders.fontsource(), name, cssVariable, fallbacks }]` in `astro.config.*`; `<Font cssVariable="…" preload />` im `<head>`; optimierte Fallbacks aus Schriftmetriken. Ob die Version `astro ^7.3.2` diese API enthält, ist in Task 3 zu belegen (die Doku-Quelle nennt teils eine ältere Hauptversion).

## Review Focus

- Dynamisch zusammengesetzte Klassennamen (z. B. `bg-${farbe}`) gehen bei jeder Token-Umstellung verloren, weil Tailwind nur vollständige Klassen erkennt: vor der Umstellung im Quelltext danach suchen.
- Feldrahmen mit 3:1 wirken dunkler als bisher: Fokusring (`ring-hsb-red`) und Fehlerzustand müssen weiterhin unterscheidbar bleiben; Screenshot-Vergleich im Task 1.
- Der Cookie-Banner enthält Bedienelemente und sitzt über dem Inhalt: Kontrast und Fokusreihenfolge müssen dort ebenfalls stimmen (nicht nur im Formular).
- Mobile Breite: Die Lighthouse-Läufe sind Desktop-/Standardprofil; das Formular muss bei 320 px ohne horizontales Scrollen bedienbar bleiben (Prüfung in Task 4).
- Schriftwechsel verschiebt Zeilenumbrüche: Layoutverschiebungen (CLS) und abgeschnittene Überschriften auf `/`, `/kontakt/` und einer Branchenseite prüfen.

---

### Task 1: Kontrast der Formularfelder (WCAG 1.4.11)

**Files:**
- Modify: `apps/website/tailwind.config.mjs` (neues Token `field`)
- Modify: `apps/website/src/components/forms/LeadForm.astro`, `StressCheck.astro`, `src/components/layout/CookieConsent.astro` (nur, wo Bedienelemente `border-hsb-line` nutzen)
- Create: `apps/website/tests/helpers/contrast.ts`
- Create: `apps/website/tests/design-contrast.test.ts`

**Interfaces:**
- Produces: `contrastRatio(foreground: string, background: string): number` in `tests/helpers/contrast.ts` (Hex-Eingabe `#rrggbb`, WCAG-Formel, nicht gerundet); Tailwind-Farbe `hsb.field`; Kandidat `#7b8794` (3,66:1 auf Weiß, 3,35:1 auf Nebel, nachgerechnet), Optik-Freigabe durch den Owner.

- [ ] **Step 1: Freigabe einholen** für `tailwind.config.mjs` und die drei Komponenten; Kandidatenfarbe per Screenshot bestätigen lassen.
- [ ] **Step 2: Failing Tests schreiben** in `design-contrast.test.ts`. Die Konfiguration wird **als Text** gelesen (`readFileSync`, Regex `field:\s*"(#[0-9a-fA-F]{6})"`), nicht importiert: `tailwind.config.mjs` ruft `require(...)` in einer ESM-Datei auf und ist deshalb nicht zuverlässig importierbar. Tests: `hsb.field has at least 3:1 against white and against hsb.mist`; `hsb.red text has at least 4.5:1 against white`; `no input, select or textarea (except checkbox and radio) uses border-hsb-line` (durchsucht `src/**/*.astro` Zeile für Zeile nach Feldern mit dieser Klasse).
- [ ] **Step 3: Run.** `cd apps/website && npx vitest run tests/design-contrast.test.ts`. Expected: Feldtest und Klassentest FAIL (Token fehlt, 10 Treffer), Rot-Test PASS.
- [ ] **Step 4: Umsetzen:** Token `hsb.field: "#7b8794"` in `tailwind.config.mjs`; in den Komponenten Felder von `border-hsb-line` auf `border-hsb-field` umstellen; Karten und Trenner behalten `border-hsb-line`.
- [ ] **Step 5: Run.** `npx vitest run tests/design-contrast.test.ts && npm run check && npm run build`. Expected: alle PASS; im Build-CSS ist `border-hsb-field` enthalten (`grep -l "border-hsb-field" dist/_astro/*.css`).
- [ ] **Step 6: Sichtprüfung** (Preview): Feld normal, Fokus, Fehlerzustand, mobil 320 px, Screenshots dem Owner zeigen.
- [ ] **Step 7: Commit.** `git add apps/website/tailwind.config.mjs apps/website/src/components/forms/LeadForm.astro apps/website/src/components/forms/StressCheck.astro apps/website/src/components/layout/CookieConsent.astro apps/website/tests/helpers/contrast.ts apps/website/tests/design-contrast.test.ts` (nur tatsächlich geänderte Dateien), Nachricht `fix(a11y): Formularfeld-Rahmen mit 3:1 Kontrast`.

### Task 2: Token-Quelle konsolidieren

**Files:**
- Modify: `apps/website/src/styles/global.css`, `apps/website/tailwind.config.mjs`
- Test: `apps/website/tests/design-tokens.test.ts`

**Interfaces:**
- Consumes: `hsb.*`-Farben aus `tailwind.config.mjs` (inkl. `hsb.field` aus Task 1).
- Produces: `@theme`-Block in `global.css` mit `--color-hsb-red`, `--color-hsb-red-light`, `--color-hsb-black`, `--color-hsb-steel`, `--color-hsb-mist`, `--color-hsb-line`, `--color-hsb-signal`, `--color-hsb-field`, `--font-sans`; die bisherigen Klassen (`bg-hsb-red` usw.) bleiben unverändert nutzbar.

- [ ] **Step 1: Freigabe einholen** für `global.css` und `tailwind.config.mjs`.
- [ ] **Step 2: Klassennamen sichern.** Run: `rg -n '(bg|text|border|ring|from|to|via|fill|stroke|outline|divide|shadow)-(hsb-)?\$\{' apps/website/src --glob '*.astro' --glob '*.ts'`. Expected: keine Ausgabe (am 2026-10-26 geprüft: kein Treffer, es werden keine Farbklassen aus Variablen zusammengesetzt); bei Treffern sie vor der Umstellung als vollständige Klassennamen ausschreiben.
- [ ] **Step 3: Failing Test schreiben**, Name `global.css defines hsb colors in @theme and tailwind.config.mjs defines none`. Assertions: `global.css` enthält `@theme` und für jede der acht Farben die Zeile `--color-hsb-<name>: <hex>;` mit den Werten aus den Global Constraints (`field` mit dem in Task 1 bestätigten Wert); `tailwind.config.mjs` enthält kein `colors:`.
- [ ] **Step 4: Run.** `npx vitest run tests/design-tokens.test.ts`. Expected: FAIL.
- [ ] **Step 5: Umsetzen.** Farben und `--font-sans` nach `@theme`; `body`-Textfarbe auf `var(--color-hsb-black)`; `@config` bleibt für die Plugins `@tailwindcss/typography` und `tailwindcss-animate`, bis ein Wechsel auf `@plugin` mit gleichem Ergebnis belegt ist [D2].
- [ ] **Step 6: Kontrasttest umhängen.** In `design-contrast.test.ts` den Wert für `hsb.field` nicht mehr aus `tailwind.config.mjs`, sondern aus der Zeile `--color-hsb-field: #rrggbb;` in `src/styles/global.css` lesen (die Konfiguration enthält ihn nach Step 5 nicht mehr). Ohne diesen Schritt schlägt der Test aus Task 1 nach Task 2 fehl.
- [ ] **Step 6b: Run.** `npm run test:run && npm run check && npm run build`. Expected: alle grün; Stichprobe `grep -c "hsb-red" dist/_astro/*.css` liefert für jede Datei mit Treffern mehr als 0, und die Seitenzahl bleibt 58.
- [ ] **Step 7: Sichtvergleich** `/`, `/kontakt/` und eine Branchenseite vorher/nachher (Pixelvergleich per Playwright-Screenshot, Abweichung nur dort, wo Task 1 sie verursacht).
- [ ] **Step 8: Commit.** `git add apps/website/src/styles/global.css apps/website/tailwind.config.mjs apps/website/tests/design-tokens.test.ts`, Nachricht `refactor(design): Tokens in @theme zusammenführen`.

### Task 3: Spike Schriftladung (Astro Fonts-API gegen `@fontsource`)

**Files:**
- Create: `docs/audits/FONTS_SPIKE_2026-10.md`
- Modify (nur bei Adoption und Freigabe): `apps/website/astro.config.mjs`, `apps/website/src/layouts/BaseLayout.astro`, `apps/website/src/styles/global.css`, `apps/website/package.json`

**Interfaces:**
- Produces: Messtabelle (Anzahl und Bytes der Schriftdateien in `dist/`, Lighthouse-Werte LCP und CLS auf `/` und einer Branchenseite) für beide Varianten sowie eine Empfehlung mit Adoptionskriterien.

- [ ] **Step 1: Ist-Messung auf `main`.** Run: `cd apps/website && npm run build && find dist -name "*.woff2" | wc -l && du -cb $(find dist -name "*.woff2") | tail -1`. Expected: zwei Zahlen, in die Tabelle eintragen.
- [ ] **Step 2: Wegwerf-Branch mit Fonts-API** [D3]: `fonts`-Eintrag für Outfit mit denselben fünf Schnitten, `<Font cssVariable="--font-sans" preload={[{weight: 400}, {weight: 700}]} />`. Prüfen, ob `astro build` die Option akzeptiert. Expected: Build grün; sonst Spike beenden und „API in dieser Version nicht vorhanden“ eintragen.
- [ ] **Step 3: Gleiche Messung** wie Step 1 und Lighthouse-Lauf (3 Läufe je Seite, Median) für beide Varianten.
- [ ] **Step 4: Adoptionskriterien prüfen:** (a) weniger oder gleich viele Schriftbytes, (b) CLS nicht schlechter, (c) `font-src 'self'` genügt (Schriften werden beim Build selbst gehostet), (d) `npx vitest run tests/webperf-fonts.test.ts` unverändert grün. Nur wenn alle vier erfüllt sind, empfiehlt die Datei die Übernahme.
- [ ] **Step 5: Commit** der Messdatei: `git add docs/audits/FONTS_SPIKE_2026-10.md`, Nachricht `docs(audit): Schriftladung-Spike`. Die Übernahme selbst ist ein eigener Task nach Owner-Freigabe.

### Task 4: Lighthouse-Abdeckung erweitern

**Files:**
- Modify: `apps/website/.lighthouserc.json`

**Interfaces:**
- Produces: URL-Liste mit zusätzlich `/kontakt/`, `/danke-projektanfrage/`, `/beanspruchungs-check/`, `/en/`, `/fr/`; `numberOfRuns: 3`; zusätzliche Assertion `color-contrast` als `error`.

- [ ] **Step 1: Failing Prüfung.** Run: `python3 -c "import json,os;u=json.load(open('apps/website/.lighthouserc.json'))['ci']['collect']['url'];print(len(u))"`. Expected vorher: `5`.
- [ ] **Step 2: Konfiguration erweitern.** Neue URLs im selben Muster (`http://localhost/<pfad>/index.html`); `numberOfRuns` von 1 auf 3 (ein Lauf ist eine Einzelstichprobe und schwankt); Assertion `"color-contrast": ["error", {"minScore": 1}]` ergänzen.
- [ ] **Step 3: Pfade gegen den Build prüfen.** Run: `cd apps/website && npm run build && python3 -c "import json,os;[print(os.path.exists('dist'+u.split('localhost',1)[1]),u) for u in json.load(open('.lighthouserc.json'))['ci']['collect']['url']]"`. Expected: jede Zeile beginnt mit `True`.
- [ ] **Step 4: Laufzeit beobachten:** Beim ersten PR die Dauer des Workflows `lighthouse.yml` notieren; steigt sie unvertretbar, `numberOfRuns` auf 2 setzen, nicht Seiten streichen.
- [ ] **Step 5: Commit.** `git add apps/website/.lighthouserc.json`, Nachricht `ci(lighthouse): mehr Seiten, drei Läufe, Kontrastprüfung`.
