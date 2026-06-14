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
- **Gemini CLI / Codex**: apply the same Non-Negotiables, Verification,
  Execution Stack, and Deploy Gate sections above.

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

## KI-System Pflichtstart (Shared-Memory-Governance)

Vor jeder Arbeit an diesem Repo:

1. Lies `~/KI-System/00_INDEX.md`.
2. Führe aus: `~/KI-System/tools/handoff.sh read`.
3. Lies die Registry: `~/KI-System/08_System/config/canonical-projects.json`.
4. Verifiziere den Pfad:
   `cd "$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)" && ~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden`

Niemals in diesen Pfaden arbeiten:

- Backup-Pfade (`*KI-System-Backup*`, `*Backup*`, `*.Trash*`)
- `/Users/joelcherinodiaz/Projects/hsb-boden` (älterer Klon, NICHT kanonisch)
- Rohimporte unter `brain/07_imported/`
- leere brain-Projektordner (z. B. `brain/03_projects/hexafloor`)

Kanonischer Arbeitsrepo-Pfad (Stand 2026-06-14, belegt durch letzte Claude-Code-Session + git log + GitHub-Remote):
`/Users/joelcherinodiaz/KI-System/01_Wahrheitsquelle/_MERGED_20260613/AI-Memory-Hub/projects/hsb-boden`

Keine Website-Code-Änderung ohne Freigabe. Kein Push, kein Production-Deploy ohne Freigabe.
