# P0B_SECRET_REQUIREMENTS — HSB-Boden

> Stand: 2026-06-14. Nur Anforderungen, KEINE Werte. Secrets niemals im Repo, niemals im Frontend, niemals committen.

| Secret | Zweck | Speicherort | Wann benötigt | Testmethode (ohne Wertausgabe) |
|--------|-------|-------------|---------------|--------------------------------|
| `N8N_WEBHOOK_URL` | Endpoint → n8n Weiterleitung | n8n-Credential / Worker-Secret | bei Endpoint-Integration | Mock-URL im Test; Live nur nach Freigabe |
| `GOOGLE_SHEETS_ID` | Ziel-CRM-Sheet | Worker-Env/Secret | bei Sheets-Anbindung | Test-Sheet-ID separat |
| `GOOGLE_SERVICE_ACCOUNT_JSON` oder OAuth-Credentials | Sheets-Schreibzugriff | sicherer Secret-Store / n8n-Credential | bei Sheets-Anbindung | Append-Test gegen Test-Sheet |
| `HMAC_SECRET` / `FORM_SECRET` (optional) | Form-/Request-Signatur | Worker-Secret | bei Spam-Härtung | Signaturprüfung im Test |
| Rate-Limit-/Cloudflare-Config (optional) | Missbrauchsschutz | Cloudflare-Config | bei Rate-Limit | Negativtest 429 |
| Notification-Ziel (optional, z. B. SMTP/Mail) | Benachrichtigung/Report | n8n-Credential | bei Reports | Mock-Versand |

## Grundsätze
- Werte nur in externem Secret-Store (`~/KI-System/05_Secrets/`) bzw. n8n-Credentials.
- Keine Secrets in `.env` committen (`.gitignore` prüfen).
- Keine Secrets in Logs (siehe `PUBLIC_LEAD_ENDPOINT_SPEC.md` §10).
- Tests verwenden Mock-/Testwerte; Live-Werte erst nach Freigabe.
