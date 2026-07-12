# Automation Guardrails — hsb-boden

Stand: 2026-07-12. Deterministische Schutzregeln und deren Status.

## Aktive Guardrails

| Guardrail | Mechanismus | Test | Deaktivierung |
|---|---|---|---|
| Kein Direkt-Push auf `main` | GitHub Ruleset „Protect Main" (ID 18497243): PR-Pflicht, Status-Checks, kein Force-Push/Delete, keine Bypass-Actors | Push auf main ohne PR wird serverseitig abgelehnt | Repo-Settings (Owner) |
| Production-Deploy gated | `deploy-production.yml` nur `workflow_dispatch`; `npm run deploy:production` = `exit 1` | Skriptaufruf schlägt fehl | Workflow-Edit via PR |
| Kanonischer Pfad | `assert_canonical_project_path.sh` (KI-System-Registry) | Lauf außerhalb Repo → ERROR | Registry (Owner) |
| Supply Chain | Alle Actions SHA-gepinnt; Workflows minimal `contents: read` | grep-Audit 2026-07-12: 0 ungepinnte | PR |

## Bewusst NICHT eingerichtet

- Kein automatischer Codex-Review-Gate (Stop-Hook): Risiko von Review-Schleifen und hohem Verbrauch; Reviews laufen explizit pro Gate.
- Keine neuen globalen User-Hooks: projektlokale, versionierte Wege genügen.
- Keine Auto-Merge-Erweiterung.

## OWNER_DECISION offen

| Thema | Befund | Empfehlung |
|---|---|---|
| `dependabot-auto-merge.yml` | merged semver-patch UND semver-minor automatisch (`gh pr merge --auto --squash`) ohne menschliche Diff-Prüfung; Status-Checks greifen, bleibt aber Auto-Pfad nach main | Auf `semver-patch` beschränken (kleiner reversibler PR) |
| Secret Scanning | API 404 — Status nicht read-only verifizierbar | Owner prüft Repo-Settings → Security; ggf. Push Protection aktivieren |
