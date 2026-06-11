# Vollständiger Site-Review & Optimierungsplan (HSB Hexagon Säurebau, Preview) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jede Seite der hsb-boden-Website gegen die bestehenden Checklisten-Dokumente abgleichen, alle vorgeschlagenen Optimierungen verifizieren und risikofreie Punkte umsetzen — Ergebnis: auditierter „Meisterwerk"-Stand auf der PR-#5-Branch-Preview.

**Architecture:** Read-only-Audit (Phase A) → visuelle Browser-QA (Phase B) → verifiziertes Backlog (Phase C) → minimal-invasive Umsetzung mit Gate je Schritt (Phase D) → Abschluss-Gate + Reporting (Phase E). Alle Arbeit findet in einem Git-Worktree auf dem Branch `claude/hsb-boden-architecture-o2479f` (PR #5, draft) statt.

**Tech Stack:** Astro 5, Cloudflare Workers, Vitest, Playwright/Lighthouse (QA), `gh` CLI.

---

## Verifizierter Ist-Zustand (Stand 2026-06-11, nicht raten — gilt als Faktenbasis)

- Lokales Repo `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` steht auf `main` mit **staged, uncommitteten Änderungen in 17 Dateien** (Design-Politur, u. a. `src/pages/index.astro`, `src/styles/global.css`). **Diese NICHT anfassen, nicht committen, nicht verwerfen** — sie gehören einer anderen Session.
- PR #5 (draft, OPEN): „Mehrsprachigkeit (6 Sprachen) + Cookie-Consent + reale Projektfotos + Ton-Feinschliff", Branch `claude/hsb-boden-architecture-o2479f` — existiert **nur remote** (`origin/claude/hsb-boden-architecture-o2479f`).
- Auf dem PR-Branch existieren (auf `main` NICHT): `docs/launch/referenzen-freigabe.md`, `src/data/clientLocations.ts`, `src/lib/i18n.ts`, Sprachordner `src/pages/{en,fr,nl,pl,tr}/`, 12 WebP-Fotos in `public/media/hsb/projekte/`.
- Hero-Bild auf der Startseite (PR-Branch, `src/pages/index.astro` ~Zeile 42–52) hat **bereits** `srcset`, `sizes`, `fetchpriority="high"`, `width`/`height` — es fehlen nur ggf. `loading="eager"` und `decoding="async"`.
- `pharma-hessen`: laut `docs/launch/referenzen-freigabe.md` §1 bewusst anonymisiert („kein eindeutiger Treffer in der Liste"). Default dieses Plans: Status unverändert lassen, nur erneut gegen die Liste sichten.
- npm-Scripts: `check` = `astro check --js-only`, `test:run` = `vitest run`, `build` = `astro build`.
- Gate-Befehl (nach jeder Code-/Content-Änderung): `npm run check && npm run test:run && npm run build`
- seo-content-reviewer-Agent: definiert in `.claude/agents/seo-content-reviewer.md` (auf `main`; im Worktree via `--agents`-Verfügbarkeit identisch, da User-Level-Agents global laden — falls nicht auffindbar, Datei aus `main` lesen und Prompt manuell als Subagent-Auftrag verwenden).

## Leitplanken (gelten für JEDE Task)

1. **PR #2 bleibt unmerged**; nichts tun, was `hsb-boden.de` produktiv übernimmt. Kein `npm run deploy:production`.
2. Keine erfundenen Zahlen/Statistiken/Claims; keine neuen Kundennamen/Logos ohne die Freigabelogik aus `docs/launch/referenzen-freigabe.md` §0.
3. Keine Fremd-/Maschinenlogos auf neuen Fotos (KLINGER-Regel — Fotos mit erkennbaren Fremdlogos sind tabu).
4. GA4, SMTP/Formularversand, n8n, juristische Prüfung: **out of scope**, nicht anfassen, nicht „mit erledigen".
5. Nur bestehende Patterns/Komponenten wiederverwenden; kein neues Abstraktions-Layer für einmalige Anpassungen.
6. Die staged Änderungen auf `main` im Haupt-Checkout nicht berühren.

---

### Task 0: Preflight — Worktree auf PR-Branch + Baseline-Gate

**Files:**
- Create: Worktree `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review` (Branch `claude/hsb-boden-architecture-o2479f`)
- Copy: dieses Plan-Dokument in den Worktree

- [ ] **Step 1: Worktree anlegen (Haupt-Checkout bleibt unberührt auf `main`)**

```bash
cd /Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden
git fetch origin
git worktree add ../hsb-boden-review claude/hsb-boden-architecture-o2479f
```

Erwartung: Worktree erstellt, Branch trackt `origin/claude/hsb-boden-architecture-o2479f`. Falls „already exists" → vorhandenen Worktree prüfen (`git worktree list`) und weiterverwenden, sofern er auf demselben Branch steht und clean ist.

- [ ] **Step 2: Dependencies installieren**

```bash
cd /Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review
npm install
```

- [ ] **Step 3: Baseline-Gate laufen lassen (muss VOR jeder Änderung grün sein)**

```bash
npm run check && npm run test:run && npm run build
```

Erwartung: check 0 errors, alle Tests grün, Build erfolgreich. Falls rot: STOPP — Befund dokumentieren und an den Nutzer berichten, nicht „nebenbei fixen".

- [ ] **Step 4: Plan-Dokument in den Worktree übernehmen und committen**

```bash
cp /Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden/docs/superpowers/plans/2026-06-11-hsb-full-site-review.md docs/superpowers/plans/
git add docs/superpowers/plans/2026-06-11-hsb-full-site-review.md
git commit -m "docs(plan): Full-Site-Review-Plan 2026-06-11"
```

---

### Task 1: Statusmatrix aus den Planungsdokumenten konsolidieren (Read-only)

**Files:**
- Read: `docs/launch/checklist.md`, `docs/launch/referenzen-freigabe.md`, `docs/audit/current-state.md`, `docs/superpowers/plans/2026-06-06-hsb-go-live.md`, `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`, `docs/superpowers/plans/2026-06-07-hsb-masterplan-golive.md`, `docs/superpowers/plans/2026-06-10-hexafloor-abgleich.md` (alle im Worktree)
- Create: `docs/audit/2026-06-10-full-review-status.md`

- [ ] **Step 1: Alle 7 Dokumente lesen** (vollständig, nicht nur Überschriften — offene Punkte je Dokument extrahieren).

- [ ] **Step 2: Audit-Datei mit Statusmatrix anlegen**

Struktur der neuen Datei `docs/audit/2026-06-10-full-review-status.md`:

```markdown
# Full-Site-Review Status (erstellt 2026-06-11, Branch claude/hsb-boden-architecture-o2479f)

## 1. Statusmatrix (konsolidiert aus Planungsdokumenten)

| Bereich | Status | Offene Punkte | Quelle |
|---|---|---|---|
| ... | ... | ... | checklist.md / referenzen-freigabe.md / ... |

## 2. Routenliste (siehe Task 2)

## 3. Pro-Seite-Findings (siehe Task 3)

| Seite | Befund | Schweregrad (hoch/mittel/niedrig) | Vorschlag |
|---|---|---|---|

## 4. Visuelle QA (siehe Task 4)

## 5. Optimierungsbacklog (siehe Task 5)

## 6. Endergebnis (siehe Task 7)
```

Die Matrix in Abschnitt 1 vollständig befüllen. Out-of-scope-Punkte (GA4/SMTP/n8n/rechtlich) explizit als „out of scope, siehe Masterplan" kennzeichnen, NICHT als offen-für-diese-Session.

- [ ] **Step 3: Commit**

```bash
git add docs/audit/2026-06-10-full-review-status.md
git commit -m "docs(audit): Statusmatrix aus Planungsdokumenten konsolidiert"
```

---

### Task 2: Vollständige Routenliste erzeugen

**Files:**
- Read: `src/pages/sitemap.xml.ts`
- Modify: `docs/audit/2026-06-10-full-review-status.md` (Abschnitt 2)

- [ ] **Step 1: Sitemap-Logik lesen** (`src/pages/sitemap.xml.ts`) — verstehen, welche Routen sie aufnimmt (inkl. Sprachvarianten?).

- [ ] **Step 2: URL-Liste aus dem Build-Output extrahieren** (Build existiert aus Task 0 Step 3)

```bash
grep -o '<loc>[^<]*</loc>' dist/client/sitemap.xml 2>/dev/null | sed 's/<\/\?loc>//g' | sort
# Falls dist/client/sitemap.xml nicht existiert (SSR-Route): stattdessen alle Seiten-Routen aus dem Quellbaum ableiten:
find src/pages -name "*.astro" -o -name "*.ts" | sort
```

Bei `getStaticPaths()`-Slugs ([slug].astro für branchen/leistungen/wissen/referenzen): Slugs aus `src/data/industries.ts`, `src/data/services.ts`, `src/data/articles.ts`, `src/data/references.ts` auslesen.

- [ ] **Step 3: Routenliste in Abschnitt 2 der Audit-Datei eintragen** — gruppiert: DE-Kernseiten / Branchen / Leistungen / Wissen / Referenzen / Sprachvarianten (en, fr, nl, pl, tr) / Sonstige (robots, sitemap). Abgleich: Tauchen alle Seiten in der Sitemap auf? Fehlende notieren.

- [ ] **Step 4: Commit**

```bash
git add docs/audit/2026-06-10-full-review-status.md
git commit -m "docs(audit): vollstaendige Routenliste + Sitemap-Abgleich"
```

---

### Task 3: Pro-Seite Content-Audit (parallelisierte Read-only-Agents)

**Files:**
- Read: alle Seiten-/Daten-Dateien (durch Agents)
- Modify: `docs/audit/2026-06-10-full-review-status.md` (Abschnitt 3)

- [ ] **Step 1: 4 parallele Explore-/general-purpose-Agents dispatchen** (ein Aufruf, 4 Agents — Bereiche: Branchen / Leistungen / Wissen / Sonstige+Sprachvarianten). Jeder Agent bekommt denselben Prüfkatalog und seinen Dateibereich:

Prüfkatalog (wörtlich in jeden Agent-Prompt):
1. H1 vorhanden & einzigartig je Seite; `seoTitle`/`description` vorhanden UND inhaltlich sinnvoll (nicht nur Zod-Mindestlänge — Stichprobe auf Aussagekraft).
2. Bilder: `alt`-Text vorhanden, beschreibend, kein Hinweis auf Fremdlogo im Bild (Dateiname/alt prüfen; KLINGER-Regel).
3. Interne Links: Cross-Links Branche↔Leistung↔Wissen vorhanden oder fehlend (Felder `relatedServices`/`relatedReferences` o. ä. in `src/data/*.ts` + Fließtext-Links).
4. Nur Bereich „Sonstige": Sprachvarianten `/en/ /fr/ /nl/ /pl/ /tr/` — Platzhalter-Qualität vs. vollwertiger Content, hreflang-Konsistenz (in `src/components/seo/SEOHead.astro` bzw. `src/lib/i18n.ts`).

Output-Format je Agent (wörtlich vorgeben): Markdown-Tabelle `| Seite | Befund | Schweregrad | Vorschlag |` — nur echte Befunde, kein „alles ok"-Rauschen außer einer Sammelzeile pro geprüftem Bereich.

Dateibereich je Agent:
- Branchen: `src/pages/branchen/`, `src/data/industries.ts`
- Leistungen: `src/pages/leistungen/`, `src/data/services.ts`
- Wissen: `src/pages/wissen/`, `src/data/articles.ts`
- Sonstige: `src/pages/{index.astro,referenzen,kontakt,karriere,impressum,datenschutz,danke-projektanfrage.astro}`, `src/pages/{en,fr,nl,pl,tr}/`, `src/data/{references.ts,clientLocations.ts}`, `src/components/seo/SEOHead.astro`, `src/lib/i18n.ts`

- [ ] **Step 2: Ergebnisse konsolidieren** — Tabellen der 4 Agents in Abschnitt 3 der Audit-Datei zusammenführen, Duplikate mergen, Schweregrade vereinheitlichen.

- [ ] **Step 3: Commit**

```bash
git add docs/audit/2026-06-10-full-review-status.md
git commit -m "docs(audit): Pro-Seite-Findings aus parallelem Content-Audit"
```

---

### Task 4: Visuelle/Design-QA im Browser + Lighthouse

**Files:**
- Modify: `docs/audit/2026-06-10-full-review-status.md` (Abschnitt 4)
- Create: Screenshots unter `/tmp/hsb-review/` (NICHT ins Repo committen)

- [ ] **Step 1: Branch-Preview-URL ermitteln**

```bash
gh pr view 5 --repo cherinojoel-lang/hsb-boden --comments | grep -oE 'https://[a-z0-9.-]+\.workers\.dev[^ )"]*' | tail -5
```

Fallback, falls kein Webhook-Kommentar: `https://hsb-boden-preview.cherinojoel.workers.dev` verwenden — aber dann in der Audit-Datei vermerken, dass dies ggf. NICHT den PR-#5-Stand zeigt (Stand prüfen: Seite muss Sprachumschalter/6 Sprachen + Foto-Galerie auf /referenzen/ enthalten; wenn nicht → Preview ist stale, visuelles QA-Ergebnis entsprechend kennzeichnen und optional `npm run deploy:preview` NUR nach explizitem Check, dass das Preview-Worker-Target nicht die Produktiv-Domain ist — im Zweifel überspringen und als blockiert dokumentieren).

- [ ] **Step 2: Screenshots erstellen** (Playwright-MCP oder CLI; Auswahl: Startseite, 1 Branchenseite, 1 Leistungsseite, 1 Wissensseite, `/referenzen/`, `/kontakt/`, 1 Sprachvariante z. B. `/en/`)

```bash
mkdir -p /tmp/hsb-review
# je Seite, Desktop 1440 und Mobile 390 (Playwright-MCP: browser_navigate + browser_resize + browser_take_screenshot,
# oder CLI:)
npx playwright screenshot --viewport-size=1440,900 "$PREVIEW_URL/" /tmp/hsb-review/home-1440.png
npx playwright screenshot --viewport-size=390,844  "$PREVIEW_URL/" /tmp/hsb-review/home-390.png
```

- [ ] **Step 3: Screenshots visuell prüfen** (jede Datei mit Read ansehen): Layoutbrüche, abgeschnittene Bilder/Texte, Kontrast/Lesbarkeit, Konsistenz Abstände/Typografie zwischen Seitentypen, korrekte Darstellung der Referenzkarte (21 Kundenstandorte) und der Foto-Galerie auf `/referenzen/`. Befunde in Abschnitt 4 eintragen.

- [ ] **Step 4: Lighthouse für 3 Seiten** (Startseite, 1 Branchenseite, `/referenzen/`)

```bash
npx lighthouse "$PREVIEW_URL/" --quiet --chrome-flags="--headless" --output=json --output-path=/tmp/hsb-review/lh-home.json
python3 -c "import json; d=json.load(open('/tmp/hsb-review/lh-home.json')); print({k: round(v['score']*100) for k,v in d['categories'].items()})"
```

Scores (Performance/Accessibility/Best-Practices/SEO) als Zahlen in Abschnitt 4 notieren — keine Performance-Aussagen ohne diese Messwerte (mistakes.md-Regel).

- [ ] **Step 5: Commit**

```bash
git add docs/audit/2026-06-10-full-review-status.md
git commit -m "docs(audit): visuelle QA + Lighthouse-Scores"
```

---

### Task 5: Optimierungsbacklog verifizieren & priorisieren

**Files:**
- Read: `src/pages/index.astro`, `src/components/sections/PageHero.astro`, `src/lib/seo.ts`, `src/components/seo/SEOHead.astro`, `src/data/{industries,services,articles}.ts`, `src/pages/branchen/[slug].astro`, `src/pages/leistungen/[slug].astro`, `src/pages/sitemap.xml.ts`, `src/pages/robots.txt.ts`, `src/data/clientLocations.ts`, `docs/launch/referenzen-freigabe.md`
- Modify: `docs/audit/2026-06-10-full-review-status.md` (Abschnitt 5)

- [ ] **Step 1: Backlog-Tabelle in Abschnitt 5 anlegen und je Kandidat den IST-Stand im Code verifizieren** (Datei + Zeilennummer notieren):

| Kandidat | Verifizieren anhand | Vorab-Einordnung |
|---|---|---|
| Hero `loading="eager"`/`decoding="async"` (srcset+fetchpriority sind BEREITS da) | `src/pages/index.astro` ~Z. 42–52; zusätzlich `PageHero.astro` auf Unterseiten prüfen | Quick Win (nur falls Attribute fehlen) |
| OG-Image vorhanden/aktuell | `src/lib/seo.ts` + `src/components/seo/SEOHead.astro`, OG-Asset-Pfade in `public/` | Quick Win (nur falls Lücke) |
| Interne Verlinkung Branchen↔Leistungen↔Wissen | `src/data/{industries,services,articles}.ts`: vorhandene related-Felder + Fließtext | Quick Win |
| Leistungs-Bildslot (analog `industryImages` in `branchen/[slug].astro`) | Foto-Nutzung prüfen: `for f in public/media/hsb/projekte/*.webp; do n=$(basename $f); grep -rl "$n" src/ >/dev/null || echo "UNGENUTZT: $n"; done` | Bedingt — nur mit ungenutzten, logo-freien Fotos |
| Sitemap/robots Re-Check | `src/pages/sitemap.xml.ts`, `src/pages/robots.txt.ts` + Build-Output | Quick Win (Verifikation) |
| srcset für die neuen Projekt-WebPs | Bildbreiten prüfen (`sips -g pixelWidth public/media/hsb/projekte/*.webp`); zusätzliche Breiten via sharp nur bei Bedarf | Mittel |
| Echte Markenlogos statt Wordmark-SVGs | — | Blockiert (Kundenlieferung), zurückstellen |
| pharma-hessen erneut gegen Kundenliste | `src/data/clientLocations.ts` + `referenzen-freigabe.md` §1 (Stand: bewusst anonymisiert) | Quick Win (Recherche, Default: unverändert) |
| GA4/SMTP/n8n/rechtlich | — | Out of scope |

- [ ] **Step 2: Für jeden Quick-Win/Mittel-Punkt die konkrete minimal-invasive Änderung festlegen** (Datei + exakte Stelle + neuer Code), in die Tabelle eintragen. Punkte, deren Verifikation „bereits erledigt" ergibt, als solche markieren — NICHT trotzdem ändern.

- [ ] **Step 3: Commit**

```bash
git add docs/audit/2026-06-10-full-review-status.md
git commit -m "docs(audit): Optimierungsbacklog verifiziert und priorisiert"
```

---

### Task 6: Umsetzung — Hero-Performance (nur falls Task 5 Lücke ergab)

**Files:**
- Modify: `src/pages/index.astro` (~Z. 42–52), ggf. `src/components/sections/PageHero.astro`

- [ ] **Step 1: Attribute ergänzen, falls fehlend** — am bestehenden `<img>` NUR ergänzen, nichts umbauen:

```html
<img
  src="/media/hsb/current/industrieboden-baustelle.webp"
  srcset="/media/hsb/current/industrieboden-baustelle-640.webp 640w, /media/hsb/current/industrieboden-baustelle.webp 1024w"
  sizes="(min-width: 1024px) 50vw, 100vw"
  alt="Keramischer Industrieboden mit Entwässerungsrinne und Hexagon-Verlegung in Produktionshalle"
  class="absolute inset-0 h-full w-full object-cover object-center"
  style="opacity:0.72"
  fetchpriority="high"
  loading="eager"
  decoding="async"
  width="1024"
  height="768"
/>
```

In `PageHero.astro` analog: above-the-fold-Bild → `loading="eager"` + `fetchpriority="high"`; falls dort `loading="lazy"` gesetzt ist, korrigieren.

- [ ] **Step 2: Gate**

```bash
npm run check && npm run test:run && npm run build
```

Erwartung: 0 errors, Tests grün, Build ok.

- [ ] **Step 3: Commit**

```bash
git add src/pages/index.astro src/components/sections/PageHero.astro
git commit -m "perf(hero): eager loading + async decoding fuer Above-the-fold-Bilder"
```

(Falls Task 5 ergab: alles bereits vorhanden → Task überspringen, in Audit-Datei als „bereits erledigt" markieren.)

---

### Task 7: Umsetzung — OG-Image (nur falls Task 5 Lücke ergab)

**Files:**
- Modify: `src/lib/seo.ts` und/oder `src/components/seo/SEOHead.astro`

- [ ] **Step 1: Befund aus Task 5 umsetzen** — falls OG-Image fehlt oder auf ein veraltetes/generisches Asset zeigt: auf ein existierendes, repräsentatives Asset umstellen (z. B. das Hero-Bild `public/media/hsb/current/industrieboden-baustelle.webp` oder ein dediziertes OG-Asset, falls vorhanden). KEIN neues Bild generieren. Absolute URL verwenden (og:image braucht absolute URLs — Site-URL aus `src/data/site.ts` bzw. `astro.config` beziehen, vorhandenes Muster in `SEOHead.astro` wiederverwenden).

- [ ] **Step 2: Gate + Verifikation im Build-Output**

```bash
npm run check && npm run test:run && npm run build
grep -o '<meta property="og:image"[^>]*>' dist/client/index.html 2>/dev/null || grep -ro 'og:image' dist/ | head -3
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/seo.ts src/components/seo/SEOHead.astro
git commit -m "seo(og): OG-Image auf aktuelles Asset gesetzt"
```

---

### Task 8: Umsetzung — Interne Cross-Links Branchen↔Leistungen↔Wissen

**Files:**
- Modify: `src/data/industries.ts`, `src/data/services.ts`, `src/data/articles.ts` (nur Daten/Fließtext — KEINE neuen Komponenten)

- [ ] **Step 1: Fehlende Cross-Links aus Task-3/5-Findings ergänzen** — vorhandene related-Felder (z. B. `relatedServices`, `relatedReferences`) befüllen bzw. im Fließtext (`intro`/`body`-Felder) mit dem bestehenden Link-Pattern verlinken (vorher 1 Beispiel eines existierenden Fließtext-Links in den Daten suchen und exakt dieses Markup-Muster kopieren). Nur sachlich korrekte Verknüpfungen (Branche nutzt Leistung wirklich); nichts erfinden.

- [ ] **Step 2: seo-content-reviewer-Agent über die geänderten Texte laufen lassen** — PASS erforderlich; bei FAIL nachbessern und erneut prüfen (gleiches Vorgehen wie bei den 4 Referenztexten der Vorsession).

- [ ] **Step 3: Gate**

```bash
npm run check && npm run test:run && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add src/data/industries.ts src/data/services.ts src/data/articles.ts
git commit -m "content(links): interne Cross-Links Branchen/Leistungen/Wissen ergaenzt"
```

---

### Task 9: pharma-hessen erneut gegen Kundenliste abgleichen

**Files:**
- Read: `src/data/clientLocations.ts`, `src/data/references.ts`, `docs/launch/referenzen-freigabe.md`
- Modify (nur bei eindeutigem Treffer): `src/data/references.ts`, `docs/launch/referenzen-freigabe.md`

- [ ] **Step 1: Abgleich** — Einträge der „Referenzprojekte 2025"-Liste (dokumentiert in `referenzen-freigabe.md` / `clientLocations.ts`) auf einen eindeutigen Pharma-Kunden in Hessen sichten.

- [ ] **Step 2a (Default, kein eindeutiger Treffer):** Status unverändert lassen; in der Audit-Datei vermerken: „pharma-hessen erneut geprüft am 2026-06-11, weiterhin kein eindeutiger Treffer, bleibt anonymisiert."

- [ ] **Step 2b (nur bei eindeutigem Treffer):** Gleiches Vorgehen wie bei den 4 freigegebenen Referenzen (referenzen-freigabe.md §0/§1): `publicName` + Ort in `src/data/references.ts` setzen, Tabelle in `referenzen-freigabe.md` aktualisieren, seo-content-reviewer (PASS), dann:

```bash
npm run check && npm run test:run && npm run build
git add src/data/references.ts docs/launch/referenzen-freigabe.md
git commit -m "content(referenzen): pharma-hessen per Kundenliste freigegeben"
```

---

### Task 10: Leistungs-Bildslot (NUR falls Task 5 ungenutzte, logo-freie Fotos ergab)

**Files:**
- Modify: `src/pages/leistungen/[slug].astro`, `src/data/services.ts`

- [ ] **Step 1: Bestehendes Branchen-Pattern lesen** — `industryImages`-Mechanik in `src/pages/branchen/[slug].astro` exakt nachvollziehen (Datenstruktur, Markup, alt-Texte).

- [ ] **Step 2: Identisches Pattern für Leistungsseiten replizieren** — gleiche Feldstruktur in `src/data/services.ts` (z. B. `serviceImages` analog `industryImages`), gleiches Markup in `leistungen/[slug].astro`. KEINE neue Komponente, KEINE Abstraktion über beide Seitentypen. Nur die in Task 5 als ungenutzt UND logo-frei verifizierten Fotos aus `public/media/hsb/projekte/` verwenden; jedes Foto vor Verwendung per Read ansehen (KLINGER-Regel: erkennbare Fremd-/Maschinenlogos → Foto nicht verwenden). Beschreibende deutsche alt-Texte.

- [ ] **Step 3: Gate + Commit**

```bash
npm run check && npm run test:run && npm run build
git add src/pages/leistungen/[slug].astro src/data/services.ts
git commit -m "feat(leistungen): Bildslot mit ungenutzten Projektfotos (analog Branchen-Pattern)"
```

(Falls keine geeigneten Fotos: Task überspringen, in Audit-Datei als „zurückgestellt — keine ungenutzten logo-freien Fotos" markieren.)

---

### Task 11: Sitemap/robots final verifizieren

**Files:**
- Read: `src/pages/sitemap.xml.ts`, `src/pages/robots.txt.ts`, Build-Output

- [ ] **Step 1: Frischer Build + Stichprobe**

```bash
npm run build
# Sitemap: enthalten alle Routen aus Task 2 (inkl. Sprachvarianten)? Keine 404-Kandidaten?
grep -c '<loc>' dist/client/sitemap.xml 2>/dev/null || echo "sitemap ist SSR-Route — per Preview-URL pruefen: curl -s $PREVIEW_URL/sitemap.xml | grep -c '<loc>'"
# robots: verweist auf sitemap, blockiert nichts Wichtiges?
cat dist/client/robots.txt 2>/dev/null || curl -s "$PREVIEW_URL/robots.txt"
```

- [ ] **Step 2: Abweichungen fixen (nur falls vorhanden), Gate, Commit; sonst nur Audit-Datei-Vermerk** „Sitemap/robots verifiziert, N URLs, konsistent".

---

### Task 12: Abschluss — Gate, Re-Screenshots, Audit-Endstand, Push, Bericht

**Files:**
- Modify: `docs/audit/2026-06-10-full-review-status.md` (Abschnitt 6)

- [ ] **Step 1: Vollständiges Gate**

```bash
npm run check && npm run test:run && npm run build
```

Erwartung: check 0 errors / 0 warnings, alle Tests grün, Build erfolgreich. Zahlen notieren.

- [ ] **Step 2: Audit-Datei Abschnitt 6 befüllen** — je Backlog-Punkt: erledigt / zurückgestellt (Grund) / blockiert (Grund) / out of scope.

- [ ] **Step 3: Commit + Push auf den PR-Branch**

```bash
git add -A docs/ && git status --short   # NUR erwartete Dateien staged? Sonst korrigieren.
git commit -m "docs(audit): Full-Site-Review Endstand 2026-06-11"
git push origin claude/hsb-boden-architecture-o2479f
```

PR #5 aktualisiert sich automatisch. KEIN Merge, PR bleibt draft.

- [ ] **Step 4: Cloudflare-Deploy abwarten und geänderte Seiten re-screenshotten** — Webhook-Kommentar am PR abwarten (`gh pr view 5 --comments`, ggf. 2–3 Min warten), dann Task-4-Screenshots NUR für tatsächlich geänderte Seiten wiederholen und visuell gegenprüfen. Befund in Audit-Datei nachtragen (kleiner Folge-Commit + Push ok).

- [ ] **Step 5: Abschlussbericht an den Nutzer** — Tabelle: erledigt / zurückgestellt (Grund) / blockiert (Grund, z. B. fehlende Logo-Lieferung; GA4/SMTP/n8n/rechtlich = out of scope), plus Gate-Zahlen und Lighthouse-Scores (vorher/nachher falls beides gemessen).

- [ ] **Step 6: Shared Memory aktualisieren** — `ai-state event --tool claude --type step --msg "hsb-boden Full-Site-Review abgeschlossen (PR #5)"` und `ai-state checkpoint --tool claude --task "hsb full-site-review" --status completed`; Worktree stehen lassen (Aufräumen nur nach User-OK).
