# AGENTS.md — hsb-sales-os

HSB Sales OS: Apps-Script-/Sheets-basiertes Vertriebssystem mit Flows, Engine und Adaptern. Stand und Betrieb: @PROJECT_STATE.md, @CURRENT_HANDOFF.md, @README_OPERATING.md

## Struktur
`apps_script/` (Google Apps Script, ID in `SCRIPT_ID`), `engine/`, `flows/`, `adapters/`, `tests/`, `golden/` (Referenzausgaben), `deploy/` + `deploy.sh`, `deploy_manifest.json`, `RELEASE_MANIFEST.json`.

## Regeln
- Deploy nur ueber `deploy.sh` und nur nach Freigabe; `RELEASE_MANIFEST.json` und `VERIFICATION_REPORT.md` danach aktualisieren.
- Golden-Dateien in `golden/` sind Referenz: Aenderung nur mit Begruendung im Handoff.
- Das Sheet gehoert dem privaten Konto — HSB-Geschaeftsfluesse und privates Konto nicht mischen.
- `.env` nie lesen oder committen.
