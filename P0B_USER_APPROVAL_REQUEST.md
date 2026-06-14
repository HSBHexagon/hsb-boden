# P0B_USER_APPROVAL_REQUEST — HSB-Boden

> Stand: 2026-06-14. Freigabe-Gate. P0B startet ausschließlich nach Ankreuzen durch den Nutzer. Push und Deploy bleiben separat; nicht angekreuzt = verboten.

## Freigabe-Checkboxen

| # | Entscheidung | Freigabe |
|---|--------------|----------|
| 1 | P0B technische Implementierung starten | ☐ |
| 2 | `PUBLIC_LEAD_ENDPOINT` implementieren | ☐ |
| 3 | Feldnamen an reales Formular angleichen | ☐ |
| 4 | Endpoint-n8n-Mapping gegen `ops/n8n/hsb-boden-lead-intake.json` abgleichen | ☐ |
| 5 | Rate-Limit-Werte festlegen | ☐ |
| 6 | n8n Webhook anbinden | ☐ |
| 7 | Google Sheets CRM-Light anbinden | ☐ |
| 8 | Testlead senden | ☐ |
| 9 | Build/Test ausführen | ☐ |
| 10 | **Push erlauben** (separat) | ☐ |
| 11 | **Deploy erlauben** (separat) | ☐ |

## Regeln
- Ohne #1 startet P0B nicht.
- #10 (Push) und #11 (Deploy) sind unabhängig; ohne Häkchen bleiben sie verboten.
- Test-/Live-Schritte (#6–#8) erfordern die zugehörigen Secrets (`P0B_SECRET_REQUIREMENTS.md`).
- Abbruchkriterien gemäß `P0B_IMPLEMENTATION_PLAN.md` gelten jederzeit.

## Offene Nutzerentscheidungen (Voraussetzung)
- n8n-Hosting (Cloud/VPS/Docker) — `N8N_HOSTING_DECISION.md`.
- Service Account vs OAuth — `GOOGLE_API_SETUP.md`.
- Endpoint-Route + konkrete Rate-Limit-Werte.
