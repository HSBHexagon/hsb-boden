# DEPLOY_READINESS_GAP

Stand: 2026-06-11
Rolle: Release Engineer
Scope: Gap zwischen lokalem Review-HEAD `2369155` und einem deploy-/produktionsreifen Stand. Keine Website-Aenderungen, keine Commits, kein Push, kein Merge, kein Deployment, kein DNS.

## 1. Ausgangslage

Aktuelle Wahrheit aus den Projektquellen:

- Local Review HEAD: `2369155`
- Remote PR HEAD: `a591724`
- PR #5: Draft
- PR #5: `CONFLICTING`
- Canonical Review Worktree: `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review`
- Canonical Audit/Handoff-Ort: `docs/audit/`

`2369155` enthaelt die lokale Claude-Code-Arbeit Phase 1 + 2 plus Audit-Evidenz. Der Remote-PR-Branch enthaelt diese acht lokalen Commits noch nicht.

## 2. Was zwischen `2369155` und produktionsreif fehlt

### Remote-/PR-Promotion

- Die acht lokalen Commits muessen bewusst in den Remote-PR-Stand promoted werden, falls sie Teil des Release Candidates werden sollen.
- Solange Remote PR Head `a591724` ist, bildet PR #5 nicht den lokalen Endstand `2369155` ab.

### Merge-Stabilisierung

- PR #5 ist weiterhin konfliktig.
- Eine Merge-Simulation von `2369155` gegen `origin/main` meldet Content-Konflikte in 13 Dateien.
- 10 dieser Konfliktdateien wurden durch die acht lokalen Commits beruehrt.

### Frisches lokales Gate

Der Masterpiece-Audit dokumentiert gruene Gates waehrend der Claude-Arbeit. Fuer Release Readiness reicht das nicht als finale Freigabe.

Vor jedem Preview-Deploy nach Promotion/Conflict-Resolution fehlen frisch:

1. `npm run check`
2. `npm run test:run`
3. `npm run build`

Diese Befehle muessen nach dem finalen Merge-Prep-Stand laufen, nicht nur auf einem alten Zwischenstand.

### Eindeutige Preview-Verifikation

- Bekannte Preview: `https://hsb-boden-preview.cherinojoel.workers.dev/`
- Laut `PROJECT_CURRENT_STATE.md`: erreichbar, aber nicht eindeutig gegen `2369155` verifiziert.
- Es fehlt eine commit-nahe Preview-Verifikation, die beweist, dass die sichtbare Preview exakt den aktuellen HEAD ausliefert.

### PR-Status

- PR #5 ist Draft.
- PR #5 ist `CONFLICTING`.
- PR #5 darf erst nach Konfliktloesung, frischem Gate und Preview-Nachweis auf Ready gesetzt werden.

### Production-Go-Live

Produktionsreife ist mehr als Preview-Reife.

Vor Production fehlen weiterhin:

- explizite Freigabe fuer Domain/DNS/Cutover
- eindeutige Production-Route-Verifikation
- frische Browser-/HTTP-Verifikation eines Kernpfads
- Claim-/Rechtsfreigabe fuer produktionsrelevante Aussagen, besonders WHG, GMP/FDA, ISO 14644, pH 0-14 und DIN EN 14411
- Lead-Pipeline-/n8n-/SMTP-Entscheidung, falls Production direkt fuer Outreach genutzt werden soll

## 3. Aktuelle Blocker

| Blocker | Status | Bedeutung |
| --- | --- | --- |
| Remote PR Head != Local Review HEAD | offen | PR #5 bildet `2369155` nicht ab. |
| PR #5 Draft | offen | Nicht release-formal bereit. |
| PR #5 `CONFLICTING` | offen | Kein sauberer Merge in `main`. |
| Merge-Konflikte gegen `origin/main` | offen | 13 Content-Konfliktdateien in Merge-Simulation. |
| Worktree mit untracked Reports | offen | Promotion-Zustand ist dokumentarisch unaufgeraeumt, auch wenn die Commit-Spanne sauber ist. |
| Kein frisches finales Gate | offen | Audit-Gates sind Evidenz, aber keine finale Release-Verifikation. |
| Keine eindeutige Preview auf `2369155` | offen | Sichtbarer Stand kann nicht als Abnahmebasis gelten. |
| Kein Production-Cutover erlaubt | bewusst gesperrt | DNS/Domain/Production bleiben ausser Scope. |

## 4. Konfliktdateien vor Release

Merge-Simulation `2369155` gegen `origin/main` meldet Content-Konflikte in:

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

Diese Konflikte muessen vor Merge oder releasefaehiger PR manuell fachlich geloest werden.

## 5. Was vor einem Preview-Deploy erledigt werden muss

Preview-Deploy darf erst erfolgen, wenn klar ist, welcher Stand deployt wird.

Minimaler Pre-Preview-Pfad:

1. Entscheiden, ob die acht lokalen Commits in PR #5 promoted werden.
2. Worktree-Status bereinigen oder untracked Root-Reports bewusst aus dem Deploy-Kontext ausschliessen.
3. Falls Preview aus Remote-Branch gebaut wird: Remote-PR-Branch von `a591724` auf `2369155` bringen.
4. Falls Preview aus Merge-Prep gebaut wird: Konflikte vorher loesen und einen eindeutigen neuen HEAD erzeugen.
5. Frisches lokales Gate auf genau diesem HEAD:
   - `npm run check`
   - `npm run test:run`
   - `npm run build`
6. Keine Produktionsroute, kein DNS, kein Domain-Cutover.
7. Preview erst danach aktualisieren.
8. Nach Preview-Deploy verifizieren:
   - HTTP 200 auf Preview
   - sichtbare Marker aus `2369155`: technische Fachprosa, Reveal ohne Layoutbruch, Hero-Hexagon, Audit-Screenshots als Vergleichsbasis
   - Console ohne Errors
   - Mobile 390 und Desktop 1440 Sichtpruefung
   - Nachweis, dass die Preview dem deployten Commit entspricht

## 6. Empfehlung

Nicht direkt deployen.

Empfohlene Release-Vorbereitung:

1. `2369155` als lokalen Review-Endstand akzeptieren.
2. Die acht lokalen Commits als RC-Promotion-Bundle behandeln.
3. Vor Promotion ein frisches lokales Gate laufen lassen.
4. Danach Remote-PR auf `2369155` bringen oder einen separaten Merge-Prep-Branch erstellen.
5. Merge-Konflikte gegen `main` loesen.
6. Nach Konfliktloesung erneut Gate laufen lassen.
7. Erst dann Preview aktualisieren und eindeutig gegen HEAD verifizieren.

Produktionsreif ist der Stand erst nach erfolgreicher Preview-Verifikation, PR-Entdrafting, Konfliktloesung, finalem Gate und separater Go-Live-Freigabe.
