# CRM_LIGHT_SCHEMA — HSB-Boden

> Google-Sheets-CRM-Light als Start. Stand: 2026-06-26. Template-ready, keine Live-Daten.

## Spalten (eine Zeile = ein Lead)

| Feld | Typ | Beispiel/Werte |
|------|-----|----------------|
| Lead-ID | string | HSB-0001 |
| Firma | string | Muster GmbH |
| Standort | string | Ort |
| Region | string | NRW / BW / … |
| Branche | string | Lebensmittel, Chemie, Logistik … |
| Tier | enum | A / B / C |
| Ansprechpartner | string | Vor-/Nachname |
| Rolle | string | Geschäftsführer, Werkleiter, Facility … |
| E-Mail | string | — |
| Telefon | string | — |
| Website | url | — |
| Quelle | string | Recherche, Empfehlung, Web … |
| Beziehung / Kontaktgrund | string | Bestandskontakt / Messe / dokumentierter Anlass |
| Kampagne | string | Outreach-2026-Q2 |
| Score | number | 0–100 |
| Status | enum | neu / kontaktiert / interessiert / Angebot / gewonnen / verloren / opt-out |
| Nächste Aktion | string | Anruf, Follow-up-Mail … |
| Follow-up-Datum | date | YYYY-MM-DD |
| Interesse | string | hoch/mittel/niedrig |
| Projektart | string | Neubau / Sanierung |
| Fläche geschätzt | number (m²) | — |
| Belastungsart | string | mechanisch / chemisch / thermisch |
| Sanierungsfenster | string | Quartal / Zeitraum |
| Opt-in-Status | enum | yes / no / unknown |
| Opt-out-Status | enum | nein / ja |
| Versandfreigabe | enum | no / yes |
| Verantwortlicher | string | Joel / … |
| Notizen | text | — |

## Hinweise
- Die Struktur ist `template-ready-awaiting-lead-data`; die 5.000 Lead-Datensätze sind fuer diese Dokumentationsaufgabe nicht erforderlich.
- Defaults bei Import: `Status = neu`, `Nächste Aktion = prüfen`, `Versandfreigabe = no`, `Opt-in-Status = unknown`, `Opt-out-Status = unknown`.
- Telefonfelder muessen als Text gespeichert und formatiert werden.
- Diese Felder duerfen beim Import leer bleiben: `Ansprechpartner`, `Rolle`, `Telefon`, `Interesse`, `Projektart`, `Fläche geschätzt`, `Belastungsart`, `Sanierungsfenster`, `Notizen`.
- Dispatch bleibt blockiert, wenn `E-Mail`, `Quelle`, `Beziehung / Kontaktgrund`, `Opt-in-Status`, `Opt-out-Status`, `Versandfreigabe` oder `Verantwortlicher` fehlen oder unklar sind.
- Duplicate detection keys: E-Mail, Website, Firma + Standort, Firma + Ansprechpartner, Telefon (falls vorhanden).
- DSGVO: nur geschäftliche Kontaktdaten, dokumentierte Quelle, Opt-out respektieren (siehe `AGENTS.md` Non-Negotiables).
- Scoring-Logik und Statusübergänge: siehe `ACQUISITION_SYSTEM_PLAN.md`.
- Aktiver Lead-Intake: Website `/api/lead` -> Google Apps Script Web App -> Google Sheets CRM-Light.
- `ops/n8n/` und `N8N_AUTOMATION_PLAN.md` sind nur historisch/optional; n8n ist nicht die aktive Lead-Intake-Loesung.
