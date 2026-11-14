# P0B_SECRET_REQUIREMENTS — HSB-Boden

> Stand: 2026-07-15. Nur Anforderungen, KEINE Werte. Secrets niemals im Repo, niemals im Frontend, niemals committen.

> **Revidiert 2026-06-22:** n8n entfällt (Abo-Kosten, siehe `N8N_HOSTING_DECISION.md` §9b). Zustellziel ist jetzt eine kostenlose Google-Apps-Script-Web-App (`GOOGLE_SHEETS_CRM_SETUP.md`), kein Service Account/OAuth mehr nötig.

| Secret | Zweck | Speicherort | Wann benötigt | Testmethode (ohne Wertausgabe) |
|--------|-------|-------------|---------------|--------------------------------|
| `LEAD_WEBHOOK_CONFIG` | Atomare Apps-Script-URL + Auth-Token | verschlüsseltes Cloudflare-Pages-Secret, getrennt für Preview/Production | authentifizierter Cutover | Mock-Config im Unit-Test; names-only Binding-Prüfung; E2E nur nach Freigabe |
| `LEAD_WEBHOOK_URL` | Vorübergehender unauthentifizierter Legacy-Fallback | verschlüsseltes Cloudflare-Pages-Secret | nur bis verifizierter Cutover | nach Production-Abnahme entfernen; Wert nie ausgeben |
| `HMAC_SECRET` / `FORM_SECRET` (optional) | Form-/Request-Signatur | Worker-Secret | bei Spam-Härtung | Signaturprüfung im Test |
| Rate-Limit-/Cloudflare-Config (optional) | Missbrauchsschutz | Cloudflare-Config | bei Rate-Limit | Negativtest 429 |

## Grundsätze
- Werte nur im vorgesehenen Secret-Tresor beziehungsweise als verschlüsselte
  Cloudflare-Pages-Secrets; Preview- und Production-Token niemals wiederverwenden.
- Keine Secrets in `.env` committen (`.gitignore` prüfen).
- Keine Secrets in Logs (siehe `PUBLIC_LEAD_ENDPOINT_SPEC.md` §10).
- Tests verwenden Mock-/Testwerte; Live-Werte erst nach Freigabe.
