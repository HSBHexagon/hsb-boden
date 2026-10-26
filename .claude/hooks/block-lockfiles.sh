#!/usr/bin/env bash
# PreToolUse-Hook: blockiert direkte Edits/Writes an Lockfiles.
# Lockfiles ändern sich nur durch bewusste Installationen (npm install/ci über Bash),
# nie durch handgeschriebene Edits. Exit 2 + stderr => Claude Code bricht den Tool-Call ab.

set -euo pipefail

payload="$(cat)"

# file_path ohne jq-Abhängigkeit extrahieren (wie block-secrets.sh).
file_path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$file_path" ]; then
  exit 0
fi

base="$(basename "${file_path//\//}")"

case "$base" in
  package-lock.json|npm-shrinkwrap.json|pnpm-lock.yaml|yarn.lock)
    echo "BLOCKIERT: '$file_path' ist ein Lockfile." >&2
    echo "Lockfiles nicht per Edit/Write ändern. Abhängigkeiten über 'npm install <paket>' bzw. 'npm ci' im Ordner apps/website ändern und nur bewusst committen." >&2
    exit 2 ;;
esac

exit 0
