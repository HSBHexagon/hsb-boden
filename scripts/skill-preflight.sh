#!/usr/bin/env bash
set -euo pipefail

task="${*:-}"

if [[ -z "$task" ]]; then
  echo "Nutzung: scripts/skill-preflight.sh <aufgabenbeschreibung>" >&2
  exit 1
fi

lower_task=$(printf '%s' "$task" | tr '[:upper:]' '[:lower:]')

declare -a picks

add_pick() {
  local item="$1"
  for existing in "${picks[@]:-}"; do
    [[ "$existing" == "$item" ]] && return 0
  done
  picks+=("$item")
}

add_pick "system-governor"

if [[ "$lower_task" == *"mehrschritt"* || "$lower_task" == *"multi-step"* || "$lower_task" == *"plan"* || "$lower_task" == *"integration"* || "$lower_task" == *"feature"* || "$lower_task" == *"workflow"* || "$lower_task" == *"n8n"* ]]; then
  add_pick "superpowers:using-git-worktrees"
  add_pick "superpowers:writing-plans"
  add_pick "superpowers:executing-plans"
fi

if [[ "$lower_task" == *"deploy"* || "$lower_task" == *"preview"* || "$lower_task" == *"cloudflare"* || "$lower_task" == *"wrangler"* || "$lower_task" == *"worker"* || "$lower_task" == *"dns"* ]]; then
  add_pick "cloudflare:wrangler"
  add_pick "context7 (direkter Cloudflare/Astro-Treffer, sonst offizielle Doku)"
  add_pick "superpowers:verification-before-completion"
fi

if [[ "$lower_task" == *"frontend"* || "$lower_task" == *"ui"* || "$lower_task" == *"hero"* || "$lower_task" == *"header"* || "$lower_task" == *"layout"* || "$lower_task" == *"mobile"* || "$lower_task" == *"design"* ]]; then
  add_pick "design-taste-frontend"
  add_pick "emil-design-eng"
  add_pick "Browser-/Viewport-Verifikation"
fi

if [[ "$lower_task" == *"fehler"* || "$lower_task" == *"bug"* || "$lower_task" == *"error"* || "$lower_task" == *"warn"* || "$lower_task" == *"fail"* || "$lower_task" == *"debug"* ]]; then
  add_pick "superpowers:systematic-debugging"
fi

if [[ "$lower_task" == *"test"* || "$lower_task" == *"tdd"* || "$lower_task" == *"schema"* || "$lower_task" == *"refactor"* ]]; then
  add_pick "superpowers:test-driven-development"
fi

if [[ "$lower_task" == *"docs"* || "$lower_task" == *"syntax"* || "$lower_task" == *"sdk"* || "$lower_task" == *"api"* || "$lower_task" == *"astro"* || "$lower_task" == *"react"* || "$lower_task" == *"tailwind"* ]]; then
  add_pick "context7 (nur bei direktem Library-Match)"
fi

printf 'Empfohlener Stack fuer: %s\n' "$task"
for item in "${picks[@]}"; do
  printf -- '- %s\n' "$item"
done
