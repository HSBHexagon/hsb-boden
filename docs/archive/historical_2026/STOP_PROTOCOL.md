# STOP_PROTOCOL — HSB / HEXAFLOOR

## Zweck
Definiert, was beim normalen Beenden, Tokenlimit oder Aufgabenende gespeichert werden muss.

## Pflichtabschluss
1. `CURRENT_HANDOFF.md` aktualisieren
2. `CHECKPOINT_STATE.json` aktualisieren
3. `SESSION_LOG.md` ergänzen
4. Report unter `~/KI-System/08_System/reports/validation/` schreiben
5. Git-Status ausgeben
6. Website-Code-Diff prüfen
7. Push/Deploy-Status dokumentieren

## CHECKPOINT_STATE.json muss enthalten
- `last_updated`
- `active_model`
- `active_phase`
- `active_task`
- `repo_path`
- `last_commit`
- `website_code_diff_lines`
- `modified_files`
- `completed_steps`
- `open_steps`
- `blocked_by`
- `next_step`
- `handoff_required`
- `safe_to_continue`

## Pflichtregel
Wenn Arbeit nicht vollständig abgeschlossen wurde: `safe_to_continue` darf nur `true` sein, wenn der nächste Schritt eindeutig dokumentiert ist.
