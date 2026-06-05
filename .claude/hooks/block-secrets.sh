#!/usr/bin/env bash
# PreToolUse-Hook: blockiert Edits/Writes an Secret-Dateien.
# Cloudflare/Astro: .dev.vars enthält Worker-Secrets, .env* lokale Konfiguration.
# Exit 2 + stderr => Claude Code bricht den Tool-Call ab und zeigt die Meldung.

set -euo pipefail

# stdin liefert das PreToolUse-Event als JSON (tool_input.file_path).
payload="$(cat)"

# file_path ohne jq-Abhängigkeit extrahieren (robust gegen fehlendes jq).
file_path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

# Kein Pfad erkannt -> nichts zu blocken.
if [ -z "$file_path" ]; then
  exit 0
fi

base="$(basename "$file_path")"

# Geschützte Muster (Basename-basiert, deckt auch Pfade in Unterordnern ab).
case "$base" in
  .dev.vars|.dev.vars.*)
    blocked=1 ;;
  .env|.env.*)
    blocked=1 ;;
  *.pem|*.key|id_rsa|id_ed25519)
    blocked=1 ;;
  *)
    blocked=0 ;;
esac

if [ "$blocked" -eq 1 ]; then
  echo "BLOCKIERT: '$file_path' enthält Secrets (Cloudflare/Env)." >&2
  echo "Secrets werden nicht über Edit/Write geändert. Nutze 'wrangler secret put' bzw. bearbeite die Datei manuell außerhalb von Claude." >&2
  echo "Offen laut Memory: Token cfat_Tc90 muss rotiert werden." >&2
  exit 2
fi

exit 0
