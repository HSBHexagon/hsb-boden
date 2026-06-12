# Security Final Report
**Project:** hsb-boden
**Date:** 2026-06-12
**Status:** COMPLETE (Phase 4 follow-up / consolidation)

---

## 1. Dependency Vulnerabilities (`npm audit`, measured 2026-06-12)

Re-running `npm audit --json` against the current `package-lock.json` gives:

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 8 |
| Moderate | 7 |
| Low | 1 |
| **Total** | **16** |

> Note: `AUDIT_REPORT.md` (Phase 1, Gemini CLI) reported "11 vulnerabilities (3 High)". The figure above is a fresh `npm audit` measurement taken during this session and supersedes that estimate — the discrepancy is most likely due to a `package-lock.json` change between the two scans, not a regression introduced here.

Affected top-level/transitive packages and the fix versions npm proposes (all flagged `isSemVerMajor: true`, i.e. require a major version bump and manual regression testing — **none applied automatically**):

| Package | Severity | Proposed fix version |
|---|---|---|
| `astro` | high | 6.4.6 |
| `@astrojs/cloudflare` | high | 13.7.0 (via `astro`) |
| `@astrojs/react` / `@vitejs/plugin-react` | high | 3.6.2 |
| `vite` | high | 8.0.16 |
| `wrangler` / `undici` | high | wrangler 3.6.0 |
| `esbuild` | high | via `astro` 6.4.6 |
| `@astrojs/check`, `@astrojs/language-server`, `volar-service-yaml`, `yaml`, `yaml-language-server` | moderate | `@astrojs/check` 0.9.2 |
| `miniflare`, `ws` | moderate | via `wrangler` 3.6.0 |
| `@astrojs/tailwind` | low | 2.1.3 |

**Recommendation:** These are major-version upgrades (Astro 6, Vite 8, Wrangler 4-ish, Tailwind integration v2). Given the project's "minimal-invasive changes" rule and the active Deploy Gate (production not yet live), schedule this as a dedicated, isolated dependency-upgrade branch with full `npm run check && npm run test:run && npm run build` + Lighthouse + Playwright verification before merging — not a drive-by fix alongside other changes.

## 2. Hardcoded Secrets

- Source tree scanned: no hardcoded API keys, tokens, or credentials found (confirms `AUDIT_REPORT.md` Phase 4 finding).
- Runtime secrets (`PUBLIC_LEAD_ENDPOINT`, `PUBLIC_LEAD_ACCESS_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) are environment/Secrets-managed, not committed.

## 3. GitHub Actions Hardening (this session)

All workflow files in `.github/workflows/` now pin third-party actions to a commit SHA with a version comment, consistent with the existing `quality.yml` pattern:

- `quality.yml` — already pinned (baseline reference).
- `deploy-preview.yml` — already pinned.
- `deploy-production.yml` — rewritten: trigger changed from `push: branches: [main]` to `workflow_dispatch` only, `environment: production` added, explicit quality gate (`npm run check && npm run test:run`) before build/deploy. This enforces the AGENTS.md Deploy Gate ("Production deploys remain blocked until the lead pipeline is live and WordPress is intentionally cut over") at the CI level, not just as documentation.
- `security.yml` — pinned `actions/checkout`, `github/codeql-action/*`, `actions/dependency-review-action`, `trufflesecurity/trufflehog`; added `permissions: contents: read` to the `dependency-review` and `secret-scanning` jobs (least privilege); secret-scanning checkout now uses `fetch-depth: 0` so trufflehog can scan full history.
- `lighthouse.yml` — pinned `actions/checkout`, `actions/setup-node`; added `permissions: contents: read`.

## 4. CodeQL / Dependabot / Secret Scanning / Dependency Review

- **CodeQL**: NOT run from `security.yml` — that workflow intentionally contains only `dependency-review` and `secret-scanning` jobs. CodeQL analysis is provided by GitHub's **default code-scanning setup** (Settings → Code security → Code scanning), confirmed via the API as `state: configured` (languages: javascript, javascript-typescript, typescript; weekly schedule). This is an external/repo-level prerequisite, not something defined in this repo's workflow files. If advanced configuration (custom queries, multiple languages, etc.) is ever needed, default setup must first be disabled in repo settings before adding a custom CodeQL job to `security.yml` — running both simultaneously causes SARIF upload failures ("CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled").
- **Dependency Review**: `dependency-review-action` runs on `pull_request` events.
- **Secret Scanning (GitHub native)**: a repo-setting toggle (Settings → Code security → Secret scanning), separate from the in-workflow `trufflehog` job. Flagged for the user to confirm is enabled.
- **Dependabot**: no `.github/dependabot.yml` exists in this repo. Not created in this pass — adding automated dependency-update PRs on top of the 16 known major-version-bump vulnerabilities above would generate a wave of large PRs; recommend introducing Dependabot only after the dependency-upgrade branch in §1 has landed, to avoid PR noise pointing at the same already-known issues.

## 5. Lighthouse CI

- `.lighthouserc.json` created (was referenced by `lighthouse.yml` but missing). Thresholds: performance ≥ 0.9 (warn), accessibility ≥ 0.95 (error), best-practices ≥ 0.95 (warn), seo ≥ 0.95 (error), `staticDistDir: ./dist` (matches the flat SSR build output, verified via `ls dist/`).
- Prior measured results (per project memory, `working_set.json`): Desktop 100/100/100/100, Mobile 99/100/100/100 — both above the configured thresholds.

---

## Open Items (not actioned in this pass — require explicit follow-up)

1. Dependency major-version upgrades (§1) — dedicated branch + full verification gate.
2. Confirm in GitHub UI: Code scanning (CodeQL) and Secret Scanning are enabled for this repository.
3. Defer Dependabot config until §1 is resolved.
