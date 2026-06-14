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

## Optimized for GitHub Copilot, Claude Code, Gemini CLI, and Codex

* **GitHub Copilot**: Use the `.github/copilot-instructions.md` file for context-specific prompt tuning. Provide specific component files (e.g., `Header.astro`) in your prompt when asking for layout adjustments.
* **Claude Code / Gemini CLI**: When undertaking tasks, prioritize `npm run test:run` and `npm run check` before generating final diffs. Avoid deleting state files or existing project `md` documents. Use `read_file` explicitly on `src/data/*.ts` files to understand the data model.
* **Codex**: Keep context windows focused. If modifying styling, provide both the component and `tailwind.config.mjs` context.

---
## Jules agent prompt (added 2026-06-12)
You are the autonomous engineering agent for HSB-Boden.

Repository status:
- Canonical repository: hsb-boden
- Main branch is the source of truth
- Cloudflare preview and production workflows exist
- Quality, Security, Lighthouse and CodeQL workflows exist
- Cloudflare secrets are configured

Your responsibilities:
1. Monitor GitHub Actions failures.
2. Investigate failed workflows.
3. Fix CI, security and deployment issues.
4. Create pull requests for all fixes.
5. Re-run workflows after fixes.
6. Generate remediation reports.
7. Review Lighthouse, SEO, accessibility and performance regressions.
8. Verify Cloudflare deployment configuration.
9. Verify branch protection configuration.
10. Verify dependency security status.

Rules:
- Never deploy directly to production.
- Never merge directly to main.
- Never remove Germany map functionality.
- Never remove marketing assets.
- Never modify Cloudflare routes without approval.
- Never delete content without confirmation.
- Always create pull requests.
- Always provide a remediation summary.

When a workflow fails:
1. Read logs.
2. Identify root cause.
3. Create fix branch.
4. Commit fix.
5. Open PR.
6. Verify all checks.
7. Report status.

When repository health is good:
1. Audit dependencies.
2. Audit security posture.
3. Audit performance.
4. Audit SEO.
5. Audit accessibility.
6. Propose improvements as pull requests.

---
