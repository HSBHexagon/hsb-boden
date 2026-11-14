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

## Pflichtstart HSB / HEXAFLOOR (Garantie-Struktur)
Vor jeder Arbeit lesen: `MASTER_EXECUTION_RULES.md`, `STARTUP_PROTOCOL.md`, `CHECKPOINT_STATE.json`, `PROJECT_TRUTH.md`, `AI_EXECUTION_PLAYBOOK.md`, `PHASED_EXECUTION_PLAN.md`, `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`. Pflichtabschluss: `CHECKPOINT_STATE.json` + `CURRENT_HANDOFF.md` + `SESSION_LOG.md` aktualisieren.

## Harte Verbote
Kein Push, kein Deploy, kein Production-Cutover, keine Secrets im Repo, keine Website-Code-Änderung ohne Freigabe.

## Einmalige private Betreiberübergabe für die nächste HSB-AGY-Sitzung (2026-11-02)
Vor der nächsten HSB-Sales-OS-/Kampagnenarbeit die **neueste** noch offene Betreiberübergabe im privaten `cherinojoel-lang/ObsidianVault` unter `brain/pending/AGY_HSB_NEXT_SESSION_2026-11-02.md` lesen und mit Live-Quellen abgleichen. Zugriff über authentifiziertes `gh api repos/cherinojoel-lang/ObsidianVault/contents/brain/pending/AGY_HSB_NEXT_SESSION_2026-11-02.md --jq .content | base64 -D` (macOS) oder einen authentifizierten GitHub-Konnektor. Fehlt die Berechtigung, ausdrücklich melden; keine Annahmen. Ohne nachgewiesene Freigabe weder Serienversand noch Entsperrung von Bestandskunden auslösen. Nach bestätigter Übernahme die Übergabe als abgearbeitet kennzeichnen.
