# CRM_LIGHT_SCHEMA — HSB-Boden

> Google-Sheets-CRM-Light als Start. Stand: 2026-06-14. Plan, keine Live-Daten.

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
| Notizen | text | — |
| Opt-out-Status | enum | nein / ja |
| Letzter Kontakt | date | YYYY-MM-DD |
| Verantwortlicher | string | Joel / … |

## Hinweise
- DSGVO: nur geschäftliche Kontaktdaten, dokumentierte Quelle, Opt-out respektieren (siehe `AGENTS.md` Non-Negotiables).
- Scoring-Logik und Statusübergänge: siehe `ACQUISITION_SYSTEM_PLAN.md`.
- Befüllung/Automation via n8n: siehe `N8N_AUTOMATION_PLAN.md`.
