---
name: deploy-preview
description: Prüft die Website (Tests, Typen, Build) und deployt sie als Preview auf Cloudflare Pages. Nur manuell aufrufen. Production-Deploys laufen ausschließlich über den GitHub-Workflow, nie über diesen Skill.
disable-model-invocation: true
---

# Preview-Deploy der Website

Arbeitsordner: `apps/website`. Produktion ist hier **gesperrt** (`npm run deploy:production` bricht absichtlich ab). Production läuft nur über `.github/workflows/deploy-production.yml` (workflow_dispatch, Freigabe der Umgebung `production`).

## Ablauf
1. `git status --short` prüfen. Das Preview-Skript deployt mit `--commit-dirty=true`, also auch uncommittete Änderungen. Bei unerwarteten Änderungen anhalten und nachfragen.
2. `cd apps/website`.
3. `npm run test:run` — muss grün sein.
4. `npm run check` — Typprüfung, dauert ca. 45 Sekunden.
5. `npm run deploy:dry-run` — baut und prüft die Pages-Functions.
6. Erst nach Freigabe des Nutzers: `npm run deploy:preview` (Branch `preview`, Projekt `hsb-boden`).
7. Preview-URL aus der Wrangler-Ausgabe nennen und die geänderte Seite dort mit `curl -I` auf Status 200 prüfen.

## Nie
- Kein Production-Deploy, kein Push auf `main`.
- Keine Secrets ausgeben (`.dev.vars`, Tokens).
