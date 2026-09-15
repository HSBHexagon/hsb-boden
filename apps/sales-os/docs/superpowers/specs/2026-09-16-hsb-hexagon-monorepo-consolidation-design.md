# HSB Hexagon Monorepo Consolidation Design Specification

- **Status:** Proposed & Validated Design
- **Date:** 2026-09-16
- **Authors:** Team Director (`oma-director`), HSB Hexagon Architectural Lane
- **Target Repository:** `https://github.com/HSBHexagon/hsb-boden`
- **Scope:** Consolidation of Website (`hsb-boden`) and CRM Sales OS (`hsb-sales-os`) into a unified, zero-data-loss Monorepo, plus archiving of deprecated `auto-hub1`.

---

## 1. Executive Summary & Goals

The objective is to consolidate two historically separated repositories—the Cloudflare Pages Astro website ([`HSBHexagon/hsb-boden`](https://github.com/HSBHexagon/hsb-boden)) and the Python/Apps Script Sales OS CRM ([`HSBHexagon/hsb-sales-os`](https://github.com/HSBHexagon/hsb-sales-os))—into a single, canonical enterprise Monorepo under `HSBHexagon/hsb-boden`.

### Key Business & Technical Goals
1. **Single Source of Truth:** 1 Company = 1 Google Drive Root (`HSB-Boden`) = 1 GitHub Monorepo (`hsb-boden`).
2. **Zero Data Loss (`DATA_LOSS_PROHIBITED = YES`):** Every single git commit, author attribution, and branch history from both repositories is preserved via `git subtree`.
3. **Zero Breakage / Operational Parity:**
   - Cloudflare Pages builds continue running autonomously from `apps/website/`.
   - Google Apps Script Clasp pushes continue running autonomously from `apps/sales-os/`.
   - Python CRM pipelines (2,000 drafts rollout, batch engine, Gate 1–9 tests) execute without dependency conflicts.
4. **Auto-Hub Cleanup:** Formally archive `cherinojoel-lang/auto-hub1` on GitHub, confirming `cherinojoel-lang/auto-hub` as the sole canonical repository.

---

## 2. Directory Architecture & Monorepo Layout

The unified repository uses a **Pure Directory Isolation** architecture with an orchestration Makefile at the root.

```text
HSBHexagon/hsb-boden/ (Monorepo Root)
├── .github/
│   └── workflows/              # GitHub Actions CI/CD (lint, test, security audit)
├── .omg/                       # Oh-My-Antigravity team state & session telemetry
├── apps/
│   ├── website/                # [App 1] Astro Frontend (ehemals hsb-boden)
│   │   ├── src/                # Astro & React Components, Pages, Layouts
│   │   ├── public/             # Static Assets, Favicons, Robos.txt
│   │   ├── functions/          # Cloudflare Pages Functions
│   │   ├── astro.config.mjs    # Astro Configuration
│   │   ├── package.json        # Node Dependencies (Astro, Tailwind, React)
│   │   └── tsconfig.json       # TypeScript Configuration
│   │
│   └── sales-os/               # [App 2] Sales OS CRM (ehemals hsb-sales-os)
│       ├── apps_script/        # Google Apps Script Source (HSB_SALES_OS.gs, Actions.gs)
│       ├── .clasp.json         # Clasp Script Binding (rootDir: ./apps_script)
│       ├── engine/             # Python Engine (batch_engine.py, sync, drive scaffold)
│       ├── batches/            # Rollout Batches & JSON Matrices
│       ├── tests/              # Pytest Test Suite (45+ Unit/Integration Tests)
│       ├── deploy.sh           # Atomic Clasp Push Script
│       └── requirements.txt    # Python Dependencies (google-api, pandas, pytest)
│
├── shared/                     # Shared Company Assets
│   ├── brand/                  # Vector Logos, Color Schemes, Typography
│   └── docs/                   # Cross-functional Blueprints & Architecture Docs
│
├── 00_PROJECT_MANIFEST.md      # Canonical Project Manifest (Linked to Drive)
├── Makefile                    # Root Orchestration Interface
└── README.md                   # Unified Project Documentation & Onboarding
```

---

## 3. Toolchain & CI/CD Isolation (Break-Nothing Guarantee)

### 3.1 Cloudflare Pages Integration
- **Cloudflare Project:** `hsb-boden`
- **Root Directory Setting:** `apps/website`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Build Triggers:** Cloudflare Pages only triggers a build when files within `apps/website/` or `shared/` are modified. Changes to `apps/sales-os/` do not consume build minutes.

### 3.2 Google Apps Script & Clasp Integration
- **Clasp Configuration:** Stored in `apps/sales-os/.clasp.json`.
- **Root Directory Setting:**
  ```json
  {
    "scriptId": "1w3c7z3Kj1yXQp_0_6v_...",
    "rootDir": "./apps_script"
  }
  ```
- **Deployment Command:** Executed from `apps/sales-os/` via `./deploy.sh` or from repo root via `make deploy-crm`.

### 3.3 Root Orchestration Makefile
```makefile
.PHONY: help install-web install-crm build-web test-web test-crm deploy-crm

help:
	@echo "HSB Hexagon Monorepo Commands:"
	@echo "  make build-web    - Builds Astro website for Cloudflare Pages"
	@echo "  make test-crm     - Runs full Pytest suite for Sales OS CRM"
	@echo "  make deploy-crm   - Deploys Apps Script code to Google Sheet"

build-web:
	cd apps/website && npm run build

test-web:
	cd apps/website && npm test

test-crm:
	cd apps/sales-os && pytest tests/ -v

deploy-crm:
	cd apps/sales-os && ./deploy.sh
```

---

## 4. Zero-Data-Loss Migration Protocol (`git subtree`)

To guarantee `DATA_LOSS_PROHIBITED = YES`, the migration follows an immutable 4-step git process:

### Step 1: Safety Baseline Tags
Create immutable tags in both repositories prior to any modifications:
```bash
git -C /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden tag backup-pre-monorepo-2026-09-16
git -C /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os tag backup-pre-monorepo-2026-09-16
```

### Step 2: Structure Web Repo via `git mv`
In `hsb-boden`, create a branch `feat/monorepo-consolidation`. Move all website files into `apps/website/` using `git mv` so that file history and `git blame` are 100% preserved:
```bash
mkdir -p apps/website
git mv src public functions astro.config.mjs package.json tsconfig.json apps/website/
git commit -m "refactor(monorepo): Namespace website files into apps/website"
```

### Step 3: Subtree Import of Sales OS
Add the local `hsb-sales-os` as a temporary remote and merge its entire commit history under the `apps/sales-os` prefix:
```bash
git remote add local-sales-os /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os
git fetch local-sales-os
git subtree add --prefix=apps/sales-os local-sales-os fix/anhang-signatur-trigger-2026-09-07 -m "chore(monorepo): Merge hsb-sales-os via git subtree preserving 100% commit history"
git remote remove local-sales-os
```

### Step 4: Python & Clasp Path Hardening
Update relative import paths in `apps/sales-os/engine/` so that `REPO_ROOT` dynamically resolves whether called from `apps/sales-os/` or from the monorepo root.

---

## 5. Auto-Hub Repository Clarification

- **Canonical Repository:** `https://github.com/cherinojoel-lang/auto-hub` (680+ commits, active production codebase).
- **Deprecated Repository:** `https://github.com/cherinojoel-lang/auto-hub1` (1 commit, empty documentation placeholder).
- **Action:** Archive `cherinojoel-lang/auto-hub1` via GitHub CLI:
  ```bash
  gh repo archive cherinojoel-lang/auto-hub1 --yes
  ```

---

## 6. Verification & Quality Gates

| Gate | Description | Command | Success Criteria |
| :--- | :--- | :--- | :--- |
| **Gate 1** | Git History Audit | `git log --oneline -- apps/sales-os` | Shows complete commit history from Sales OS |
| **Gate 2** | Astro Build | `cd apps/website && npm run build` | Exit Code 0, `dist/` successfully generated |
| **Gate 3** | CRM Pytest Suite | `cd apps/sales-os && pytest tests/ -v` | 45/45 Tests PASS |
| **Gate 4** | Clasp Integrity | `cd apps/sales-os && npx clasp status` | 7 Files tracked, matches Apps Script container |
| **Gate 5** | Google Drive Sync | `python3 apps/sales-os/engine/drive_ecosystem_scaffold.py --execute` | `00_PROJECT_MANIFEST.md` updated and live verified |

---

## 7. Rollback Strategy

If any gate fails or unexpected regressions occur:
1. Revert to `backup-pre-monorepo-2026-09-16` tag via `git reset --hard backup-pre-monorepo-2026-09-16`.
2. Both repositories remain completely intact in their original local directories `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden` and `.../hsb-sales-os`.
3. 0% data loss risk.
