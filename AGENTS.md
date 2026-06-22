# Project Rules: hsb-boden

## Purpose

Build a parallel Astro/Cloudflare relaunch for HSB that generates organic B2B leads while preserving the current WordPress live site until final approval.

## Non-Negotiables

- Do not mutate or replace the live WordPress site from this repo.
- Do not claim Argelith/Zahna certification, partnership, or endorsement unless documented and approved.
- Do not publish exact customer locations, logos, or names without explicit approval.
- Do not use competitor customer lists publicly.
- Do not activate or automate email campaigns to purchased contacts without legal review.

## Verification

Run before completion claims:

```bash
npm run test:run
npm run check
npm run build
```

For frontend changes, verify desktop and mobile rendering before launch.

## Execution Stack

For multi-step implementation, deploy, launch, or integration work on this
project:

- Use `system-governor` first to recover shared state before acting from chat.
- Run `scripts/skill-preflight.sh "<task>"` when the task spans multiple areas
  and the relevant skill stack is not obvious from the first read.
- Prefer an isolated git worktree for anything larger than a tiny one-file fix.
  Project-local path is `.worktrees/<branch-name>`.
- Use `cloudflare:wrangler` before changing deploy commands, Wrangler config,
  bindings, or production/preview flow.
- For Astro, Wrangler, Cloudflare, or SDK syntax questions, prefer official
  docs first and use `context7` when it has a direct library match.
- If `context7` has no direct match, say so briefly and fall back to official
  Cloudflare or framework docs instead of guessing.
- For debugging, do not patch first. Reproduce, isolate, then fix.

## Deploy Gate

For preview or production work, verify in this order:

1. `npm run test:run`
2. `npm run check`
3. `npm run build`
4. `npm run deploy:dry-run`
5. browser or HTTP verification of one real user path

Production deploys remain blocked until the lead pipeline is live and the
WordPress site is intentionally cut over.

## Content Model

Structured content lives under `src/data`. Add new service, industry, reference, or article entries there and let routes generate pages.

## Design Direction

Technical, industrial, robust, quiet B2B interface. Avoid generic agency visuals, decorative hero gimmicks, or unsupported trust claims.

## Multi-Agent Guardrails

This repository is worked on by multiple AI coding agents: Claude Code,
GitHub Copilot, Gemini CLI, and Codex. All agents must follow this file.
Agent-specific notes:

- **Claude Code**: see global `~/.claude/CLAUDE.md` (SCMS Governor-Loop) for
  cross-session memory; this file (`AGENTS.md`) is the project-level source
  of truth and wins on conflict.
- **GitHub Copilot**: see `.github/copilot-instructions.md` for a condensed
  summary tuned for inline-completion/chat context.
- **Gemini CLI**: only optional research/review assistance. Because Google has
  announced the June 18, 2026 stop for Gemini CLI / Gemini Code Assist requests
  in the Individuals / Google AI Pro / Ultra context, Gemini is not an
  operational critical path for this repo.
- **Codex**: apply the same Non-Negotiables, Verification, Execution Stack,
  and Deploy Gate sections above.

Shared rules for all agents:

- **CI/CD is owned by this repo's `.github/workflows/`.** `quality.yml` runs
  `npm run check`, `npm run build`, `npm run test:run` on push/PR to `main`.
  `security.yml` runs CodeQL, Dependency Review, and secret scanning.
  `lighthouse.yml` runs Lighthouse CI against `.lighthouserc.json` thresholds.
  `deploy-preview.yml` deploys PR previews to Cloudflare Workers preview env.
  `deploy-production.yml` is `workflow_dispatch`-only (manual) per the Deploy
  Gate above — do not change it to an automatic trigger without first
  confirming the lead pipeline is live and WordPress has been cut over.
- **Pin third-party GitHub Actions to a commit SHA** with a version comment
  (e.g. `actions/checkout@<sha> # v4.2.2`), matching the existing pattern in
  `quality.yml`. Do not introduce unpinned `@v4`/`@main`-style references.
- **Open PRs for non-trivial changes**; do not commit directly to `main`.
- **No invented numbers, prices, ratings, or claims** (see Non-Negotiables).
  Mark any placeholder data explicitly as `MOCK_DATA`.
- **Security/SEO/Accessibility/Performance audit reports** (e.g.
  `SECURITY_FINAL_REPORT.md`, `SEO_REPORT.md`, `ACCESSIBILITY_REPORT.md`,
  `PERFORMANCE_REPORT.md`) must be based on actual tool output (osv-scanner,
  Lighthouse, build output), not estimates.
- **Codex**: keep context windows focused — if modifying styling, provide
  both the component and `tailwind.config.mjs` context.

### Modularity Mandate

- **File Size Limit:** No source file (TS/JS) may exceed **500 lines**.
- **Data Modularization:** Large data arrays (e.g., services, industries, references) must be split into individual files under `src/data/<domain>/`.
- **Refactoring Requirement:** If a file grows near the 500-line limit during a task, the agent MUST plan and execute its modularization as part of the completion.

### Google Jules

- Jules (`google-labs-jules[bot]`) may create branches, commits, and pull
  requests, and may fix failing CI/workflows — same as any other agent in
  this file.
- Jules may **auto-merge** its own PRs into `main` once all required status
  checks are green (`validate`, `build-and-test`, `Dependency Review`,
  `Secret Scanning`, `lighthouse`, `deploy`, `Analyze (javascript-typescript)`,
  `Analyze (actions)` — enforced by the "Protect Main" ruleset). This is a
  deliberate policy: Jules is registered as a `pull_request`-scoped bypass
  actor on that ruleset, so its PRs do not require a separate human approval
  once CI is green.
- This does **not** change the non-negotiables: `deploy-production.yml`
  remains `workflow_dispatch`-only and off-limits for Jules and all other
  agents; WordPress (`hsb-boden.de`), Argelith/Zahna claims, and customer
  data rules apply unconditionally to Jules as well.
- Jules must not push directly to `main` — only via pull request, so that CI
  and required status checks always run before the change lands.

## Kanonischer Arbeitsrepo-Pfad

`/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden` (Registry:
`~/KI-System/08_System/config/canonical-projects.json`). Der frühere
`_MERGED_20260613`-Pfad ist archiviert und nicht kanonisch.

Keine Website-Code-Änderung ohne Freigabe. Kein Push, kein Production-Deploy
ohne Freigabe.
