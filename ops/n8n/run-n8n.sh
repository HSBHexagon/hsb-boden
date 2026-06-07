#!/usr/bin/env bash
# n8n Community lokal starten — pinnt die kompatible Node-Version (20.x).
# Hintergrund: Das System-Node (26.x) wird von n8n abgelehnt
# (unterstützt: >=20.19 <=24.x). node@20 liegt unter Homebrew bereit.
set -euo pipefail

export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
export N8N_DIAGNOSTICS_ENABLED=false
export N8N_PERSONALIZATION_ENABLED=false

# WEBHOOK_URL: erst setzen, wenn n8n öffentlich über den Cloudflare-Tunnel
# erreichbar ist (siehe Plan Phase 2 / Runbook). Lokal leer lassen.
# export WEBHOOK_URL="https://<stabile-tunnel-url>/"

echo "node: $(node -v)  |  n8n start auf http://localhost:5678"
exec n8n start
