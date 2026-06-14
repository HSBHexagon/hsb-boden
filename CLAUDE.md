# CLAUDE.md — hsb-boden

Projektregeln für Claude Code in diesem Repo. `AGENTS.md` ist die projektweite Quelle der Wahrheit und gewinnt bei Konflikt; diese Datei ergänzt sie für Claude.

## KI-System Pflichtstart

Vor jeder Arbeit:

1. `~/KI-System/00_INDEX.md` lesen.
2. `~/KI-System/tools/handoff.sh read` ausführen.
3. Registry lesen: `~/KI-System/08_System/config/canonical-projects.json`.
4. Pfad verifizieren:
   `cd "$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)" && ~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden`

## Kanonischer Pfad

`/Users/joelcherinodiaz/KI-System/01_Wahrheitsquelle/_MERGED_20260613/AI-Memory-Hub/projects/hsb-boden`

Niemals arbeiten in: Backup-Pfaden, `/Users/joelcherinodiaz/Projects/hsb-boden`, Rohimporten, leeren brain-Projektordnern.

## Harte Regeln

- Keine Website-Code-Änderung ohne Freigabe (`src/`, `public/`, `components/`, `layouts/`, `styles/`, `astro.config.*`, `wrangler.toml`, `package.json`, Lockfiles).
- Kein `git add .` — immer exakte Pfade stagen.
- `.astro/data-store.json` nie committen.
- Kein Push, kein Production-Deploy ohne Freigabe.
- Keine Secrets anzeigen oder committen.
- Non-Negotiables aus `AGENTS.md` gelten unverändert (Live-WordPress nicht anfassen, keine unbelegten Zertifizierungs-/Referenzclaims, keine Kundennamen/Logos ohne Freigabe).

## Memory/Handoff

- Memory-/Handoff-Wahrheit: `~/KI-System/ObsidianVault/brain`.
- Bei Abschluss: `~/KI-System/tools/handoff.sh write "Claude Code" "<getan>" "<nächster Schritt>"` + `brain/CURRENT_HANDOFF.md` aktualisieren.

## Verifikation

Vor Completion-Claims (siehe `AGENTS.md` Deploy Gate): `npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run`.

## MASTER_EXECUTION_RULES Pflicht
Vor jeder Arbeit im Projekt HSB/HEXAFLOOR muss zuerst gelesen werden:
1. `MASTER_EXECUTION_RULES.md`
2. `PROJECT_TRUTH.md`
3. `AI_EXECUTION_PLAYBOOK.md`
4. `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`
Ohne diese Dateien darf keine Projektarbeit starten.
Der kanonische Repo-Pfad wird ausschließlich über `~/KI-System/08_System/config/canonical-projects.json` und `resolve_project_path.sh` bestimmt.
Bei Widerspruch zwischen Dateien:
STOP. Keine eigenmächtige Strukturentscheidung.
