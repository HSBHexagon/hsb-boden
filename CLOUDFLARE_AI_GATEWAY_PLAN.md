# CLOUDFLARE_AI_GATEWAY_PLAN — HSB-Boden

> Nur Plan, keine Live-Konfiguration. Stand: 2026-06-14.

## Grundsätze
- Cloudflare bleibt Hauptplattform.
- Workers Preview (`hsb-boden-preview`) bleibt Staging.
- Production (`hsb-boden`) später über `hsb-boden.de` Route / Custom Domain — nur nach Freigabe und WordPress-Cutover.
- Dieser Schritt ist eine Planung. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.

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
