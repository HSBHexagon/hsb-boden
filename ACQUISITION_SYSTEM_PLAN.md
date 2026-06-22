# ACQUISITION_SYSTEM_PLAN — HSB-Boden / HEXAFLOOR

> Stand: 2026-06-20. Akquise-Gesamtsystem (Plan). Eine Lead-Liste `hsb_lead_list_2026_06_11.csv` wird in älteren Docs erwähnt, ist im aktuellen Repo aber nicht vorhanden.

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

## 3. Lead-Scoring (0–100, Start-Heuristik)
- Branche-Fit, Flächenpotenzial, Belastungsart, Entscheider-Erreichbarkeit, Timing/Sanierungsfenster.
- Verfeinerung optional via n8n/AI später.

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
- Konsistenz Flyer ↔ Website (Namen/Logos/Referenzen) = offen (P1).

## 7. Rolle der Outlook-Mail
- `cherinodiaz@outlook.com` als Versand-/Antwortkanal für Erstansprache und Follow-ups.
- Keine Massen-Automation an gekaufte Kontakte ohne Rechts-Review (`AGENTS.md`).

## 8. Übergang zu CRM-Light
- Alle Leads/Status in Google-Sheets-CRM-Light (`CRM_LIGHT_SCHEMA.md`).

## 9. Übergang zu n8n
- Formular-Leads automatisch ins CRM (`N8N_AUTOMATION_PLAN.md`), Follow-up-Reminder, Tagesreport.

## Offene Punkte
- Webhook/SMTP aktivieren (P0), n8n-Hosting (P0), Rechts-Review Outreach (P1), Go-Live-Zeitpunkt.
- Heute verwendbar: einzelne vorbereitete Mails mit geprüftem PDF-Anhang und manueller Antwortbearbeitung.
- Heute blockiert: Serienversand, CRM-Automation, n8n-Livebetrieb und Formularzustellung ohne Freigabe/Secrets.
