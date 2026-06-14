# P0B_IMPLEMENTATION_PLAN — HSB-Boden

> Stand: 2026-06-14. Planung. P0B startet erst nach ausdrücklicher Nutzerfreigabe (`P0B_USER_APPROVAL_REQUEST.md`).

## Zweck
Technische Umsetzung der Lead-Pipeline gemäß P0A-Spezifikationen: serverseitiger Endpoint, n8n-Anbindung, Google-Sheets-CRM-Light, kontrollierter Testlead.

## Grenzen
- P0B erst nach Nutzerfreigabe.
- Kein Push ohne separate Push-Freigabe.
- Kein Deploy ohne separate Deploy-Freigabe.
- Kein Production-Cutover, kein Cloudflare Production Route/Custom Domain.
- Keine öffentliche Aktivierung ohne Testfreigabe.

## Vorgesehene technische Schritte (Reihenfolge)
1. Feldnamenabgleich Endpoint ↔ reales Formular (`firstName`, `lastName`, `privacyConsent`, `areaSize`, `industry`, `projectType`, `loads`, `liveOperation`, `description`).
2. `PUBLIC_LEAD_ENDPOINT_SPEC.md` an reale Felder angleichen.
3. Endpoint-n8n-Mapping gegen `ops/n8n/hsb-boden-lead-intake.json` abgleichen.
4. Konkrete Rate-Limit-Werte festlegen.
5. `PUBLIC_LEAD_ENDPOINT` implementieren (serverseitig, Astro/Workers).
6. Validierung (zod) + Spam-/Rate-Limit + Consent-Prüfung.
7. Weiterleitung an n8n-Webhook (URL aus Secret/Env).
8. Google-Sheets-CRM-Light schreiben (Mock zuerst, dann nach Freigabe live).
9. Kontrollierter Testlead.

## Nicht enthalten
- Production-Cutover
- Cloudflare Production Deploy
- öffentliche Aktivierung ohne Testfreigabe

## Abhängigkeiten
- n8n-Hosting-Entscheidung (`N8N_HOSTING_DECISION.md`).
- Externe Secrets (`P0B_SECRET_REQUIREMENTS.md`).
- Service Account vs OAuth (`GOOGLE_API_SETUP.md` / `GOOGLE_SHEETS_CRM_SETUP.md`).

## Abbruchkriterien
- Website-Code-Diff unerwartet/ohne Freigabe.
- Secret im Repo.
- Falscher Repo-Pfad (Guard-Fehler).
- Fehlende/unklare Freigabe.
