# PROJECT_CURRENT_STATE

Stand: 2026-06-11
Projekt: HSB-Boden / HEXAFLOOR
Quelle: lokale Projektquellen, Git, PR-Status. Chatverlaeufe ignorieren.

## Aktueller Branch

`claude/hsb-boden-architecture-o2479f`

## Aktueller Commit

Lokaler Review-HEAD:

`2369155` - `docs(audit): Masterpiece SOTA Phase 1+2 Umsetzungsbericht + visuelle QA`

Remote-PR-HEAD:

`a591724`

Wichtig: Der lokale Review-Branch ist 8 Commits vor `origin/claude/hsb-boden-architecture-o2479f`.

## Aktuelle Worktrees

| Rolle | Pfad | Branch | Status |
| --- | --- | --- | --- |
| Main | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` | `main` | sauber, `d2d5e90`, synchron mit `origin/main` |
| Review | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review` | `claude/hsb-boden-architecture-o2479f` | lokaler HEAD `2369155`, 8 Commits vor Remote |
| Zusatz | `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden/.worktrees/lead-pipeline-finalize` | `codex/lead-pipeline-finalize` | sauber, nicht kanonisch |

## Aktuelle Preview

Bekannte Preview:

`https://hsb-boden-preview.cherinojoel.workers.dev/`

Status aus den Projektquellen: erreichbar, aber nicht eindeutig gegen den aktuellen Branch-HEAD verifiziert. Die bestehenden RC-Statusdateien beziehen sich noch auf `a591724`; fuer `2369155` fehlt eine deployte, eindeutig commit-nahe Preview-Verifikation.

Produktionsdomain:

`https://hsb-boden.de/`

Status aus den Projektquellen: kein freigegebener Produktions-Cutover. Domain/DNS/WordPress nicht anfassen.

## Letzte abgeschlossene Phase

`docs/audit/2026-06-11-masterpiece-sota-phase1-2.md`

Abgeschlossen:

- Phase 1 Content-Hardening.
- Phase 2 High-End-Motion-Polish.
- 7 lokale Commits von `a591724` bis `f300873`; aktueller lokaler Endstand `2369155`.
- Laut Audit: `npm run check`, `npm run test:run`, `npm run build` nach Tasks gruen; visuelle Prod-Build-Pruefung mit Screenshots; Console 0 Errors; CLS = 0.

Einschraenkung: In dieser Struktur-Inventur wurden diese Gates nicht neu ausgefuehrt. Sie sind Audit-Evidenz, nicht frische Verifikation.

## Aktueller PR-Status

PR #5:

- URL: `https://github.com/cherinojoel-lang/hsb-boden/pull/5`
- Status: offen
- Draft: ja
- Mergeable: `CONFLICTING`
- Base: `main`
- Head remote: `a591724`

## Naechste Phase

Release-Candidate-Stabilisierung, keine weitere Website-Arbeit.

Reihenfolge:

1. `RELEASE_CANDIDATE_STATUS.md`, `BRANCH_DELTA_REPORT.md` und `FINAL_RELEASE_AUDIT.md` auf lokalen HEAD `2369155` aktualisieren oder durch ein neues Audit unter `docs/audit/` ersetzen.
2. Konflikte gegen `main` kontrolliert in einem separaten Merge-Prep-Stand loesen.
3. Danach lokal verifizieren: `npm run check`, `npm run test:run`, `npm run build`.
4. Erst nach expliziter Freigabe Preview aktualisieren.
5. Preview gegen den dann aktuellen HEAD verifizieren.
6. Erst danach PR aus Draft/Conflict-Zustand herausfuehren.

## Aktive Dokumente

Primaer:

- `PROJECT_CANONICAL_STRUCTURE.md`
- `PROJECT_CURRENT_STATE.md`
- `docs/audit/2026-06-11-masterpiece-sota-phase1-2.md`
- `RELEASE_CANDIDATE_STATUS.md`
- `RELEASE_PATH.md`
- `MERGE_RESOLUTION_PLAN.md`

Sekundaer / Evidenz:

- `BRANCH_DELTA_REPORT.md`
- `FINAL_RELEASE_AUDIT.md`
- `docs/audit/screenshots/`
- `docs/launch/referenzen-freigabe.md`
- `ops/n8n/README.md`
- `ops/n8n/README-runbook.md`

Nicht als Primaerwahrheit verwenden:

- alte Chatverlaeufe
- `FINAL_HANDOFF.md`
- `CURRENT_EXECUTION_STATE.md`
- `WEBSITE_FINAL_*`
- `WEBSITE_FINALIZATION_*`
- widerspruechliche Deployment-Snapshots ohne frische Verifikation

## Harte Stop-Regeln

- Keine Website-Aenderungen ohne neue Aufgabenfreigabe.
- Kein Merge.
- Kein Deployment.
- Kein DNS-/Domain-Cutover.
- Keine SMTP-/n8n-Aktivierung.
- Keine Produktionsbehauptung ohne frische Verifikation.
