# ACQUISITION_SYSTEM_PLAN — HSB-Boden / HEXAFLOOR

> Stand: 2026-06-26. Akquise-Gesamtsystem (Plan). Eine Lead-Liste `hsb_lead_list_2026_06_11.csv` wird in älteren Docs erwähnt, ist im aktuellen Repo aber nicht vorhanden.

## 1. Zielgruppen / ICP
- B2B-Industrie mit anspruchsvollen Bodenanforderungen: Lebensmittel/Getränke, Chemie/Pharma, Logistik/Lager, Produktion.
- Entscheider: Geschäftsführung, Werk-/Betriebsleitung, Facility-Management, Instandhaltung.
- Trigger: Sanierungsbedarf, Hygiene-/Belastungsanforderungen, Neubau/Erweiterung.

## 2. Leadliste A/B/C
- **A**: hoher Fit + akuter Bedarf + erreichbarer Entscheider.
- **B**: guter Fit, Bedarf mittelfristig.
- **C**: passender Fit, niedrige Priorität / Beobachtung.
- Pflege im CRM-Light (`CRM_LIGHT_SCHEMA.md`).
- Aktueller Repo-Check 2026-06-20: keine CSV-Leadliste im Arbeitsbaum gefunden. Für Versand heute muss die Empfängerliste außerhalb des Repos separat verifiziert werden.
- Die späteren 5.000 Lead-Datensätze sind ein zukünftiger externer Input. Ihr Fehlen blockiert diese Dokumentationsvorbereitung nicht.

## 3. Lead-Scoring (0–100, Start-Heuristik)
- Branche-Fit, Flächenpotenzial, Belastungsart, Entscheider-Erreichbarkeit, Timing/Sanierungsfenster.
- Verfeinerung optional nur über später explizit freigegebene Automatisierung; n8n ist derzeit nicht aktiv.

## 4. Statusmodell
`neu → kontaktiert → interessiert → Angebot → gewonnen | verloren | opt-out`

## 5. Follow-up-Stufen
1. Erstkontakt (Mail + Flyer/Landingpage).
2. Follow-up 1 (nach 4–7 Tagen).
3. Follow-up 2 (nach 10–14 Tagen).
4. Abschluss/Archiv (gewonnen/verloren/opt-out).

## 6. Flyer / Landingpage / QR / UTM
- Flyer-PDFs in `public/` (committet 9ac994a) mit QR → Landingpage/Kontakt.
- UTM-Parameter pro Kanal/Kampagne (Quelle/Kampagne im CRM erfassen).
- Konsistenz Flyer ↔ Website (Namen/Logos/Referenzen) fuer den dokumentierten Materialstand geschlossen.

## 7. Kanonischer Outreach-Kanal
- `j-cherino@hsb-boden.de` ist der kanonische Absender- und Antwortkanal fuer finalisierte Flyer- und Mail-Outreach-Materialien.
- `info@hsb-boden.de` bleibt die offizielle allgemeine Website-/Legal-/Kontakt-Mailbox.
- `cherinodiaz@outlook.com` ist nur historischer/interner Fallback und kein kanonischer oeffentlicher Outreach-Kanal.
- Keine Massen-Automation an gekaufte Kontakte ohne Rechts-Review (`AGENTS.md`).

## 8. Übergang zu CRM-Light
- Alle Leads/Status in Google-Sheets-CRM-Light (`CRM_LIGHT_SCHEMA.md`).
- Künftiger 5.000-Lead-Paste/Import ist nur CRM-Datenvorbereitung und keine Versandfreigabe.

## 9. Optionale spätere Automatisierung (derzeit deaktiviert)
- Mögliche spätere Erweiterungen: Follow-up-Reminder oder Tagesreporting, nur nach expliziter Freigabe.
- Der aktive Lead-Intake ist jedoch Website `/api/lead` -> Google Apps Script Web App -> Google Sheets CRM-Light.
- `ops/n8n/` bleibt historisch/deprecated und wird nur bei späterer expliziter Re-Freigabe wieder relevant.

## 10. Phase-7- und Import-Gates
- Phase 7 wird kanonisch ueber `docs/launch/PHASE_7_COMPLIANCE_GATE.md` vorbereitet.
- Der spaetere 5.000-Lead-Paste/Import wird kanonisch ueber `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` vorbereitet.
- Dispatch bleibt blockiert, bis beide Gate-Anforderungen mit realen Daten und expliziten Freigaben erfuellt sind.

## Offene Punkte
- Vor jedem echten Versand separat dokumentieren: Lead-Liste, Empfaengerbasis, Opt-out-Handling und Compliance/Freigabe fuer den konkreten Einsatz.
- Heute owner-approved: bestehende Flyer- und Mail-Materialien fuer einen kontrollierten manuellen B2B-Testeinsatz.
- Heute blockiert: Serienversand, CRM-Automation, n8n-Livebetrieb, Apps-Script-/API-Versand und jeglicher Dispatch ohne separate Compliance-/Freigabedokumentation.
- Die 5.000 Akquise-Datensaetze fehlen aktuell noch und bleiben ein kuenftiger externer Input.
