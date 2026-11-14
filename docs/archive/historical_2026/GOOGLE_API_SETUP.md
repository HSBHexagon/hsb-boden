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
- Keys/Secrets nie im Repo. Speicherung über `~/KI-System/05_Secrets/` bzw. Cloudflare-Worker-Secrets.
- Minimale Scopes (Sheets/Drive read/write nur wo nötig).
- Keine Secrets in `.env`-Dateien committen (`.gitignore` prüfen).

## OAuth-Minimalsetup

> **Revidierte Entscheidung (2026-06-22):** Die ursprüngliche Service-Account-/n8n-Kombination wurde verworfen, weil n8n Cloud ein kostenpflichtiges Abo ist (siehe `N8N_HOSTING_DECISION.md` §9b). Stattdessen: **Google Apps Script Web App**, gebunden an das CRM-Light-Sheet selbst — komplett kostenlos (Google-Workspace-Kontingente), kein Service Account, kein OAuth-Flow, kein externer Host nötig. Details: `GOOGLE_SHEETS_CRM_SETUP.md`.

- Gmail/Calendar (optional, derzeit nicht im Scope) bleiben bei Bedarf OAuth — unverändert, betrifft nicht die Lead-Pipeline.
- Credential-Ort: keine Credentials im Repo, keine Secrets committen. Apps-Script-URL
  und Auth-Token werden atomar als verschlüsseltes `LEAD_WEBHOOK_CONFIG`-Secret in
  Cloudflare Pages gehalten. Die technisch öffentliche URL ist keine Authentifizierung.
- Minimaltest: ausschließlich über `/api/lead` im isolierten Pages-Preview senden,
  im Sheet prüfen und die markierte Testzeile kontrolliert entfernen. Keine direkte
  POST-Anfrage an Apps Script. Ablauf: `docs/crm/WEBHOOK_AUTH_CUTOVER.md`.
- Status: keine Live-Aktivierung ohne Freigabe.
