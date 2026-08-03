# CRM-Datenquelle — kanonische Wahrheit

Stand: 2026-08-03, per direkter Dateisystem- und Google-Drive-Recherche verifiziert
(alle drei Google-Workspace-Profile `cherinodiaz`, `cherinojoel`, `hsb-boden` durchsucht).

## Ergebnis

**Die 6.424-Lead-Akquiseliste existiert ausschließlich lokal, nicht in Google Sheets.**

Kanonischer Pfad: `data/lead-import/output/` (bewusst per `.gitignore` Zeile 21
von Git ausgeschlossen — enthält personenbezogene B2B-Kontaktdaten, gehört nicht
ins Repo).

| Datei | Zeilen (inkl. Header) | Zweck |
|---|---|---|
| `HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv` | 6.425 | Vollständiger Gesamtbestand, beide Operatoren |
| `HSB_CRM_Leads_ALL_Joel_2026-07-08.csv` | 3.213 | Joel-Hälfte des Gesamtbestands |
| `HSB_CRM_Leads_ALL_Jordi_2026-07-08.csv` | 3.213 | Jordi-Hälfte des Gesamtbestands |
| `HSB_CRM_Leads_MASTER_2026-07-08.csv` | 5.001 | Kleinerer Teilbestand (5.000) — Verhältnis zum ALL-Bestand ungeklärt, Owner-Rückfrage nötig |
| `HSB_CRM_Leads_Joel_2500_2026-07-08.csv` | 2.501 | Joel-Hälfte des 5.000er-Teilbestands |
| `HSB_CRM_Leads_Jordi_2500_2026-07-08.csv` | 2.501 | Jordi-Hälfte des 5.000er-Teilbestands |
| `HSB_CRM_Leads_RESERVE_2026-07-08.xlsx` | — | Reserve-Liste, ungeprüft |
| `sheet_import_matrix.json`, `kaltakquise_import_matrix.json` | — | Vermutlich Vorbereitung für einen Google-Sheet-Import, der nie durchgeführt wurde (kein passendes Sheet in Drive gefunden) |

Jede Zeile hat 29 Spalten, u. a. `Versandfreigabe`, `Opt-in-Status`,
`Opt-out-Status`, `Verantwortlicher`, `Flyer-Anhang`.

**Verifizierter Freigabestatus (2026-08-03):** In `HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv`
haben alle 6.423 Datenzeilen `Versandfreigabe=unknown`. Keine Zeile ist aktuell
auf `yes` gesetzt.

## Was NICHT existiert

- Kein Google Sheet namens "HSB CRM Light", "Leads" o. ä. in Drive auffindbar
  (Volltextsuche nach einem konkreten Lead-Namen aus der lokalen Datei ergab
  ebenfalls keinen Treffer in Drive).
- `docs/crm/CRM_LIGHT_*.md` beschreibt ein separates, kleines Sheet für den
  technischen Lead-Webhook-Testpfad (`/api/lead` → Apps Script → Sheet) — das
  ist ein anderer Datensatz als diese Akquiseliste und hat eine andere Funktion
  (Formular-Eingänge der Live-Website, nicht die Kaltakquise-Liste).

## Owner-Bestätigung zur rechtlichen Grundlage (2026-08-03)

Der Owner hat mündlich erklärt, die rechtliche Grundlage für den Versand an
den Gesamtbestand sei durch einen Fachanwalt geprüft. Kein Dokumentbeleg
vorliegend — siehe Vermerk in `docs/launch/PHASE_7_COMPLIANCE_GATE.md`.

## Offene Klärung (an Owner)

1. Welcher der beiden Datensätze (6.424 "ALL" oder 5.000 "MASTER") ist der
   aktuell gültige, zu versendende Bestand?
2. Sollen die "RESERVE"-Leads einbezogen werden?
3. Soll `Versandfreigabe` für den gesamten Bestand pauschal auf `yes` gesetzt
   werden, oder soll das zeilenweise/nach Tier (A/B/C) erfolgen?
