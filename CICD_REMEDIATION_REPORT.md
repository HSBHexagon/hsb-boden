# CI/CD Remediation Report
**Project:** hsb-boden
**Date:** 2026-06-12
**Scope:** Fix failing GitHub Actions on PR #23, resolve CodeQL conflict, verify Cloudflare/Lighthouse workflows and branch protection. No Cloudflare config, Germany map, or marketing assets changed. No auto-merge, no auto-deploy.

---

## 1. Status before this pass

All 4 checks on PR #23 were red:

| Check | Result | Cause |
|---|---|---|
| Quality | ❌ failure | invalid `actions/setup-node` SHA |
| Security | ❌ failure | invalid `trufflehog` SHA + CodeQL default-setup conflict |
| Deploy Preview | ❌ failure | invalid `actions/setup-node` SHA + wrong `--env preview` |
| Lighthouse Audit | ❌ failure | invalid `actions/setup-node` SHA + invalid `serverBaseUrl` |

## 2. Fixes applied (commit `de211c1`, same branch/PR #23)

1. **Invalid action pins** — `actions/setup-node@3932cf9a3b834d39a4730375a3f19e88f1a3b502` and `trufflesecurity/trufflehog@903f0808...` were SHAs that do not exist on those repos (introduced in the previous commit). Replaced with the real commit SHAs for the intended tags:
   - `actions/setup-node` → `39370e3970a6d050c480ffad4ff0ed4d3fdee5af` (v4.1.0) — fixed in `quality.yml`, `lighthouse.yml`, `deploy-preview.yml`, `deploy-production.yml`.
   - `trufflesecurity/trufflehog` → `1aa1871f9ae24a8c8a3a48a9345514acf42beb39` (v3.82.13) — fixed in `security.yml`.
   - `treosh/lighthouse-ci-action` pinned to `512cc908a55bfb0ad231facca52adf3d3a651df4` (v12) for consistency.

2. **CodeQL configuration conflict** — `security.yml`'s custom `analyze` job (CodeQL init/autobuild/analyze) failed with: *"CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled"*. Verified via API that this repo has GitHub's **default code-scanning setup** active (`code-scanning/default-setup` → `state: configured`, languages `javascript/javascript-typescript/typescript`, weekly schedule). Removed the redundant custom CodeQL job from `security.yml` (with an explanatory comment); `dependency-review` and `secret-scanning` jobs remain and are unaffected. CodeQL coverage continues via the default setup — no scanning capability was lost.

3. **Lighthouse workflow** — `lighthouse.yml` passed `serverBaseUrl: ./dist` (a filesystem path, not a URL) together with `urls: http://localhost:4321/`, while `.lighthouserc.json` already declares `staticDistDir: ./dist`. These are conflicting/redundant configurations. Removed `urls`/`serverBaseUrl`; `.lighthouserc.json`'s `staticDistDir` is sufficient — `treosh/lighthouse-ci-action` starts its own static server and audits the built output directly.

4. **Deploy Preview workflow** — used `wrangler deploy --env preview`, but `wrangler.toml` has no `[env.preview]` block. The top-level config (`name = "hsb-boden-preview"`) **is** the preview environment, matching `package.json`'s `deploy:preview` script (`wrangler deploy --env=""`). Changed to plain `wrangler deploy`. (No values inside `wrangler.toml` were changed.)

## 3. Result after fixes

| Check | Result |
|---|---|
| Quality | ✅ success |
| Security | ✅ success |
| Lighthouse Audit | ✅ success |
| Deploy Preview | ✅ success |
| CodeQL (default setup) | ✅ success |
| Dependency Review | ✅ success |
| Secret Scanning | ✅ success |
| Workers Builds: hsb-boden-preview | ✅ success |

**All 8 checks on PR #23 are green.** PR #23 is ready for the user's manual merge decision.

## 4. Deploy Preview — resolved

The user added `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as GitHub Actions repository secrets (Settings → Secrets and variables → Actions). The Deploy Preview job (run `27442186992`) was re-run and completed successfully (`conclusion: success`).

Previously, after the `--env preview` → `deploy` fix, Wrangler ran but failed with:

```
✘ [ERROR] In a non-interactive environment, it's necessary to set a
CLOUDFLARE_API_TOKEN environment variable for wrangler to work.
```

This is now resolved — no further action needed here.

Separately noted (not fixed, config unchanged per instructions): Wrangler 3.90 logs a warning that `preview_urls` is an "unexpected field" at the top level of `wrangler.toml`. This is a non-fatal warning under the current Wrangler version and `wrangler.toml` was left untouched as instructed; revisit if/when Wrangler is upgraded (see `SECURITY_FINAL_REPORT.md` §1 dependency-upgrade follow-up).

## 5. Branch Protection (verified, not changed)

```
GET /repos/cherinojoel-lang/hsb-boden/branches/main/protection → 404 "Branch not protected"
```

**`main` currently has no branch protection rules at all** — no required status checks, no required reviews, no restriction on force-push/deletion.

**Not changed in this pass** — enabling branch protection is a repository-governance change with immediate effect on how the user merges their own work, so it was not applied without explicit confirmation. Recommended configuration once Deploy Preview is green (§4):

- Require status checks to pass before merging: `Quality`, `Security`, `Lighthouse Audit`, `Deploy Preview`
- Require branches to be up to date before merging
- (Optional, matches the "Joel keeps the merge button" decision from the user's own message) Require pull request review before merging — can be skipped if the user is the sole merger and wants to self-approve via admin override.

## 6. Security & Analysis Settings (verified via API — already correct, no action needed)

```json
{
  "dependabot_security_updates": "enabled",
  "secret_scanning": "enabled",
  "secret_scanning_push_protection": "enabled",
  "code_scanning_default_setup": "configured (javascript/javascript-typescript/typescript, weekly)"
}
```

Dependabot Alerts, Dependabot Security Updates, Secret Scanning (+ push protection), and Code Scanning (default CodeQL setup) are **all already enabled** for this repository. Nothing to change here.

## 7. Repository structure

No structural changes in this pass beyond the workflow-file edits described above (`.github/workflows/{quality,security,lighthouse,deploy-preview,deploy-production}.yml`). Cloudflare configuration (`wrangler.toml`), Germany map (`src/data/germanyMap.ts`, `src/components/references/ReferenceMap*.astro`), and `marketing/` assets were not touched.

---

## Summary / Next Steps

1. ✅ Done: User added `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` as GitHub Actions secrets; Deploy Preview re-run succeeded.
2. **All 8 checks on PR #23 are green.** PR #23 is ready for the user's manual merge (per the "Joel keeps the merge button" policy — no auto-merge was performed or configured). Merge decision and execution remain with the user.
3. Optional follow-up (separate, explicitly-approved step): add branch protection on `main` per §5.
4. Existing follow-ups from `SECURITY_FINAL_REPORT.md` (dependency major-version upgrades) and `PROJECT_STRUCTURE.md` (duplicate status docs) remain open and out of scope for this CI fix pass.
