# PROJECT_CANONICAL_STRUCTURE

Stand: 2026-06-11
Rolle: Project Curator
Scope: Nur Struktur- und Quellenanalyse. Keine Website-Aenderungen, keine Commits, keine Deployments, keine Merges.

## 1. Single Source Of Truth

Die dauerhafte Projektwahrheit fuer HSB-Boden liegt im Review-Worktree unter:

`/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review/docs/audit/`

Jeder Agent beginnt dort. Chatverlaeufe sind keine Wahrheit.

Startreihenfolge fuer Agenten:

1. `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md`
2. `PROJECT_CANONICAL_STRUCTURE.md`
3. `PROJECT_CURRENT_STATE.md`
4. `RELEASE_CANDIDATE_STATUS.md`
5. `RELEASE_PATH.md`
6. `MERGE_RESOLUTION_PLAN.md`
7. Git-/PR-Zustand zur mechanischen Verifikation

Dokumente beschreiben Entscheidungen und Kontext. Git/PR beschreibt den tatsaechlichen technischen Zustand.

## 2. Kanonische Pfade

| Rolle | Kanonischer Wert |
| --- | --- |
| Canonical Repository | `https://github.com/cherinojoel-lang/hsb-boden.git` |
| Canonical Main Worktree | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` |
| Canonical Main Branch | `main` |
| Canonical Main HEAD | `d2d5e90` (`origin/main`, sauber) |
| Canonical Review Worktree | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review` |
| Canonical Review Branch | `claude/hsb-boden-architecture-o2479f` |
| Canonical Review HEAD lokal | `2369155` |
| Remote PR Head | `a591724` |
| PR | #5, Draft, offen, `CONFLICTING` |
| Canonical Audit Folder | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review/docs/audit/` |
| Canonical Handoff Folder | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review/docs/audit/` |

## 3. Nicht-kanonische Worktrees

| Pfad | Branch | Status | Einordnung |
| --- | --- | --- | --- |
| `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden/.worktrees/lead-pipeline-finalize` | `codex/lead-pipeline-finalize` | sauber | Zusatz-Worktree, nicht kanonisch. Erst nach Branch-Audit entfernen. |

## 4. Aktive Dokumente

Diese Dokumente bleiben aktiv oder entscheidungsrelevant:

- `PROJECT_CANONICAL_STRUCTURE.md` - Strukturwahrheit.
- `PROJECT_CURRENT_STATE.md` - kompakter aktueller Projektzustand.
- `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md` - aktueller abgeschlossener Endstand Phase 1+2, lokaler HEAD `2369155`.
- `RELEASE_CANDIDATE_STATUS.md` - No-Go/RC-Status; fachlich aktiv, aber HEAD-Feld nennt noch Remote-PR-Head `a591724` und muss beim naechsten Status-Refresh auf `2369155` aktualisiert werden.
- `RELEASE_PATH.md` - Reihenfolge fuer RC-Stabilisierung.
- `MERGE_RESOLUTION_PLAN.md` - Konfliktloesungsstrategie.
- `BRANCH_DELTA_REPORT.md` - Branch-/PR-Differenz gegen `main`.
- `FINAL_RELEASE_AUDIT.md` - Release-Audit/No-Go-Bewertung; ebenfalls vor naechster Freigabe gegen `2369155` refreshen.
- `docs/audit/screenshots/` - visuelle Evidenz aus dem Masterpiece-Audit.
- `docs/launch/referenzen-freigabe.md` - Freigabe-/Referenzkontext.
- `ops/n8n/README.md` und `ops/n8n/README-runbook.md` - Lead-Pipeline-Betriebskontext.

## 5. Doppelte Dokumente

Exakte Duplikate ueber `hsb-boden`, `hsb-boden-review` und den Zusatz-Worktree:

- `README.md`
- `docs/audit/current-state.md`
- `docs/competitors/benchmark.md`
- `docs/content-briefs/landingpages.md`
- `docs/launch/checklist.md`
- `docs/superpowers/plans/2026-06-06-hsb-go-live.md`
- `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`
- `ops/n8n/README.md`
- `ops/n8n/README-runbook.md`

Exakte Duplikate zwischen Main- und Review-Worktree:

- `docs/superpowers/plans/2026-06-10-hexafloor-abgleich.md`
- `docs/superpowers/plans/2026-06-11-hsb-full-site-review.md`

Inhaltlich konkurrierende Status-/Handoff-Dokumente im Review-Worktree:

- `CURRENT_EXECUTION_STATE.md`
- `FINAL_HANDOFF.md`
- `FINAL_WEBSITE_ACCEPTANCE.md`
- `FINAL_WEBSITE_COMPLETION_TASKS.md`
- `NEXT_CRITICAL_PATH.md`
- `WEBSITE_FINALIZATION_AUDIT.md`
- `WEBSITE_FINALIZATION_TASKS.md`
- `WEBSITE_FINAL_IMPLEMENTATION_REPORT.md`
- `VISUAL_RELEASE_VERIFICATION.md`
- `DEPLOYMENT_BLOCKER_REPORT.md`
- `WEBSITE_PRODUCTION_CONFIRMATION.md`

Diese Dateien duerfen nicht mehr als Primaerwahrheit verwendet werden, weil sie teils "ready/go-live" behaupten, waehrend PR #5 weiterhin Draft/konfliktig ist und die Preview nicht eindeutig den aktuellen HEAD belegt.

## 6. Veraltete Dokumente

Als historisch oder ueberholt einordnen:

- `docs/audit/current-state.md` - alter Basiszustand vom 2026-06-03.
- `docs/superpowers/plans/2026-06-06-hsb-go-live.md` - durch spaetere RC-/Audit-Dokumente ueberholt.
- `docs/superpowers/plans/2026-06-07-hsb-masterplan-golive.md` - historischer Go-Live-Plan, nicht aktueller RC-Pfad.
- `docs/superpowers/plans/2026-06-07-home-design-final-pass.md` und `docs/superpowers/specs/2026-06-07-home-design-final-pass.md` - abgeschlossene Designhistorie.
- `FINAL_HANDOFF.md` - nennt `ab2b5d2` und "einsatzbereit"; ueberholt durch `2369155` plus No-Go/PR-Konflikt.
- `CURRENT_EXECUTION_STATE.md` - behauptet hohe Fertigstellung, aber nicht die aktuelle PR-/Preview-Blockade als fuehrende Wahrheit.
- `DEPLOYMENT_BLOCKER_REPORT.md` und `WEBSITE_PRODUCTION_CONFIRMATION.md` - widerspruechliche Infrastruktur-Snapshots; nur als Verlauf lesen, nicht als Status.

## 7. Archivieren

Nach expliziter Freigabe archivieren, nicht sofort loeschen:

- Root-Statusfragmente im Review-Worktree: `CURRENT_EXECUTION_STATE.md`, `FINAL_HANDOFF.md`, `FINAL_WEBSITE_*`, `WEBSITE_FINALIZATION_*`, `P0_EXECUTION_REPORT.md`, `PROJECT_REALITY_CHECK.md`, `RECOVERY_EXECUTION_PLAN.md`, `NEXT_CRITICAL_PATH.md`, `LANGUAGE_STRATEGY_REVIEW.md`, `VISUAL_RELEASE_VERIFICATION.md`.
- Alte Planstufen in `docs/superpowers/plans/` nach Abschluss der RC-Stabilisierung.
- Nicht-kanonischen Worktree `.worktrees/lead-pipeline-finalize` erst nach Branch-Audit.

Empfohlenes Archivziel nach Freigabe:

`/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review/docs/audit/archive/`

## 8. Loeschbar

Nur nach expliziter Freigabe und nur wenn keine laufende lokale Pruefung darauf zugreift:

- generierte Build-/Cache-Ordner: `dist/`, `.astro/`, `.wrangler/tmp/`
- lokale Abhaengigkeiten: `node_modules/` (regenerierbar ueber `npm install`)
- der Zusatz-Worktree `.worktrees/lead-pipeline-finalize`, falls sein Branch als nicht mehr benoetigt bestaetigt wurde

Keine fachlichen Berichte loeschen, bevor sie archiviert oder in `docs/audit/` konsolidiert wurden.

## 9. Erhalten

Muss erhalten bleiben:

- `hsb-boden` als sauberer `main`-Worktree.
- `hsb-boden-review` als einziger Review-/RC-Worktree.
- `docs/audit/` als einziger Audit- und Handoff-Ort.
- `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md`.
- `PROJECT_CURRENT_STATE.md`.
- `RELEASE_PATH.md`, `MERGE_RESOLUTION_PLAN.md`, `RELEASE_CANDIDATE_STATUS.md`, `BRANCH_DELTA_REPORT.md`, `FINAL_RELEASE_AUDIT.md` bis zur naechsten konsolidierten Audit-Version.
- alle freigegebenen Assets, Content-Daten, Tests und n8n-Runbooks.

## 10. Naechster sicherer Schritt

Nicht deployen, nicht mergen, nicht DNS anfassen.

Naechster Schritt ist RC-Stabilisierung:

1. Lokale Statusdokumente fuer `2369155` konsolidieren.
2. Konflikte gegen `main` in einem separaten Merge-Prep-Stand loesen.
3. `npm run check`, `npm run test:run`, `npm run build` ausfuehren.
4. Erst nach gruenem Gate und expliziter Freigabe Preview aktualisieren.
5. Preview gegen den dann aktuellen HEAD verifizieren.
