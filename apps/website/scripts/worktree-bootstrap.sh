#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Dieses Skript muss innerhalb eines Git-Repos gestartet werden." >&2
  exit 1
fi

repo_root=$(git rev-parse --show-toplevel)
branch_name="${1:-}"

if [[ -z "$branch_name" ]]; then
  echo "Nutzung: scripts/worktree-bootstrap.sh <branch-name>" >&2
  exit 1
fi

worktree_root="$repo_root/.worktrees"
worktree_path="$worktree_root/$branch_name"

mkdir -p "$worktree_root"

if ! git check-ignore -q .worktrees; then
  echo ".worktrees ist nicht ignoriert. Bitte zuerst .gitignore aktualisieren." >&2
  exit 1
fi

if [[ -e "$worktree_path" ]]; then
  echo "Worktree existiert bereits: $worktree_path" >&2
  exit 1
fi

git worktree add "$worktree_path" -b "$branch_name"

cd "$worktree_path"

if [[ ! -d node_modules ]]; then
  npm install
fi

npm run test:run
npm run check
npm run build

echo "Worktree bereit: $worktree_path"
