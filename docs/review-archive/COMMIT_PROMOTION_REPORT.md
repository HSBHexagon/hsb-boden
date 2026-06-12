# COMMIT_PROMOTION_REPORT

Stand: 2026-06-11
Rolle: Release Engineer
Scope: Analyse der lokalen Commit-Spanne `a591724..2369155`. Keine Website-Aenderungen, keine Commits, kein Push, kein Merge, kein Deployment, kein DNS.

## 1. Quellen

Verwendete Projektquellen:

- `PROJECT_CANONICAL_STRUCTURE.md`
- `PROJECT_CURRENT_STATE.md`
- `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md`

Mechanische Verifikation:

- `git log --reverse a591724..2369155`
- `git diff --name-status a591724..2369155`
- `git diff --stat a591724..2369155`
- `git diff --check a591724..2369155`
- `git merge-tree --write-tree --name-only 2369155 origin/main`

## 2. Ergebnis Kurzfassung

Die acht lokalen Commits sind eine lineare Erweiterung des Remote-PR-HEAD `a591724` bis zum lokalen Review-HEAD `2369155`.

- `a591724` ist direkter Vorfahr von `2369155`.
- Die Commit-Spanne ist mechanisch sauber: `git diff --check` meldet keine Whitespace-/Conflict-Marker-Probleme.
- Inhaltlich besteht die Spanne aus Website-Content, Motion-/UX-Polish, Tests und Audit-Evidenz.
- Keine Infrastrukturdateien wurden in dieser Spanne geaendert: kein `package.json`, kein `package-lock.json`, kein `wrangler.toml`, keine `.env`, kein `ops/`, kein `public/`.
- Der Arbeitsbaum ist nicht vollstaendig clean, weil mehrere Root-Reports untracked sind. Das betrifft die Commit-Qualitaet nicht, muss aber vor Promotion bewusst bereinigt oder einsortiert werden.

## 3. Commit-Liste

| Reihenfolge | Commit | Produktrelevanz | Inhalt |
| --- | --- | --- | --- |
| 1 | `f329a0d` | Ja | `services.ts`: Saeureschutz um WHG/Vinylester/pH 0-14; Keramik um Ruettelverlegetechnik/DIN EN 14411; Tests erweitert. |
| 2 | `a171478` | Ja | `industries.ts`: Chemie um WHG Paragraph 62/63, ESD, Stoffbestaendigkeit; Pharma um ISO 14644, GMP/FDA, porenfreie Versiegelung; Tests erweitert. |
| 3 | `9660f2d` | Ja | `articles.ts`: Artikel-Sections von Strings auf `{ title, body? }`; Schema und Wissensseiten-Template angepasst; Molkerei-/PU-Beton-Prosa ergaenzt; Tests erweitert. |
| 4 | `46780fc` | Ja | Reveal-Fundament: globale `.reveal`-CSS, IntersectionObserver in `BaseLayout`, reduced-motion-Fallback. |
| 5 | `8e419d2` | Ja | Staggered Scroll-Reveal fuer Service-, Branchen-, Schmerzpunkte- und ProofMedia-Grids. |
| 6 | `b1192b6` | Ja | Taktiles `active:scale-[0.99]` auf klickbaren Karten; Hover/Active-Transition auf 200ms entkoppelt. |
| 7 | `f300873` | Ja | Startseiten-Hero: dezentes Marken-Hexagon in der Eyebrow statt riskantem H1-Inline-Icon. |
| 8 | `2369155` | Nein, Audit | Masterpiece-SOTA-Bericht und drei Screenshot-Artefakte unter `docs/audit/`. |

## 4. Veraenderte Dateien

Kumulative Dateiliste in `a591724..2369155`:

| Status | Datei | Einordnung |
| --- | --- | --- |
| A | `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md` | Audit/Evidenz |
| A | `docs/audit/screenshots/hero-mobile-390-hexagon.png` | Audit/Evidenz |
| A | `docs/audit/screenshots/home-desktop-1440-after.png` | Audit/Evidenz |
| A | `docs/audit/screenshots/home-mobile-390-after.png` | Audit/Evidenz |
| M | `src/components/sections/IndustryGrid.astro` | Website/Motion |
| M | `src/components/sections/ProofMediaSection.astro` | Website/Motion |
| M | `src/components/sections/SchmerzpunkteSection.astro` | Website/Motion |
| M | `src/components/sections/ServiceGrid.astro` | Website/Motion |
| M | `src/data/articles.ts` | Website/Content-Modell |
| M | `src/data/industries.ts` | Website/Content |
| M | `src/data/services.ts` | Website/Content |
| M | `src/layouts/BaseLayout.astro` | Website/Globales Layout/JS |
| M | `src/lib/content.ts` | Website/Schema |
| M | `src/pages/index.astro` | Website/Hero |
| M | `src/pages/wissen/[slug].astro` | Website/Wissensseiten-Rendering |
| M | `src/styles/global.css` | Website/Motion/CSS |
| M | `tests/content.test.ts` | Tests |

Statistik: 17 Dateien, 215 Insertions, 33 Deletions.

## 5. Produktrelevante Aenderungen

Produktrelevant sind alle sieben Commits vor `2369155`.

Fachlicher Content:

- Services werden technischer und regulatorischer beschrieben.
- Branchen Chemie/Pharma erhalten konkrete Anforderungen wie WHG, ESD, ISO 14644, GMP/FDA.
- Wissensartikel erhalten teilweise echte Fachprosa statt generischer Fallbacktexte.
- Artikelmodell wechselt zu objektbasierten Sections mit optionalem `body`.

UX/Motion:

- Below-the-fold-Reveal wird global ueber CSS und einen IntersectionObserver aktiviert.
- Grids erhalten gestaffelte Reveal-Delays.
- Klickbare Karten erhalten taktiles Active-Feedback.
- Hero erhaelt ein dezentes Marken-Hexagon im Eyebrow.

Test-/Audit-Evidenz:

- `tests/content.test.ts` sichert neue Content-Anforderungen ab.
- `2369155` dokumentiert Ziel, Entscheidungen, Verifikation, Abweichungen und Screenshots.

## 6. Sauberkeit der lokalen Commits

Ja, die acht Commits sind lokal als Commit-Spanne sauber:

- lineare Spanne: `a591724` ist Ancestor von `2369155`.
- keine uncommitted tracked Aenderungen in der Spanne selbst.
- `git diff --check a591724..2369155`: keine Ausgabe, Exit 0.
- keine Infrastruktur-/Secret-/Deployment-Dateien in der Spanne.

Einschraenkung:

Der Worktree ist nicht clean, weil untracked Reports im Root liegen, unter anderem `BRANCH_DELTA_REPORT.md`, `FINAL_RELEASE_AUDIT.md`, `MERGE_RESOLUTION_PLAN.md`, `PROJECT_CANONICAL_STRUCTURE.md`, `PROJECT_CURRENT_STATE.md`, `RELEASE_CANDIDATE_STATUS.md`, `RELEASE_PATH.md` und weitere. Diese muessen vor einer Promotion bewusst einsortiert, ignoriert oder separat behandelt werden.

## 7. Risiken fuer Merge

Merge-Risiko: hoch.

`git merge-tree --write-tree --name-only 2369155 origin/main` meldet weiterhin Content-Konflikte. Konfliktdateien:

- `src/components/layout/Header.astro`
- `src/components/references/ReferenceMapPreview.astro`
- `src/components/sections/CTASection.astro`
- `src/components/sections/IndustryGrid.astro`
- `src/components/sections/ProofMediaSection.astro`
- `src/components/sections/SchmerzpunkteSection.astro`
- `src/components/sections/ServiceGrid.astro`
- `src/data/articles.ts`
- `src/layouts/BaseLayout.astro`
- `src/lib/content.ts`
- `src/pages/index.astro`
- `src/pages/wissen/[slug].astro`
- `src/styles/global.css`

Direkte Ueberschneidung der acht Commits mit Main-Aenderungen:

- `src/components/sections/IndustryGrid.astro`
- `src/components/sections/ProofMediaSection.astro`
- `src/components/sections/SchmerzpunkteSection.astro`
- `src/components/sections/ServiceGrid.astro`
- `src/data/articles.ts`
- `src/layouts/BaseLayout.astro`
- `src/lib/content.ts`
- `src/pages/index.astro`
- `src/pages/wissen/[slug].astro`
- `src/styles/global.css`

Bewertung:

Die acht Commits sind nicht der einzige Konfliktgrund, vergroessern aber die aktuelle Konfliktflaeche deutlich, vor allem bei Content-Schema, Wissensseiten, BaseLayout, globalem CSS und Grid-Komponenten.

## 8. Risiken fuer Deployment

Deployment-Risiko: mittel, solange nicht gemerged; hoch, wenn ohne frisches Gate oder ohne eindeutige Preview deployed wird.

Technische Risiken:

- `BaseLayout.astro` fuegt globales Browser-JS hinzu. Es ist klein und defensiv, aber muss nach Merge erneut gegen Browser/Build verifiziert werden.
- `.reveal` setzt `opacity: 0` bis zur Observer-Aktivierung. Reduced-motion und No-IntersectionObserver-Fallback sind vorhanden, aber nach Merge darf keine Above-the-fold-Komponente versehentlich mit `.reveal` belegt werden.
- Artikel-Schema wurde veraendert. Alle Datenverbraucher muessen nach Konfliktloesung auf `{ title, body? }` passen.

Content-/Claim-Risiken:

- Begriffe wie WHG, GMP/FDA, ISO 14644, pH 0-14 und DIN EN 14411 sind produktionsrelevant und sollten vor finalem Production-Go-Live fachlich/freigabeseitig abgesichert bleiben.
- Der Masterpiece-Audit dokumentiert bewusstes Weglassen riskanter Argelith-Hexalith-Claims; diese Entscheidung muss bei Konfliktloesung erhalten bleiben.

Infrastruktur:

- Kein direktes Infra-Risiko aus diesen acht Commits, weil keine Deploy-/Package-/Wrangler-/Env-Dateien geaendert wurden.

## 9. Empfehlung

Empfehlung: Die acht Commits als zusammenhaengendes lokales RC-Delta erhalten und in die PR-Promotion aufnehmen, aber nicht direkt in Produktion bringen.

Konkrete Reihenfolge:

1. Root-Reports konsolidieren oder bewusst als untracked lassen, damit der Promotion-Stand eindeutig bleibt.
2. Die acht Commit-Inhalte nicht einzeln cherry-picken, sondern als zusammenhaengende Spanne behandeln.
3. Vor Push/Promotion ein frisches lokales Gate auf `2369155` ausfuehren: `npm run check`, `npm run test:run`, `npm run build`.
4. Danach Remote-PR-Branch von `a591724` auf `2369155` bringen, falls die lokale Spanne promotet werden soll.
5. Konflikte gegen `main` in einem separaten Merge-Prep-Stand manuell loesen.
6. Nach Konfliktloesung erneut Gate + Preview-Verifikation ausfuehren.

Release-Entscheidung:

`2369155` ist ein sinnvoller lokaler Promotion-Kandidat fuer die Review-PR, aber noch kein produktionsreifer Stand.
