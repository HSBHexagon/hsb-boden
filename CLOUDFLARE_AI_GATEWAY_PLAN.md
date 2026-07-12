# CLOUDFLARE_AI_GATEWAY_PLAN — HSB-Boden

> Ursprünglicher Plan, Stand: 2026-06-14. Die isolierte Preview-Ausführung vom
> 2026-07-12 ist im
> `docs/cloudflare/GITHUB_MODELS_POC_EXECUTION_REPORT.md` dokumentiert.

## Grundsätze
- Cloudflare bleibt Hauptplattform.
- Workers Preview (`hsb-boden-preview`) bleibt Staging.
- Production (`hsb-boden`) später über `hsb-boden.de` Route / Custom Domain — nur nach Freigabe und WordPress-Cutover.
- Dieser Plan autorisiert keine Production-Aktivierung, keinen Production-Deploy
  oder Production-Cutover ohne ausdrückliche Freigabe. Die
  isolierte Preview-Route wurde ausschließlich für einen Test geöffnet und ist
  jetzt wieder deaktiviert; Production blieb unverändert.

## Verifizierter Preview-PoC-Stand (2026-07-12)

- Pages Preview: `AI_POC_ENABLED=false` im finalen Zustand; Production besitzt
  keine PoC-Variablen und behielt nur `LEAD_WEBHOOK_URL`.
- Gateway: `hsb-boden-ai`, authentifiziert, Log-Sammlung deaktiviert und Cache
  deaktiviert.
- Custom Provider: `github-models` mit `https://models.github.ai` und einer
  Secret-Store-Credential im Scope `ai_gateway`.
- Ergebnis: Direkte GitHub-Models-Inferenz mit dem erlaubten DeepSeek-Fallback
  war erfolgreich; die Cloudflare-Custom-Provider-Weiterleitung lieferte
  reproduzierbar `404`. Daher bleibt die Route deaktiviert und die
  Inferenz-Performance ist nicht bewertet.

## AI Gateway
- Nur für konkrete AI-Features einsetzen (z. B. Lead-Klassifizierung, Content-Hilfe) — kein Selbstzweck.
- Keine Tokens/Keys im Frontend. Secrets ausschließlich serverseitig (Worker-Bindings / Wrangler Secrets).
- Rate Limits für Formular-/API-Endpunkte.

## Bewusst NICHT ohne konkreten Nutzen
- Vectorize, D1, KV, R2, AI Search — erst bei belegtem Bedarf.

## Environments
- Dev/Preview und Production strikt trennen (`wrangler.toml` `[env.production]`).
- `deploy-production.yml` bleibt `workflow_dispatch`-only (manuell).
- Production Route / Custom Domain und Production-Deploy bleiben bis zur ausdrücklichen Freigabe blockiert.
