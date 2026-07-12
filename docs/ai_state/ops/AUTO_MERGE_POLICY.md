# Auto-Merge-Policy — hsb-boden

Stand: 2026-07-12. Status: ENTWURF — endgültige Politik ist Owner-Entscheidung.

## Ist-Zustand (verifiziert)

- Ruleset „Protect Main" (ID 18497243): PR-Pflicht + Required Status Checks, keine Bypass-Actors.
- `dependabot-auto-merge.yml`: aktiviert Auto-Merge (`gh pr merge --auto --squash`) für
  `version-update:semver-patch` UND `semver-minor`, gated nur durch Required Checks.
- Kein Jules-Auto-Merge, kein generisches auto-merge-Label, kein CODEOWNERS.

## Policy (empfohlen)

| Quelle | Auto-Merge erlaubt? | Bedingung |
|---|---|---|
| Dependabot semver-patch | JA (empfohlen) | Required Checks grün; Lockfile-only |
| Dependabot semver-minor | NEIN → Owner-Review | Changelog-/Breaking-Prüfung nötig (aktueller Workflow erlaubt es — Änderung empfohlen) |
| Dependabot semver-major | NEIN | immer Owner |
| Jules/Bot-PRs | NEIN, niemals | Implementierer genehmigt nie eigene Arbeit |
| Agenten-PRs (fable5/*) | NEIN | Draft-only; Owner merged |
| Geschützte Pfade (`.github/workflows/**`, `functions/**`, `wrangler.toml`, `astro.config.mjs`, `AGENTS.md`) | NEIN, nie vollautomatisch | R3-Quorum + Owner |

## Umsetzungsschritte nach Owner-Freigabe

1. `dependabot-auto-merge.yml`: Bedingung auf `semver-patch` reduzieren (1-Zeilen-PR).
2. Optional CODEOWNERS für geschützte Pfade einführen.
3. Required-Check-Namen im Ruleset gegen tatsächliche Workflow-Job-Namen verifizieren.
