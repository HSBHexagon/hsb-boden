# HSB Boden — Go-Live-Vervollständigung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die bereits umgesetzte HSB-Design-Überarbeitung (Logo, Scroll-Header, Referenzbilder, SEO-H1, Desktop-Schärfung — heute auf Preview live) trust-sicher und messbar bis zur Produktions-Reife bringen.

**Architecture:** Astro-SSR + Tailwind, Cloudflare Workers. Bestehende Routing- und Datenstruktur bleibt unverändert. Änderungen sind chirurgisch: ein Daten-Gate (Südzucker), drei Copy-Abschwächungen, dann Qualitätsmessung (Review/Lighthouse/A11y) vor dem Production-Deploy.

**Tech Stack:** Astro 5, Tailwind, React-Islands, Zod-validierte Daten (`src/data/*.ts`), Vitest, Wrangler, Playwright (visuelle Verifikation), Lighthouse.

**Was NICHT Teil dieses Plans ist (schon erledigt, heute committed `bf86228`):** Logo-Einsatz, Header-Scroll-Kontrast, Referenzbilder in Hero/Proof/`/referenzen/`, Hero-H1+CTAs, ProofMediaSection-Layout, Footer-Logo.

**Userentscheidungen (außerhalb Claude):** Südzucker-Freigabe (Task 0), Token `cfat_Tc90`-Rotation, DNS-Cutover `hsb-boden.de`, echte Fotos/Logos.

---

## File Structure

| Datei | Verantwortung | Tasks |
|---|---|---|
| `src/data/references.ts` | Referenzdaten + Freigabestatus | Task 0 |
| `src/components/sections/ProofMediaSection.astro` | Eigene Session-Copy (Claims) | Task 1 |
| `src/pages/referenzen/index.astro` | CTA-Reichweitenclaim | Task 2 |
| `src/pages/{leistungen,branchen,wissen,kontakt,impressum,datenschutz,karriere}/*` | Restliche Content-Seiten (Review-Ziel) | Task 3 |
| (Messung, keine Datei) | Lighthouse + A11y | Task 4 |
| `wrangler.toml` (read-only) | Production-Env-Check | Task 5 |

---

## Task 0: GATE — Südzucker-Freigabe (Userentscheidung, blockiert Go-Live)

**Files:**
- Modify (nur im NEIN-Pfad): `src/data/references.ts:22`

**Hintergrund:** `references.ts:3` führt `Südzucker AG` mit `approvalStatus: "approved"` + `canShowLogo: true` + Logo `/logos/suedzucker.svg`. Render-Logik (`src/lib/content.ts:147-156`): `displayName = approved ? publicName : anonymousName`, `logo` nur wenn `approved && canShowLogo`. Erscheint öffentlich auf `/` und `/referenzen/`. Risiko: in einer früheren Session wurden „76 Zeilen halluzinierte Reviews" entfernt — der Eintrag könnte Alt-Halluzination sein.

- [ ] **Step 1: Frage an Joel stellen (kein Code)**

> „Ist Südzucker AG ein realer HSB-Kunde mit schriftlicher Freigabe für Namens- und Logo-Nutzung?"

- [ ] **Step 2a: Antwort JA → keine Änderung**

Eintrag bleibt unverändert. Task 0 abgehakt, weiter zu Task 1.

- [ ] **Step 2b: Antwort NEIN/unklar → anonymisieren**

In `src/data/references.ts` den Südzucker-Eintrag ändern:

```diff
-    year: "2026",
-    approvalStatus: "approved",
+    year: "2026",
+    approvalStatus: "anonymous",
```

Das genügt: `getPublicReferences()` zeigt dann automatisch `anonymousName` („Zuckerproduktion in Sachsen-Anhalt") und blendet das Logo aus (`canShowLogo = approved && …` = false). `canShowLogo`/`logo`-Felder bleiben unangetastet — keine weiteren Edits nötig.

- [ ] **Step 3: Verifikation (nur NEIN-Pfad)**

Run: `npm run check`
Expected: 0 errors.
Run: `grep -c '"approved"' src/data/references.ts`
Expected: `0` (kein approved-Eintrag mehr).

- [ ] **Step 4: Commit (nur NEIN-Pfad)**

```bash
git add src/data/references.ts
git commit -m "fix(trust): Südzucker auf anonymisierte Referenz zurückstufen (keine belegte Freigabe)"
```

**Rollback:** `git revert <hash>` — stellt `approved` wieder her, falls Freigabe nachgereicht wird.

---

## Task 1: ProofMediaSection-Claims auf Belegbares abschwächen

**Files:**
- Modify: `src/components/sections/ProofMediaSection.astro`

**Hintergrund:** Diese Texte stammen aus der heutigen Session (eigene Copy, kein Fremd-Defekt), sind aber unbelegte Tatsachenbehauptungen. Nur abschwächen, falls Joel die Aussagen NICHT belegen kann; sonst überspringen.

- [ ] **Step 1: Section-Lead abschwächen**

In `src/components/sections/ProofMediaSection.astro` ersetzen:

```diff
-        <p class="lead mt-4">
-          Keine Stockfotos. Die abgebildeten Flächen wurden von Hexagon Säurebau geplant und ausgeführt.
-        </p>
+        <p class="lead mt-4">
+          Keine Stockfotos, sondern reale Industrieboden-Flächen aus dem HSB-Arbeitsumfeld.
+        </p>
```

- [ ] **Step 2: HACCP-Claim im ersten Panel abschwächen**

```diff
-    text:
-      "Fugenarme keramische Systeme mit Gefälle, Rinnenkante und Säureschutzbeschichtung — ausgeführt nach HACCP-relevanten Hygieneanforderungen.",
+    text:
+      "Fugenarme keramische Systeme mit Gefälle, Rinnenkante und Säureschutzbeschichtung — ausgelegt für die Hygieneanforderungen von Lebensmittelbetrieben.",
```

- [ ] **Step 3: Verifikation**

Run: `npm run check`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add src/components/sections/ProofMediaSection.astro
git commit -m "fix(copy): ProofMedia-Aussagen auf belegbare Formulierungen abschwächen"
```

**Rollback:** `git revert <hash>` — Wenn Joel die Eigenausführung/HACCP belegt, Originaltext wiederherstellen.

---

## Task 2: Reichweitenclaim „bundesweit" auf `/referenzen/` prüfen

**Files:**
- Modify: `src/pages/referenzen/index.astro:64`

- [ ] **Step 1: Nur wenn „bundesweit" nicht zutrifft, ändern**

```diff
-  <CTASection title="Industriebodenprojekt anfragen" text="HSB plant keramische Industrieböden, Säureschutz, PU-Beton, Entwässerung und Sanierungen für Lebensmittel-, Getränke-, Pharma- und Chemiebetriebe in NRW und bundesweit." />
+  <CTASection title="Industriebodenprojekt anfragen" text="HSB plant keramische Industrieböden, Säureschutz, PU-Beton, Entwässerung und Sanierungen für Lebensmittel-, Getränke-, Pharma- und Chemiebetriebe — Schwerpunkt NRW und Münsterland." />
```

- [ ] **Step 2: Verifikation + Commit**

Run: `npm run check` → 0 errors.
```bash
git add src/pages/referenzen/index.astro
git commit -m "fix(copy): Reichweitenclaim auf belegbaren Schwerpunkt eingrenzen"
```

**Rollback:** `git revert <hash>`.

---

## Task 3: Restliche Seiten durch seo-content-reviewer

**Files (Review-Ziel, read-only):**
- `src/pages/leistungen/index.astro`, `src/pages/leistungen/[slug].astro`
- `src/pages/branchen/index.astro`, `src/pages/branchen/[slug].astro`
- `src/pages/wissen/index.astro`, `src/pages/wissen/[slug].astro`
- `src/pages/kontakt/index.astro`, `src/pages/impressum/`, `src/pages/datenschutz/`, `src/pages/karriere/`

- [ ] **Step 1: Subagent dispatchen**

Den `seo-content-reviewer` (ab nächster Session in Registry) über die obigen Seiten laufen lassen. Prompt: „Prüfe diese Seiten gegen Trust-Integrität, H1-genau-einmal, Alt-Texte, Meta-Längen. Report im definierten Format."

- [ ] **Step 2: KRITISCH-Findings als eigene Tasks behandeln**

Jeder KRITISCH-Befund → Stop, an Joel zurück (keine autonome Trust-Mutation). WARNUNG-Befunde → fixen falls eigene Copy.

- [ ] **Step 3: Commit (falls Fixes)**

```bash
git add src/pages/
git commit -m "fix(seo): Reviewer-Findings auf Content-Seiten beheben"
```

**Rollback:** `git revert <hash>` pro Fix-Commit.

---

## Task 4: Lighthouse + A11y gegen Prod-Build (ADR-003-Pflicht)

**Files:** keine (Messung).

**Hintergrund:** ADR-003 verlangt Lighthouse-Messung vor „fertig"; heute übersprungen. Ziel ≥90 Perf / ≥95 A11y / ≥95 Best-Practices / ≥95 SEO. Zahlen notieren.

- [ ] **Step 1: Prod-Build + Preview-Deploy**

Run: `npm run build` → „Complete!"
Run: `CLOUDFLARE_API_TOKEN=$(security find-generic-password -s "cloudflare-workers-deploy-token" -w) npx wrangler deploy`
Expected: Preview-URL ausgegeben.

- [ ] **Step 2: Lighthouse über chrome-devtools MCP**

`mcp__chrome-devtools__lighthouse_audit` gegen die Preview-URL (Desktop). Zahlen je Kategorie notieren.

- [ ] **Step 3: A11y-Check (Playwright)**

Fokuszustände (Tab durch Header-Nav + CTAs), Kontrast Buttons, Touch-Targets ≥44px, keine horizontalen Scrollbars bei 390px. Screenshot 1440 + 390.

- [ ] **Step 4: Ergebnis dokumentieren**

Zahlen in `_AI_Memory/Projects/hsb-boden/PROJECT_STATUS.md` eintragen. Unter Ziel → Findings als Folge-Tasks.

**Rollback:** entfällt (read-only Messung).

---

## Task 5: Production-Deploy-Readiness (Gate, kein echter Deploy)

**Files:** `wrangler.toml` (read-only Prüfung).

- [ ] **Step 1: Dry-Run gegen Production-Env**

Run: `npm run deploy:dry-run`
Expected: Build grün, Upload-Simulation ohne Fehler, Routes `hsb-boden.de/*` korrekt aufgelöst.

- [ ] **Step 2: Gate-Prüfung**

Bestätigen: Task 0 (kein offener KRITISCH), Task 3 (Review grün), Task 4 (Lighthouse-Ziele erreicht). NUR dann ist Production freigegeben.

- [ ] **Step 3: STOP — echter Production-Deploy ist Userentscheidung**

Production-Deploy (`npm run deploy:production`) erst NACH Joels DNS-Cutover-Entscheidung. Nicht autonom.

**Rollback:** Cloudflare Worker-Versionen erlauben Rollback auf vorige Version-ID.

---

## Self-Review

**1. Spec-Coverage:** Südzucker-Blocker (T0) ✓, eigene Claims (T1/T2) ✓, restliche Seiten (T3) ✓, ADR-003-Lighthouse-Lücke (T4) ✓, Production-Gate (T5) ✓. Schon erledigte Design-Arbeit korrekt als out-of-scope markiert.

**2. Placeholder-Scan:** Keine TBD/TODO. Jeder Code-Schritt zeigt exakten Diff. T3 nennt Subagent-Dispatch statt vorab erfundener Fixes (Findings sind noch unbekannt — bewusst, kein Placeholder).

**3. Typ-Konsistenz:** `approvalStatus`/`canShowLogo`/`displayName` konsistent mit `src/lib/content.ts:147-156`. Deploy-Scripts (`deploy:dry-run`, `deploy:production`) existieren in `package.json`.

---

## Sicherheits-Gates (durchgehend gültig)
- Keine autonome Trust-Mutation (Südzucker, neue Referenzkunden) — Stop→Frage.
- Kein Production-Deploy ohne Joels „deploy" + DNS-Entscheidung.
- Keine lokalen Commits pushen ohne Freigabe (offen: `bf86228`, `25ccf2d`).
