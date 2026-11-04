# Phase 9: Repository Structure Audit
**Project:** hsb-boden
**Date:** 2026-06-12
**Status:** AUDIT ONLY — no files moved or deleted (per SCMS guardrail "Keine Ordner verschieben ohne Diff/Backup")

---

## 1. Application Code (`src/`) — healthy

```
src/components/{consent,forms,layout,localization,references,sections,seo}/
src/data/        — content model (services, industries, references, articles, navigation, i18n, manufacturers, client locations)
src/layouts/     — BaseLayout.astro
src/lib/         — content, i18n, schema (JSON-LD), seo, tracking, validation
src/pages/       — routes incl. /branchen, /leistungen, /wissen, locale homepages (en/fr/nl/pl/tr), robots.txt, sitemap.xml
src/styles/      — global.css
tests/           — content, experience, form, schema tests (vitest)
```

This matches `AGENTS.md` → Content Model ("Structured content lives under `src/data`"). No issues found.

## 2. Operational / Config

- `astro.config.mjs`, `wrangler.toml`, `tailwind.config.mjs`, `tsconfig.json`, `vitest.config.ts`, `package.json` — standard, at root, correctly placed.
- `.github/workflows/` — CI (quality, security, lighthouse, deploy-preview, deploy-production), all pinned this session.
- `.github/copilot-instructions.md` — added this session.
- `scripts/` — `optimize-images.mjs`, `skill-preflight.sh`, `worktree-bootstrap.sh`. Reasonable.
- `ops/n8n/` — lead-pipeline workflow + runbooks. Reasonable, matches `CONVERSION_REPORT.md` findings.
- `marketing/flyer/` — self-contained flyer build (own `package.json`/`package-lock.json`, assets, render script). Isolated from the main app; fine as-is.
- `docs/` — audit reports, competitor benchmarks, content briefs, launch checklists, superpowers plans, and `docs/review-archive/`.

## 3. Finding: Duplicated status/report Markdown files at repo root

The following files exist **both** at the repo root **and** as (often identically-named) entries under `docs/review-archive/`:

| Root file | Also in `docs/review-archive/` |
|---|---|
| `CURRENT_EXECUTION_STATE.md` | ✅ |
| `FINAL_HANDOFF.md` | ✅ |
| `FINAL_WEBSITE_ACCEPTANCE.md` | ✅ |
| `FINAL_WEBSITE_COMPLETION_TASKS.md` | ✅ |
| `LANGUAGE_STRATEGY_REVIEW.md` | ✅ |
| `MERGE_COMPLETION_REPORT.md` | ✅ |
| `NEXT_CRITICAL_PATH.md` | ✅ |
| `P0_EXECUTION_REPORT.md` | ✅ |
| `PROJECT_REALITY_CHECK.md` | ✅ |
| `RECOVERY_EXECUTION_PLAN.md` | ✅ |
| `VISUAL_RELEASE_VERIFICATION.md` | ✅ |
| `WEBSITE_FINALIZATION_AUDIT.md` | ✅ |
| `WEBSITE_FINALIZATION_TASKS.md` | ✅ |
| `WEBSITE_FINAL_IMPLEMENTATION_REPORT.md` | ✅ |
| `AGENTS.md` | ✅ (root is current; archive copy is a historical snapshot) |
| `README.md` | ✅ |

This looks like a prior session already started consolidating point-in-time status reports into `docs/review-archive/` but left the originals at root, creating a "which one is current" ambiguity for any agent.

**This audit does not resolve the duplication** — per the SCMS core rule ("bei Unsicherheit: Stop → Fragen → Planen → Ausführen") and "Keine Ordner verschieben ohne Diff/Backup", whether the root copies or the archive copies are the canonical/current version was not established within this session's approved scope (CI workflows, AGENTS.md, copilot-instructions, and the new audit reports only).

**Recommendation for a future, explicitly-approved pass:**
1. Diff each root/archive pair to confirm which is newer/authoritative.
2. Move superseded root-level status docs into `docs/review-archive/` (or delete if truly duplicate), keeping only currently-relevant docs (`AGENTS.md`, `README.md`, and the new Phase-7/8/9/Security reports from this session) at the root.
3. Do this as its own PR, separate from CI/security changes, so it's easy to review and revert.

## 4. New files added in this session

- `.github/copilot-instructions.md`
- `.lighthouserc.json`
- `AUDIT_REPORT.md`, `SEO_REPORT.md`, `ACCESSIBILITY_REPORT.md` (pre-existing untracked from the prior Gemini session, now part of this commit)
- `SECURITY_FINAL_REPORT.md`, `PERFORMANCE_REPORT.md`, `CONVERSION_REPORT.md`, `PROJECT_STRUCTURE.md` (this report)
- Modified: `AGENTS.md` (appended Multi-Agent Guardrails section), `.github/workflows/{deploy-production,security,lighthouse}.yml`

All of the above are placed at repo root or `.github/`, consistent with existing conventions — no new top-level directories introduced.
