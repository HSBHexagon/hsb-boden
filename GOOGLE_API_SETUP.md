# GOOGLE_API_SETUP — HSB-Boden

> Nur Plan. Stand: 2026-06-14. Keine Secrets committen.

## Google Cloud Projekt
- Projekt: `hsb-boden-ops`

## Aktivieren
- Google Sheets API
- Google Drive API
- optional: Gmail API
- optional: Calendar API
- optional: Search Console API
- optional: Analytics Data API

## Nicht aktivieren
- Vertex AI
- Compute Engine
- Cloud Run
- Cloud SQL
- BigQuery
- Firestore
- Kubernetes Engine

## Sicherheit
- OAuth/Service-Account-Keys nie im Repo. Speicherung über `~/KI-System/05_Secrets/` bzw. n8n-Credentials.
- Minimale Scopes (Sheets/Drive read/write nur wo nötig).
- Keine Secrets in `.env`-Dateien committen (`.gitignore` prüfen).

## OAuth-Minimalsetup
- **Entscheidung (2026-06-22, Claude Code stellvertretend nach Nutzer-Freigabe): Service Account.** Begründung: Sheets-CRM-Light ist interner Zugriff ohne Nutzerkontext, Service Account vermeidet OAuth-Refresh-Token-Wartung und Redirect-URI-Komplexität. Gmail/Calendar (optional, derzeit nicht im Scope) bleiben bei Bedarf OAuth.
- Startempfehlung (Referenz, durch obige Entscheidung umgesetzt):
  - Google Sheets CRM-Light intern: Service Account bevorzugt.
  - Gmail/Calendar mit Nutzerkonto: OAuth Client nur bei Bedarf.
- Credential-Ort:
  - keine Credentials im Repo
  - keine Secrets committen
  - Ablage nur in sicherem Secret-/n8n-Credential-Speicher
- Redirect-URI:
  - erst definieren, wenn n8n-Host feststeht
  - Beispiel nur als Platzhalter, nicht als finaler Wert
- Minimaltest:
  - Google Sheets append test
  - Lese-/Schreibtest mit Testzeile
  - danach Testzeile wieder kontrolliert entfernen oder als Test markieren
- Status:
  - keine Live-Aktivierung ohne Freigabe
