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

**Korrigiert 2026-08-11 (CSV-korrektes Parsing, `python3 csv.DictReader`,
Trennzeichen `;`, Anführungszeichen-bewusst):** Der bisherige Eintrag oben war
durch ein naives Spalten-Splitting (ohne Quote-Behandlung der mehrzeiligen
Freitextfelder `Beziehung / Kontaktgrund` und `Notizen`) falsch ausgerichtet
und zeigte daher `Versandfreigabe=unknown`. Nach korrektem CSV-Parsing gilt:

- `Versandfreigabe = no` fuer **alle 6.424** Datenzeilen in
  `HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv` (0 × `yes`, 0 × `unknown`).
- `Opt-out-Status = unknown` fuer alle 6.424 Zeilen (wie zuvor berichtet,
  dieser Wert war korrekt).
- 0 leere E-Mail-Felder, 0 Syntaxfehler, 0 exakte Duplikate innerhalb der
  Datei.
- `ALL_Joel` (3.212) ∪ `ALL_Jordi` (3.212) = `ALL_MASTER` (6.424) exakt,
  0 Ueberschneidung — Split ist sauber.
- `HSB_CRM_Leads_MASTER_2026-07-08.csv` (5.000) ist eine Teilmenge von
  `ALL_MASTER`, aber **veraltet**: 712 der 2.500 Zeilen in
  `HSB_CRM_Leads_Jordi_2500_2026-07-08.csv` sind im aktuellen `ALL_MASTER`
  Joel statt Jordi zugeordnet (Owner-Neuzuordnung fand zwischen den beiden
  Export-Wellen statt). Fuer den Versand ist ausschliesslich der
  `ALL_MASTER`/`ALL_Joel`/`ALL_Jordi`-Bestand (6.424) gueltig, nicht die
  5.000er-Welle.

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

1. **Per Evidenz beantwortet (2026-08-11):** `ALL_MASTER`/`ALL_Joel`/`ALL_Jordi`
   (6.424) ist der aktuell gültige Bestand — `MASTER_5000` ist eine ältere
   Export-Welle mit inzwischen überholter Owner-Zuordnung (siehe Korrektur
   oben). Für den Versand ausschließlich den 6.424er-Bestand verwenden.
2. Sollen die "RESERVE"-Leads einbezogen werden? — weiterhin offen, ungeprüft.
3. Soll `Versandfreigabe` für den gesamten Bestand pauschal auf `yes` gesetzt
   werden, oder soll das zeilenweise/nach Tier (A/B/C) erfolgen? — weiterhin
   offen, Owner-Entscheidung. Aktueller Wert bleibt `no` für alle Zeilen,
   automatisch nicht verändert.

## Wichtig: zwei getrennte CRM-Systeme

Dieses Dokument beschreibt ausschließlich den **Outbound**-Kaltakquise-Bestand
(lokale Dateien). Das **Inbound**-System (Website-Kontaktformular → `/api/lead`
→ Pages Function → Google Apps Script → Google Sheet „HSB CRM Light", Tab
„Leads") ist ein separates, reales, live-verifiziertes System — siehe
`PROJECT_TRUTH.md` Abschnitt 5 und `docs/crm/CRM_LIGHT_MAX_READINESS.md`.
Nicht verwechseln oder zusammenführen.
