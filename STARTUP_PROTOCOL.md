# STARTUP_PROTOCOL — HSB / HEXAFLOOR

## Zweck
Definiert, was jedes KI-System beim Start tun muss.

## Pflichtstart
1. Repo-Pfad über Registry auflösen:
```bash
REPO="$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)"
cd "$REPO"
```
2. Guard prüfen:
```bash
~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden
```
3. Pflichtdateien lesen:
- `MASTER_EXECUTION_RULES.md`
- `SKILLS_MASTER_PROMPT.md`
- `PHASED_EXECUTION_PLAN.md`
- `PROJECT_TRUTH.md`
- `AI_EXECUTION_PLAYBOOK.md`
- `CURRENT_HANDOFF.md`
- `CHECKPOINT_STATE.json`
- `SESSION_LOG.md`
4. Git-Status prüfen:
```bash
git status --short
git log -1 --format="%H | %ci | %s"
git diff -- 'src' 'public' 'components' 'layouts' 'styles' 'astro.config.*' 'vite.config.*' 'wrangler.toml' 'package.json' 'package-lock.json' 'pnpm-lock.yaml' 'bun.lock' 'yarn.lock' | wc -l
```
5. Wenn Website-Code-Diff unerwartet > 0: STOP.
6. Wenn Checkpoint eine offene Aufgabe enthält: dort fortsetzen.
7. Wenn Tokenlimit/Absturz vorher erkannt wurde: `CRASH_RECOVERY_PROTOCOL.md` nutzen.

## Kein Modell darf
- neu suchen
- neuen Repo-Pfad wählen
- aus Backup arbeiten
- ohne Checkpoint fortfahren
- ohne Handoff fortfahren
