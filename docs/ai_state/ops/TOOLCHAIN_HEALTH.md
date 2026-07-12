# Toolchain Health — hsb-boden

Stand: 2026-07-12, alle Werte frisch gemessen (UTC-Zeitpunkte im Sitzungsreport).

| System | Prüfung | Ergebnis |
|---|---|---|
| npm test:run | Vitest | 51/51 PASS |
| npm run check | astro check | 0 Fehler, 0 Warnungen |
| npm run build | Astro 6.4.6 static | 35 Seiten, PASS |
| npm run deploy:dry-run | Build + `wrangler pages deployment list` | PASS (Production-Env auf Branch `main` sichtbar) |
| GitHub CI | quality/security/lighthouse/deploy-preview | SHA-gepinnt, minimale Permissions |
| CodeQL | letzte Analyse 2026-07-11 | 0 offene Alerts |
| Dependabot | Alerts | 0 offen |
| Secret Scanning | REST-API | 404 → NEEDS_VERIFICATION (Feature-Status/Token-Scope) |
| Cloudflare Pages | Projekt `hsb-boden` | Custom Domains `hsb-boden.pages.dev`, `www.hsb-boden.de`; Direct Upload |
| Live www | HTTP | 200, `cache-control: public, max-age=0, must-revalidate` |
| Live Apex | HTTP | 301 → www (DNS zeigt weiterhin auf All-Inkl `85.13.130.17`; NS-Cutover offen) |
| Codex | CLI 0.144.1 | Auth OK; Usage-Quota zeitweise erschöpft (`CODEX_PLUGIN_NOT_READY`) |

## Bekannte Drift (behoben in `fable5/deploy-truth-consolidation`)

- `wrangler.toml` Workers-SSR-Entrypoint (Root Cause für „Workers Builds"-CI-Fehler in Bot-PRs)
- `package.json` deploy-Skripte zeigten auf `wrangler deploy` (Workers)
- `copilot-instructions.md` Astro 5/Workers/SSR
- `AGENTS.md` Deploy-Gate-Formulierung (WordPress-Ära)
- `docs/PHASE_C_CUTOVER_RUNBOOK.md` Workers-Ära-Befehle (Stale-Banner gesetzt)

## Offene Betriebs-Risiken

1. Lokales `main` ist 3 Commits vor `origin/main` (docs-only) — Push freigabepflichtig.
2. `dependabot-auto-merge.yml` merged semver-minor automatisch → OWNER_DECISION (siehe AUTOMATION_GUARDRAILS.md).
3. Verwaister Worker `hsb-boden` im Alt-Account (`cherinojoel.workers.dev`) — Lösch-/Archivierungsentscheid beim Owner.
