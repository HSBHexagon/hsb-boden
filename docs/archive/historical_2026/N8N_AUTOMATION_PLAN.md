# N8N_AUTOMATION_PLAN — HSB-Boden

> Nur Plan, keine Live-Automation. Stand: 2026-06-14. Vorhandener Workflow: `ops/n8n/hsb-boden-lead-intake.json` (laut Docs fertig).

## Pipelines (geplant)

1. **Kontaktformular → n8n Webhook → Google Sheets CRM-Light**
   - Website-Form (`PUBLIC_LEAD_ENDPOINT`) → n8n Webhook → Append-Row in CRM-Sheet.
   - Status: Webhook/SMTP inaktiv (P0-Blocker).
   - Dieser Schritt ist eine Planung. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.
2. **Leadimport → Dublettenprüfung → Scoring**
   - CSV/Manual-Import → Dedupe (Firma+E-Mail) → Score gemäß `ACQUISITION_SYSTEM_PLAN.md`.
3. **Follow-up-Erinnerungen**
   - Trigger auf `Follow-up-Datum` → Reminder (Mail/Task).
4. **Tagesreport**
   - Tägliche Zusammenfassung neuer Leads/Status an Outlook-Mail.
5. **Formularanfragen-Benachrichtigung**
   - Sofort-Benachrichtigung bei neuem Lead.

## Optional / später (nur bei Bedarf)
- CRM-/Supabase-Migration aus Sheets.
- AI-Klassifizierung/Scoring von Leads.

## Offene Entscheidungen
- n8n-Hosting: Cloud (empfohlen laut Docs) vs. lokal — P0.
- SMTP-Anbieter für Benachrichtigungen.
- Secrets nur in n8n-Credentials, nie im Repo.
- Test-Lead nur nach ausdrücklicher Freigabe auslösen.
