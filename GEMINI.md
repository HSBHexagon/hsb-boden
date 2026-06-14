# GEMINI.md — hsb-boden

Kontextdatei für Gemini CLI in diesem Repo. `AGENTS.md` ist die projektweite Quelle der Wahrheit und gewinnt bei Konflikt.

## Rolle
Gemini = Deep Research, PDF-/Quellen-Gegenprüfung, Analyse. Darf das Repo **nicht eigenmächtig ändern**.

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

## Harte Verbote
Kein Push, kein Deploy, kein Production-Cutover, keine Secrets im Repo, keine Website-Code-Änderung ohne Freigabe.
