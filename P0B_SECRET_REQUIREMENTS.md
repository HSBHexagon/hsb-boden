# P0B_SECRET_REQUIREMENTS — HSB-Boden

> Stand: 2026-06-14. Nur Anforderungen, KEINE Werte. Secrets niemals im Repo, niemals im Frontend, niemals committen.

> **Revidiert 2026-06-22:** n8n entfällt (Abo-Kosten, siehe `N8N_HOSTING_DECISION.md` §9b). Zustellziel ist jetzt eine kostenlose Google-Apps-Script-Web-App (`GOOGLE_SHEETS_CRM_SETUP.md`), kein Service Account/OAuth mehr nötig.

| Secret | Zweck | Speicherort | Wann benötigt | Testmethode (ohne Wertausgabe) |
|--------|-------|-------------|---------------|--------------------------------|
| `LEAD_WEBHOOK_URL` | Endpoint → Apps-Script-Weiterleitung | Cloudflare-Worker-Secret | bei Endpoint-Integration | Mock-URL im Test; Live nur nach Freigabe |
| `HMAC_SECRET` / `FORM_SECRET` (optional) | Form-/Request-Signatur | Worker-Secret | bei Spam-Härtung | Signaturprüfung im Test |
| Rate-Limit-/Cloudflare-Config (optional) | Missbrauchsschutz | Cloudflare-Config | bei Rate-Limit | Negativtest 429 |

## Grundsätze
- Werte nur in externem Secret-Store (`~/KI-System/05_Secrets/`) bzw. Cloudflare-Worker-Secrets.
- Keine Secrets in `.env` committen (`.gitignore` prüfen).
- Keine Secrets in Logs (siehe `PUBLIC_LEAD_ENDPOINT_SPEC.md` §10).
- Tests verwenden Mock-/Testwerte; Live-Werte erst nach Freigabe.
