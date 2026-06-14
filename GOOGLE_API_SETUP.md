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
