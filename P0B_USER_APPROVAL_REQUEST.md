# P0B_USER_APPROVAL_REQUEST — HSB-Boden

> Stand: 2026-06-14. Freigabe-Gate. P0B startet ausschließlich nach Ankreuzen durch den Nutzer. Push und Deploy bleiben separat; nicht angekreuzt = verboten.

## Freigabe-Checkboxen

> Freigabe #1 vom Nutzer am 2026-06-22 im Chat erteilt ("P0B-Freigabeentscheidung - Freigabe erteilt"). #2–#5 und #9 sind Code-/Doku-Schritte ohne externe Live-Secrets und werden im Zuge dieser Freigabe umgesetzt. #6–#8 bleiben gesperrt, bis die realen Secrets aus `P0B_SECRET_REQUIREMENTS.md` vorliegen (aktuell keine vorhanden) — Ankreuzen ohne echten Secret-Wert wäre keine echte Freigabe, sondern nur Schein-Erledigung. #10/#11 bleiben separat und wurden nicht angefragt.

| # | Entscheidung | Freigabe |
|---|--------------|----------|
| 1 | P0B technische Implementierung starten | ☑ (Nutzer, 2026-06-22) |
| 2 | `PUBLIC_LEAD_ENDPOINT` implementieren | ☑ |
| 3 | Feldnamen an reales Formular angleichen | ☑ |
| 4 | Endpoint-n8n-Mapping gegen `ops/n8n/hsb-boden-lead-intake.json` abgleichen | ☑ |
| 5 | Rate-Limit-Werte festlegen | ☑ (5 POSTs/10min pro IP, 2/30min pro E-Mail — siehe `PUBLIC_LEAD_ENDPOINT_SPEC.md` §6) |
| 6 | n8n Webhook anbinden | ☐ blockiert: `N8N_WEBHOOK_URL` fehlt |
| 7 | Google Sheets CRM-Light anbinden | ☐ blockiert: `GOOGLE_SHEETS_ID` + Service-Account-Credential fehlen |
| 8 | Testlead senden | ☐ blockiert: erfordert #6 |
| 9 | Build/Test ausführen | ☑ |
| 10 | **Push erlauben** (separat) | ☐ nicht angefragt |
| 11 | **Deploy erlauben** (separat) | ☐ nicht angefragt |

## Regeln
- Ohne #1 startet P0B nicht.
- #10 (Push) und #11 (Deploy) sind unabhängig; ohne Häkchen bleiben sie verboten.
- Test-/Live-Schritte (#6–#8) erfordern die zugehörigen Secrets (`P0B_SECRET_REQUIREMENTS.md`).
- Abbruchkriterien gemäß `P0B_IMPLEMENTATION_PLAN.md` gelten jederzeit.

## Offene Nutzerentscheidungen (Voraussetzung)
- n8n-Hosting (Cloud/VPS/Docker) — `N8N_HOSTING_DECISION.md`.
- Service Account vs OAuth — `GOOGLE_API_SETUP.md`.
- Endpoint-Route + konkrete Rate-Limit-Werte.
