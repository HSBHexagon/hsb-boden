# Copilot Instructions — hsb-boden

This is an **Astro 6** project (`output: "static"`) deployed to **Cloudflare Pages** with Pages Functions (`functions/`). It is the public website for HSB Bodenbeschichtungen — B2B lead generation for industrial floor coating services.

For full project rules, non-negotiables, and the deploy gate, see `AGENTS.md` in the repository root. This file summarizes the points most relevant to Copilot's code-completion and chat suggestions.

## Non-negotiables (see `AGENTS.md` for full list)

- Do not mutate or replace the live WordPress site (`hsb-boden.de`) from this repo.
- Do not claim Argelith/Zahna certification, partnership, or endorsement unless documented and approved.
- Do not publish exact customer locations, logos, or names without explicit approval.

## Critical priorities

- **SEO is critical.** This site relies on organic search traffic for lead generation.
- **Accessibility is critical.** Do not suggest changes that remove ARIA attributes, semantic HTML, alt text, or keyboard navigation.

## Never remove or break

- Sitemap generation (`@astrojs/sitemap` / `sitemap.xml` output)
- `robots.txt` generation
- Structured data / JSON-LD (`SEOHead.astro` and per-service `Service` schema)
- The Germany map / service-area visualization functionality
- Lead capture forms and their submission handling

If a suggested change would touch any of the above, prefer the smallest possible diff and flag it for explicit review rather than silently altering behavior.

## Working style

- **Prefer incremental changes** over large rewrites. Small, reviewable diffs.
- **Create PRs instead of direct modifications** to `main`. Do not suggest committing directly to `main`.
- **Verify the build before proposing changes are complete.** Required local gate (see `AGENTS.md`):
  ```bash
  npm run check
  npm run test:run
  npm run build
  ```
- **Production deploys remain approval-gated** (see `AGENTS.md` → Deploy Gate). Production deploys run via `deploy-production.yml` (`workflow_dispatch`-only, `wrangler pages deploy dist --project-name hsb-boden --branch=main`). Do not suggest enabling automatic production deploys on push to `main`.

## Tech stack quick reference

- Framework: Astro 6 (static output), TypeScript
- Styling: project design tokens — follow existing component conventions, do not introduce new design systems
- Deployment: Cloudflare Pages (project `hsb-boden`) via `wrangler pages deploy`; API routes live in `functions/` (Pages Functions)
- Tests: `npm run test:run`
- Type/lint check: `npm run check`

## Multi-agent context

This repository is worked on by multiple AI coding agents (Claude Code, GitHub Copilot, Gemini CLI, Codex). All agents follow the same `AGENTS.md`. If you notice a conflict between this file and `AGENTS.md`, `AGENTS.md` wins.
