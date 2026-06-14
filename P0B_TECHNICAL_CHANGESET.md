# P0B_TECHNICAL_CHANGESET — HSB-Boden

> Stand: 2026-06-14. Planung. Dateien werden in P0A NICHT geändert; Tabelle beschreibt potenzielle P0B-Änderungen.

| Potenziell betroffene Datei | Art der Änderung | Zweck | Risiko | Test | Freigabe benötigt |
|-----------------------------|------------------|-------|--------|------|-------------------|
| `src/pages/api/lead.ts` (neu) | Neuanlage | serverseitiger Lead-Endpoint | mittel | Unit + Integration (Mock-n8n) | ja |
| `src/lib/leadSchema.ts` (neu, optional) | Neuanlage | zod-Validierung Lead-Felder | niedrig | Unit | ja |
| `src/` Formular-Anbindung | Anpassung | Form → Endpoint statt direkt | mittel | E2E (nach Freigabe) | ja |
| `ops/n8n/hsb-boden-lead-intake.json` (vorhanden) | nur Abgleich/ggf. Anpassung | Endpoint↔Workflow-Mapping | mittel | Integration | ja |
| `src/data/site.ts` (referenziert `PUBLIC_LEAD_ENDPOINT`) | ggf. Anpassung | Endpoint-URL/Env-Bindung | niedrig | Build/Check | ja |
| `wrangler.toml` | ggf. Vars/Bindings | n8n-URL/Secret-Bindung | mittel | deploy:dry-run | ja (separat) |
| Testdateien (neu) | Neuanlage | Validierungs-/Integrationstests | niedrig | test:run | ja |

## Bewusst NICHT in P0B
- Bestehende Seiteninhalte (`src/pages/*`) ohne separate Freigabe.
- `package.json`/Lockfiles (zod bereits vorhanden — keine neue Dependency erwartet).
- `.astro/data-store.json`.

## Hinweis
Jede dieser Änderungen ist Website-Code und erfordert ausdrückliche Freigabe (in der aktuellen Phase verboten).
