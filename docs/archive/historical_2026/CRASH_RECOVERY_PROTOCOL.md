# CRASH_RECOVERY_PROTOCOL — HSB / HEXAFLOOR

## Zweck
Definiert, wie nach Absturz, Tokenlimit, geschlossenem Chat oder Modellwechsel weitergearbeitet wird.

## Recovery-Reihenfolge
1. `STARTUP_PROTOCOL.md` ausführen
2. `CHECKPOINT_STATE.json` lesen
3. `CURRENT_HANDOFF.md` lesen
4. neuesten Report unter `~/KI-System/08_System/reports/validation/` prüfen
5. `git status --short` prüfen
6. Website-Code-Diff prüfen
7. offene Aufgabe identifizieren
8. nur fortsetzen, wenn:
   - Repo-Pfad stimmt
   - Checkpoint plausibel ist
   - Website-Code-Diff erwartet ist
   - keine Secrets offen sind
   - kein Push/Deploy ungefragt passiert

## Wenn Checkpoint unvollständig ist
STOP. Keine eigenmächtige Fortsetzung. Report schreiben: `recovery_blocked_YYYYMMDD_HHMMSS.md`

## Wenn Checkpoint eindeutig ist
Fortsetzen bei: `active_phase`, `active_task`, `next_step`.

## Modellwechsel
- Claude → Codex: Codex liest `CHECKPOINT_STATE.json`, `CURRENT_HANDOFF.md`, Reports.
- Codex → Claude: Claude liest dieselben Dateien.
- Gemini/Perplexity liefern Research: nur als Quelle, nicht als Wahrheit, bis ChatGPT/Claude/Codex validieren.
