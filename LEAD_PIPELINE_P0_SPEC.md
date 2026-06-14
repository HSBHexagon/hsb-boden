# LEAD_PIPELINE_P0_SPEC — HSB-Boden / HEXAFLOOR

> P0A-Spezifikation. Stand: 2026-06-14. Planung/Spezifikation, keine Live-Aktivierung.

## 1. Ziel der Lead-Pipeline
Erfassung, Qualifizierung, Nachverfolgung und Übergabe von B2B-Leads aus mehreren Eingangskanälen in ein einheitliches CRM-Light, mit definierten Status-, Scoring- und Follow-up-Regeln. P0A definiert ausschließlich die Spezifikation; kein Endpoint, kein Webhook-Livebetrieb, kein Versand.

## 2. Eingangskanäle

| Kanal | Quelle | Eingang | Verarbeitung | Status |
|-------|--------|---------|--------------|--------|
| Website-Kontaktformular | `src/pages/kontakt` + Formular | `PUBLIC_LEAD_ENDPOINT` → n8n Webhook | Append CRM-Light | spezifiziert, inaktiv |
| Outlook-Kampagne | `cherinodiaz@outlook.com` | manuelle Antwort/Reply | manueller CRM-Eintrag | geplant |
| Flyer / QR / UTM | Print-Flyer (`public/*.pdf`) | QR → Landingpage → Formular | wie Website | geplant |
| Manuelle Leadliste | `hsb_lead_list_2026_06_11.csv` (30 Leads) | Import | Dedupe + Scoring | vorhanden, nicht importiert |

## 3. Lead-Statusmodell

| Status | Bedeutung | Folgestatus |
|--------|-----------|-------------|
| Neu | gerade erfasst, ungeprüft | geprüft |
| geprüft | Pflichtfelder + Plausibilität ok | kontaktiert / kein Interesse |
| kontaktiert | Erstkontakt erfolgt | Follow-up fällig / interessiert / kein Interesse |
| Follow-up fällig | Wiedervorlage erreicht | kontaktiert / interessiert / später erneut prüfen |
| interessiert | positives Signal | Angebot relevant |
| Angebot relevant | Angebot/Übergabe an Inhaber sinnvoll | (Übergabe) |
| kein Interesse | Absage | später erneut prüfen / Archiv |
| später erneut prüfen | Wiedervorlage in Zukunft | geprüft |

## 4. Pflichtfelder

| Feld | Pflicht | Quelle |
|------|---------|--------|
| Lead-ID | ja | systemvergeben |
| Firma | ja | Eingang |
| E-Mail ODER Telefon | ja (mind. eines) | Eingang |
| Quelle/Kanal | ja | systemgesetzt |
| Consent-Status | ja (bei Formular) | Formularfeld |
| Eingangsdatum | ja | systemgesetzt |
| Status | ja | Default „Neu" |

Optionale Felder gemäß `CRM_LIGHT_SCHEMA.md`.

## 5. Dublettenlogik
- Schlüssel: normalisierte `Firma` + (`E-Mail` ODER `Domain` aus Website).
- Treffer → kein neuer Datensatz; Aktivität an bestehenden Lead anhängen.
- Normalisierung: trim, lowercase, Entfernen von Rechtsform-Suffixen für Vergleich (nicht für Anzeige).

## 6. Lead-Scoring A/B/C

| Tier | Kriterien (Heuristik) |
|------|-----------------------|
| A | hoher Branchen-Fit + akuter Bedarf + erreichbarer Entscheider |
| B | guter Fit, Bedarf mittelfristig |
| C | passender Fit, niedrige Priorität / Beobachtung |

Score 0–100 aus: Branche, Flächenpotenzial, Belastungsart, Entscheider-Erreichbarkeit, Sanierungsfenster.

## 7. Follow-up-Regeln

| Stufe | Auslöser | Frist |
|-------|----------|-------|
| FU1 | nach Erstkontakt | 4–7 Tage |
| FU2 | nach FU1 ohne Antwort | 10–14 Tage |
| Abschluss | nach FU2 | Status „kein Interesse" oder „später erneut prüfen" |

## 8. Tagesreport
- Inhalt: neue Leads, Statusänderungen, fällige Follow-ups.
- Kanal: Outlook-Mail.
- Auslösung: geplant via n8n; in P0A nur spezifiziert.

## 9. Wochenreport
- Inhalt: Pipeline nach Tier/Status, Conversion-Übersicht, offene Übergaben.
- Kanal: Outlook-Mail / CRM-Tab.

## 10. Übergabe an Inhaber
- Trigger: Status „Angebot relevant".
- Inhalt: Lead-Stammdaten + Aktivitätshistorie + Notizen.

## 11. Erlaubt / Verboten

| Erlaubt (P0A) | Verboten (P0A) |
|---------------|----------------|
| Spezifikation, Tabellen, Felder, Status, Gates | Endpoint-/Webhook-Code |
| Doku im kanonischen Repo | Live-Aktivierung / echter Versand |
| Planung n8n/CRM/Reports | Push / Deploy / Production-Cutover |
| — | Secrets/Tokens im Repo |
| — | Website-Code-Änderung |

## 12. Freigabe-Gate
Keine Live-Aktivierung der Pipeline ohne ausdrückliche Nutzerfreigabe (siehe `P0_IMPLEMENTATION_APPROVAL_CHECKLIST.md`).

## 13. Testkriterien (P0A-Review)
- Statusmodell vollständig und widerspruchsfrei.
- Pflichtfelder eindeutig.
- Dublettenlogik deterministisch beschrieben.
- Jeder Kanal hat definierten Eingang + Verarbeitung.

## 14. Nächster Entscheidungspunkt
Freigabe von P0B (Implementierung Endpoint + n8n + Sheets-Anbindung) oder Anpassung der Spezifikation.
