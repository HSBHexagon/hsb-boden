# MULTI_PC_OPERATOR_SYNC_PROTOCOL — HSB-Boden / HEXAFLOOR

Status: `protocol-documented-single-operator-active`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

This document defines how Joel, JORDI, and any future operator keep the project in
sync when working across multiple machines or as a team.

---

## Current Operator Configuration

| Operator | Role | Machines |
|----------|------|---------|
| Joel Cherino Diaz | Primary — repo, deploy, CRM, outreach | Primary Mac (canonical dev machine) |
| JORDI Post | Secondary — outreach only via own flyer variant | Own device — no repo access required |
| Future operators | Viewer / CRM-only | TBD |

---

## Canonical Source of Truth

| Asset | Location | Who Has Write Access |
|-------|----------|---------------------|
| Website code | `git@github.com:cherinojoel-lang/hsb-boden` (`main`) | Joel only |
| CRM-Light | Google Sheets "HSB CRM Light" | Joel (owner), JORDI (editor if shared) |
| Flyer PDFs | `public/` in repo + deployed on Worker | Joel (via git + wrangler) |
| Outreach templates | `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md` | Joel (via git) |
| Cloudflare secrets | Cloudflare Dashboard / wrangler | Joel only |

---

## Joel — Multi-Machine Protocol

### If Working on a Second Mac or New Machine

```bash
# 1. Clone the canonical repo
git clone git@github.com:cherinojoel-lang/hsb-boden.git
cd hsb-boden

# 2. Verify you are on main and up to date
git fetch origin
git checkout main
git status

# 3. Install dependencies
npm ci

# 4. Verify wrangler identity
npx wrangler whoami
# Expected: cherinojoel@gmail.com

# 5. Read canonical state files before any work
# - PROJECT_TRUTH.md
# - CHECKPOINT_STATE.json
# - docs/FINAL_OPERATOR_HANDOFF.md
# - docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md
```

### Before Any Code Change

```bash
git fetch origin
git pull origin main
git status
```

Never work on stale code. Always pull before editing.

### Before Any Deploy

```bash
# Confirm you are on main, no uncommitted changes
git status
# Confirm worker identity
npx wrangler whoami
# Confirm current deployments
npx wrangler deployments list --name hsb-boden
# Deploy only with the canonical command
wrangler deploy --name hsb-boden --var ENVIRONMENT:production
```

### After Any Local Doc Change (Not Code)

Docs like `PROJECT_TRUTH.md`, `CHECKPOINT_STATE.json`, session logs:
- These changes are tracked in git but require explicit approval before commit/push
- Never push without Joel's decision: `no_push` rule in `active_state.json`

---

## JORDI — Operator Protocol (No Repo Access Required)

JORDI's operational surface is:
1. Own flyer: `HSB-Flyer-Jordi-Post.pdf` — provided by Joel via file share
2. CRM-Light: Google Sheets — if Joel shares the sheet with JORDI's email
3. Outreach from JORDI's own email account (not `j-cherino@hsb-boden.de`)

### JORDI CRM Workflow

1. JORDI logs all own contacts directly in CRM-Light (if sheet access granted)
2. JORDI sets `Verantwortlicher = JORDI` on rows owned by JORDI
3. JORDI never sets `Versandfreigabe = yes` unilaterally — joint approval required
4. JORDI reports new qualified leads to Joel for tier review

### JORDI Flyer Distribution

JORDI's flyer production URL (after DNS switch):
```
https://hsb-boden.de/HSB-Flyer-Jordi-Post.pdf
```

Linked in JORDI's outreach emails with UTM:
```
https://hsb-boden.de/HSB-Flyer-Jordi-Post.pdf?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=jordi-flyer
```

Workers.dev URL is for testing only. JORDI must not use it in any external communication.

---

## Future Operators — Onboarding Protocol

If a third operator joins:

1. Joel creates a read-only or editor share of Google Sheets CRM-Light
2. Joel provides the production flyer URLs (post-DNS-switch)
3. New operator reads this document + `docs/crm/CRM_LIGHT_OPERATOR_READINESS.md`
4. New operator does NOT get:
   - Cloudflare Dashboard access
   - Wrangler credentials
   - `LEAD_WEBHOOK_URL` or any Worker secret
   - Git repo push access (unless explicitly approved)
5. New operator logs all contacts in CRM with `Verantwortlicher = [Name]`

---

## Sync Cadence (Team Communication)

| Event | Who | Action |
|-------|-----|--------|
| New web form lead | Apps Script → CRM row | Joel reviews next morning |
| JORDI contacts a lead | JORDI | Log immediately in CRM (same day) |
| DNS switch pending | Domain registrar notification → Joel | Joel initiates cutover per `docs/PHASE_C_CUTOVER_RUNBOOK.md` |
| Lead qualifies for offer | Joel + JORDI | Joint review call before proposal |
| Deploy needed | Joel | Solo decision + wrangler deploy |

No async batch updates. CRM must be updated same day as contact attempt.

---

## GitHub Branch Protection Review

Current `main` branch configuration (verify in GitHub repository settings):

```
Repository: cherinojoel-lang/hsb-boden
Branch: main
```

Recommended settings (verify not currently set, apply after explicit approval):

| Setting | Recommended |
|---------|------------|
| Require pull request before merging | ✅ Enable |
| Require status checks to pass | ✅ Enable (CI must pass) |
| Require linear history | Optional |
| Allow force pushes | ❌ Disable |
| Allow deletions | ❌ Disable |

If branch protection is not yet enabled, Joel must enable it in GitHub Settings → Branches
before any external contributor is added.

---

## Deployment Coordination

Only Joel deploys to production. The deploy sequence is:

```bash
# 1. On canonical dev machine only
git status  # must be clean
git pull origin main
npm run check  # type check must pass
npm run build  # build must succeed
npx wrangler deployments list --name hsb-boden  # verify current state
wrangler deploy --name hsb-boden --var ENVIRONMENT:production
```

JORDI and future operators never run wrangler deploy.
If JORDI identifies a website bug, report to Joel → Joel fixes via PR → Joel deploys.

---

## Emergency Rollback (Joel Only)

If a bad deploy reaches production:

```bash
# List recent deployments
npx wrangler deployments list --name hsb-boden

# Roll back to previous version (replace VERSION_ID with actual ID)
npx wrangler rollback VERSION_ID --name hsb-boden
```

Full rollback plan: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` → Rollback Plan section.

---

## Stop Conditions

- No deploy from any machine other than Joel's canonical dev machine without explicit approval
- No CRM write access granted to JORDI without explicit share decision from Joel
- No GitHub collaborator added without explicit approval
- No Cloudflare sub-account or API token shared with third parties
