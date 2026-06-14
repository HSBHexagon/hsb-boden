# P0_IMPLEMENTATION_APPROVAL_CHECKLIST — HSB-Boden

> P0A → P0B Freigabe-Gate. Stand: 2026-06-14. P0B startet erst nach ausdrücklicher Nutzerfreigabe.

## 1. Was darf P0B ändern?
- Serverseitigen Lead-Endpoint implementieren (`/api/lead`, gemäß `PUBLIC_LEAD_ENDPOINT_SPEC.md`).
- n8n-Workflow live anbinden (gemäß `N8N_HOSTING_DECISION.md`).
- Google-Sheets-CRM-Light anbinden (gemäß `GOOGLE_SHEETS_CRM_SETUP.md`).
- Zugehörige Tests + Doku.

## 2. Was bleibt verboten?
- Push / Production-Deploy / Production-Cutover ohne separate Freigabe.
- Secrets im Repo / Frontend.
- Echter Massenversand an gekaufte Kontakte ohne Rechts-Review.
- Änderung der Live-WordPress-Site.
- `.astro/data-store.json` committen.
- `git add .`, `git restore`, `git reset`, `git clean`.

## 3. Potenziell betroffene Dateien in P0B

| Datei/Bereich | Art der Änderung |
|---------------|------------------|
| `src/pages/api/lead.ts` (neu) | Endpoint-Implementierung |
| `src/` Formularanbindung | Anbindung an Endpoint |
| `wrangler.toml` | ggf. Bindings/Vars (nur nach Freigabe) |
| `package.json` | ggf. keine neue Dependency nötig (`zod` vorhanden) |
| Tests | Unit/Integration für Endpoint |

> Hinweis: Jede dieser Änderungen ist Website-Code und erfordert ausdrückliche Freigabe (in P0A verboten).

## 4. Extern benötigte Secrets
- n8n Webhook-URL.
- Google Service-Account/OAuth.
- SMTP-Credentials.
- (alle extern, nie im Repo)

## 5. Tests, die vor Umsetzung grün sein müssen
- `npm run test:run`
- `npm run check`
- `npm run build`
- `npm run deploy:dry-run`

## 6. Erforderliche Nutzerentscheidungen
- n8n-Hosting (A/B/C).
- Endpoint-Route + Rate-Limit-Werte.
- Service Account vs OAuth.
- Push-Freigabe ja/nein.
- Deploy-Freigabe ja/nein.

## 7. Freigabe-Checkboxen

| Entscheidung | ja/nein |
|--------------|---------|
| PUBLIC_LEAD_ENDPOINT implementieren | ☐ |
| n8n Webhook live einrichten | ☐ |
| Google Sheets anbinden | ☐ |
| Testlead senden | ☐ |
| Push erlauben | ☐ |
| Deploy erlauben | ☐ |

## 8. Abbruchkriterien (sofortiger STOP)
- Website-Code-Diff unerwartet ≠ 0 ohne Freigabe.
- Secret im Repo entdeckt.
- Falscher Repo-Pfad (`assert_canonical_project_path.sh` schlägt fehl).
- Fehlende oder unklare Freigabe.

## 9. Nächster Entscheidungspunkt
Nutzer füllt Checkboxen (Abschnitt 7) + Entscheidungen (Abschnitt 6) aus → erst dann P0B.
