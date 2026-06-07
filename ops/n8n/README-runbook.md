# Runbook — HSB-Boden Lead-Pipeline (lokales n8n + Cloudflare Tunnel)

> Betriebsanleitung für die selbst-gehostete, kostenfreie Variante. Vollständiger
> Umsetzungsplan: `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`.

## Voraussetzungen (verifiziert 2026-06-07)
- n8n Community `2.8.4` (`/opt/homebrew/bin/n8n`)
- **Node 20.x Pflicht** — `node@20` via Homebrew (`/opt/homebrew/opt/node@20/bin`).
  System-Node 26 wird von n8n abgelehnt.
- `cloudflared` `2026.5.2` (kostenfreier Tunnel)

## Start (lokal)
```bash
# 1) n8n starten (pinnt node@20)
./ops/n8n/run-n8n.sh
# → wartet bis: "Editor is now accessible via: http://localhost:5678"
```

## Workflow publishen (EINMALIG nötig, sonst kein production-Webhook)
n8n 2.x registriert den Production-Webhook NUR für **publizierte** Workflows.
Die CLI (`publish:workflow`) reicht nicht — Publish ist eine UI-Aktion:
1. `http://localhost:5678` öffnen (Erststart: lokalen Owner-Account anlegen).
2. Workflow „hsb-boden-lead-intake" öffnen → **Publish** (oben rechts).
3. Verifizieren: `sqlite3 ~/.n8n/database.sqlite "SELECT count(*) FROM workflow_published_version;"` → `1`.

## Öffentlich erreichbar machen (Cloudflare Tunnel)
```bash
# Quick-Tunnel (ephemere URL, wechselt bei Neustart):
# WICHTIG: --protocol http2 erzwingen. QUIC/UDP ist in dieser Umgebung instabil
# (verifiziert 2026-06-07: QUIC → HTTP 000; http2/TCP → HTTP 200).
cloudflared tunnel --url http://localhost:5678 --protocol http2
# → liefert https://<random>.trycloudflare.com
```
Danach in `run-n8n.sh` `WEBHOOK_URL="https://<url>/"` setzen und n8n neu starten,
damit n8n korrekte externe Webhook-URLs erzeugt.

Für eine **stabile** URL (statt wechselnder Quick-Tunnel-URL): benannter Tunnel
`cloudflared tunnel create hsb-n8n` + DNS-Route auf eine feste Subdomain.

## Webhook testen (Fake-Daten, keine echten Personendaten)
```bash
curl -s -X POST <BASIS-URL>/webhook/hsb-boden-lead-intake \
  -H "Content-Type: application/json" -d '{"foo":"bar"}' -w "\n[%{http_code}]\n"
# Erwartet: [400] invalid_payload  → Webhook + Validierung greifen
```

## E-Mail-Zustellung aktivieren
Node „Lead per E-Mail senden" braucht ein **SMTP-Credential** + echte
`fromEmail`/`toEmail` (aktuell Platzhalter `*.invalid`). Über die UI setzen, dann
**erneut Publish**. Secrets gehören NICHT ins Repo/Memory.

## Bekannte Einschränkungen / Risiken
- **Kein echter 24/7-Betrieb auf dem Mac:** Bei Sleep/Neustart fällt n8n + Tunnel aus.
  Für Dauerbetrieb `caffeinate -s` nutzen oder später VPS erwägen.
- **Quick-Tunnel-URL ist instabil** — bei jedem Neustart neu. Production braucht stabile Subdomain.
- **Öffentlicher Webhook ohne Auth** — `PUBLIC_LEAD_ACCESS_KEY` ist im Browser sichtbar,
  also kein echtes Secret. Honeypot/Rate-Limit als Folge-Härtung einplanen.

## Stoppen
```bash
kill $(lsof -ti tcp:5678)   # n8n
# Tunnel: das cloudflared-Terminal mit Strg+C beenden
```
