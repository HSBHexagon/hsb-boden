# HSB Hexagon Monorepo Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the Astro/Cloudflare website (`hsb-boden`) and the Sales OS CRM (`hsb-sales-os`) into a single canonical Monorepo under `HSBHexagon/hsb-boden` with 100% git commit history preservation via `git subtree`, while formalizing the deprecation of `auto-hub1`.

**Architecture:** A Pure Directory Isolation Monorepo where `apps/website/` encapsulates the frontend and `apps/sales-os/` encapsulates the CRM engine. A root orchestration `Makefile` coordinates cross-cutting commands without coupling Node and Python runtimes.

**Tech Stack:** Astro 5, React, Tailwind CSS, TypeScript, Cloudflare Pages, Python 3.14, Google Apps Script (`clasp`), Pytest, Git Subtree.

## Global Constraints

- `DATA_LOSS_PROHIBITED = YES`: Every git commit, tag, and file history from both repositories must be preserved.
- `ZERO_DOWNTIME = YES`: Cloudflare Pages builds and Google Clasp deployments must remain operational.
- `SAFETY_INVARIANT = REAL_EXTERNAL_SEND_COUNT = 0`: Zero external email sending during all operations.
- `HSB_BUNDLING_RULE = YES`: Root directory `HSBHexagon/hsb-boden` represents the unified corporate entity.

---

### Task 1: Baseline Tagging & Safety Recovery Protocol

**Files:**
- Create: `apps/sales-os/.git-baseline-tag`
- Test: Git tag verification in both repositories

**Interfaces:**
- Consumes: Existing git commits from `hsb-boden` and `hsb-sales-os`
- Produces: Immutable git tags `backup-pre-monorepo-2026-09-16`

- [ ] **Step 1: Create safety tag in `hsb-sales-os`**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
git tag -a backup-pre-monorepo-2026-09-16 -m "Safety baseline before monorepo consolidation"
```

- [ ] **Step 2: Create safety tag in `hsb-boden`**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git tag -a backup-pre-monorepo-2026-09-16 -m "Safety baseline before monorepo consolidation"
```

- [ ] **Step 3: Verify tags exist in both repos**

```bash
git -C /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os tag -l "backup-pre-monorepo-*"
git -C /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden tag -l "backup-pre-monorepo-*"
```
Expected: Output shows `backup-pre-monorepo-2026-09-16` in both.

- [ ] **Step 4: Commit verification marker**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
git status
```

---

### Task 2: Auto-Hub Repository Deprecation & Archival

**Files:**
- Modify: Remote repository `cherinojoel-lang/auto-hub1` via GitHub CLI

**Interfaces:**
- Consumes: GitHub authentication via `gh` CLI
- Produces: Archived status for `cherinojoel-lang/auto-hub1`

- [ ] **Step 1: Check current state of `auto-hub1`**

```bash
gh repo view cherinojoel-lang/auto-hub1 --json isArchived,description
```
Expected: `{"isArchived": false}`

- [ ] **Step 2: Archive `auto-hub1` on GitHub**

```bash
gh repo archive cherinojoel-lang/auto-hub1 --yes
```

- [ ] **Step 3: Verify archived state**

```bash
gh repo view cherinojoel-lang/auto-hub1 --json isArchived
```
Expected: `{"isArchived": true}`

---

### Task 3: Website Namespacing in `hsb-boden` (`apps/website`)

**Files:**
- Create: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/website`
- Modify: Move frontend files to `apps/website/`
- Test: `cd apps/website && npm run build`

**Interfaces:**
- Consumes: Existing files in `hsb-boden` root
- Produces: `apps/website/package.json`, `apps/website/src`, `apps/website/dist`

- [ ] **Step 1: Create integration branch in `hsb-boden`**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git checkout -b feat/monorepo-consolidation
```

- [ ] **Step 2: Clean uncommitted cache changes and namespace files**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git checkout -- .astro/
mkdir -p apps/website
git mv src public functions astro.config.mjs package.json tsconfig.json apps/website/
```

- [ ] **Step 3: Test Astro build inside `apps/website`**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/website
npm run build
```
Expected: Exit code 0, `dist/` created.

- [ ] **Step 4: Commit namespaced website structure**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git add apps/website
git commit -m "refactor(monorepo): Namespace Astro website under apps/website"
```

---

### Task 4: Zero-Data-Loss Subtree Import of Sales OS

**Files:**
- Create: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/sales-os`
- Test: `git log --oneline -- apps/sales-os`

**Interfaces:**
- Consumes: Local repository `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os` (branch `fix/anhang-signatur-trigger-2026-09-07`)
- Produces: `apps/sales-os/` with full git history

- [ ] **Step 1: Add local remote for Sales OS**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git remote add local-sales-os /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
git fetch local-sales-os
```

- [ ] **Step 2: Execute git subtree merge**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git subtree add --prefix=apps/sales-os local-sales-os fix/anhang-signatur-trigger-2026-09-07 -m "chore(monorepo): Merge hsb-sales-os via git subtree preserving 100% commit history"
git remote remove local-sales-os
```

- [ ] **Step 3: Verify commit history preservation**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git log -n 10 --oneline -- apps/sales-os
```
Expected: Displays commits from Sales OS (e.g., `353e3b5`, `36ce571`, `a093d8d`, `cc5004b`, `b64d044`).

---

### Task 5: Toolchain Hardening & Root Makefile

**Files:**
- Create: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/Makefile`
- Modify: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/sales-os/.clasp.json`
- Test: `make test-crm`, `make build-web`

**Interfaces:**
- Consumes: Clasp script ID, Pytest suite
- Produces: Root automation targets

- [ ] **Step 1: Create Root Makefile**

```makefile
# /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/Makefile
.PHONY: help build-web test-web test-crm deploy-crm

help:
	@echo "HSB Hexagon Monorepo Commands:"
	@echo "  make build-web    - Builds Astro website for Cloudflare Pages"
	@echo "  make test-crm     - Runs full Pytest suite for Sales OS CRM"
	@echo "  make deploy-crm   - Deploys Apps Script code to Google Sheet"

build-web:
	cd apps/website && npm run build

test-crm:
	cd apps/sales-os && PYTHONPATH=. pytest tests/ -v

deploy-crm:
	cd apps/sales-os && ./deploy.sh
```

- [ ] **Step 2: Test Makefile targets**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
make build-web
make test-crm
```
Expected: Both targets succeed with exit code 0.

- [ ] **Step 3: Commit Makefile and toolchain configs**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git add Makefile apps/sales-os/.clasp.json
git commit -m "feat(monorepo): Add root orchestration Makefile and verify toolchain paths"
```

---

### Task 6: Google Drive Ecosystem Manifest Update

**Files:**
- Modify: `apps/sales-os/engine/drive_ecosystem_config.py`
- Execute: `python3 apps/sales-os/engine/drive_ecosystem_scaffold.py --execute`
- Test: `python3 -u -c "import engine.drive_ecosystem_scaffold as s; print(s.verify_all_projects_live())"`

**Interfaces:**
- Consumes: Google Drive API credentials
- Produces: Updated `00_PROJECT_MANIFEST.md` in Drive linking the unified monorepo

- [ ] **Step 1: Update `PROJECT_DEFINITIONS` in config**

Set `github_repos` for `HSB-Boden` to `["https://github.com/HSBHexagon/hsb-boden"]` and local path to `["/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden"]`.

- [ ] **Step 2: Run live Drive scaffold update**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/sales-os
PYTHONPATH=. python3 -u engine/drive_ecosystem_scaffold.py --execute
```
Expected: `00_PROJECT_MANIFEST.md` updated with `status: updated`.

- [ ] **Step 3: Verify all projects live on Drive**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/apps/sales-os
PYTHONPATH=. python3 -u -c "import engine.drive_ecosystem_scaffold as s; print(s.verify_all_projects_live()['all_passed'])"
```
Expected: `True`.

- [ ] **Step 4: Commit final monorepo state**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git add -A
git commit -m "chore(ecosystem): Reconcile consolidated Monorepo with Google Drive manifest"
```
