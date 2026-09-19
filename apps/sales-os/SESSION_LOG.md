
## 2026-09-17 17:12 — Claude Code: Abmeldung end-to-end belegt
- Trigger-Abgleich laeuft in beiden Konten (j-cherino, j-post); Jordis laufender Batch wurde automatisch auf SENT gesetzt (52 Leads, 15 Bounces).
- Befund: Ereignis-Flut (NEEDS_REVIEW bei jedem Lauf neu) -> Vorfilter (live 15:10).
- Befund: drei "Abmelden"-Antworten von Kollegenadressen der Firmendomain blieben ungesperrt -> Domain-Abmeldung (Merge 45664c8, live 17:06 per clasp push durch Owner).
- Nachweis 17:10 UTC+2: HSB-20260708-03671/-03677/-03218 Opt-out=yes, Suppressed=yes, Versandfreigabe=no, Pipeline Abgemeldet; INBOUND_EVENTS OPT_OUT PROCESSED "Domain-Abmeldung".
- Offen (Owner-Gate): Task 4 Datenregeln (crm_data_hygiene_gate.py --apply), INBOUND_EVENTS-Layout + 284 Duplikate (Plan docs/superpowers/plans/2026-09-17-crm-cockpit-visual.md Task 1), Cockpit-Tabs (Plan Task 2-7), Abmelde-Link (mailto in Signatur -> gleicher Opt-out-Pfad).
