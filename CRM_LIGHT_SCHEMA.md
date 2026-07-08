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
| Flyer-Anhang | string | public/HSB-Flyer-Joel-Cherino.pdf / public/HSB-Flyer-Jordi-Post.pdf |
| Notizen | text | — |

## Kanonik-Entscheidung (2026-07-08)

Dieses Dokument ist das kanonische Schema — so bereits vor dieser Entscheidung
in `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` ("Use `CRM_LIGHT_SCHEMA.md` as
the source of truth") festgelegt, hier nur explizit bestaetigt und mit dem
tatsaechlichen Sheet-Bestand abgeglichen.

Bekannte Abweichungen der vier realen Sheets von diesem kanonischen Schema
(Stand 2026-07-08, noch nicht bereinigt — Aenderungen an den Live-Sheets mit
6.424 realen Datensaetzen wurden bewusst nicht automatisch vorgenommen):

- **MASTER-Kaltakquise-Sheet** (`1tmNuC_Wqr8blRfZCHLqpwXXOe7zyO-3SzsotaBxOzSk`, Tab `Sheet1`, 23 Spalten): Es fehlen `Beziehung / Kontaktgrund`, `Interesse`, `Projektart`, `Fläche geschätzt`, `Belastungsart`, `Sanierungsfenster`. Reihenfolge von `Rolle`/`Tier` vertauscht gegenueber diesem Schema.
- **Jordi-Sheet** (`1uMbZAteSPjRBLGwpfT_evqA9hPbSTdDqPOK5TBXoFu4`) und **Joel-Sheet** (`1ha1iOX1pIWxF1c3FTRTxydqpa0uvPcBbbQ__ht1rAC8`): vermutlich dieselbe Struktur wie MASTER (nicht einzeln nachverifiziert, da vom selben Import-Lauf erzeugt).
- **Original-Sheet `HSB CRM Light`** (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Tab `Leads`, 27 Spalten): eigene Drift mit anderen Feldnamen — `Zielrollen-Kategorie` statt `Tier`, `Priorität` statt `Score`-Nachbarfeld, `Antwortstatus`/`Opt-out/Widerspruch` statt `Opt-in-Status`/`Opt-out-Status`, `Verantwortlich` statt `Verantwortlicher`. Dieses Sheet ist das Ziel der Website-Lead-Pipeline und wird von automatisierten Website-Leads befuellt (Feldnamen dort durch `HSBBODEN`-Apps-Script-Code vorgegeben, nicht durch dieses Schema-Dokument).

**Empfehlung fuer eine spaetere Bereinigung:** Vor einem echten Versand sollte technisch prueft werden, ob `Verantwortlicher`, `Flyer-Anhang`, `Versandfreigabe`, `Opt-in-Status`, `Opt-out-Status` in den drei Kaltakquise-Sheets an der erwarteten Spaltenposition stehen — das sind laut `LEAD_IMPORT_5000_CHECKLIST.md` die dispatch-blockierenden Pflichtfelder. Eine automatisierte Spalten-Restrukturierung auf den Live-Sheets mit realen Daten wurde bewusst nicht vorgenommen, um bestehende Zeilen-Zuordnungen nicht zu gefaehrden.

## Hinweise
- Die Struktur ist `template-ready-awaiting-lead-data`; die 5.000 Lead-Datensätze sind fuer diese Dokumentationsaufgabe nicht erforderlich.
- Defaults bei Import: `Status = neu`, `Nächste Aktion = prüfen`, `Versandfreigabe = no`, `Opt-in-Status = unknown`, `Opt-out-Status = unknown`.
- Für die 2-Personen-Akquise wird `Verantwortlicher` auf `Joel Cherino Diaz` oder `Jordi Post` gesetzt und `Flyer-Anhang` passend zugeordnet.
- Telefonfelder muessen als Text gespeichert und formatiert werden.
- Diese Felder duerfen beim Import leer bleiben: `Ansprechpartner`, `Rolle`, `Telefon`, `Interesse`, `Projektart`, `Fläche geschätzt`, `Belastungsart`, `Sanierungsfenster`, `Notizen`.
- Dispatch bleibt blockiert, wenn `E-Mail`, `Quelle`, `Beziehung / Kontaktgrund`, `Opt-in-Status`, `Opt-out-Status`, `Versandfreigabe`, `Verantwortlicher` oder `Flyer-Anhang` fehlen oder unklar sind.
- Duplicate detection keys: E-Mail, Website, Firma + Standort, Firma + Ansprechpartner, Telefon (falls vorhanden).
- DSGVO: nur geschäftliche Kontaktdaten, dokumentierte Quelle, Opt-out respektieren (siehe `AGENTS.md` Non-Negotiables).
- Scoring-Logik und Statusübergänge: siehe `ACQUISITION_SYSTEM_PLAN.md`.
- Aktiver Lead-Intake: Website `/api/lead` -> Google Apps Script Web App -> Google Sheets CRM-Light.
- `ops/n8n/` und `N8N_AUTOMATION_PLAN.md` sind nur historisch/optional; n8n ist nicht die aktive Lead-Intake-Loesung.
