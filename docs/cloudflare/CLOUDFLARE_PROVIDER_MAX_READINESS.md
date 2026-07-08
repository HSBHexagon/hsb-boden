# CLOUDFLARE_PROVIDER_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `cloudflare-account-zone-worker-ready-awaiting-ns-switch`
Stand: 2026-06-26 | Canonical since this sweep.

This is the **single canonical Cloudflare provider-readiness document**.
`docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md` is now a historical/final-audit wrapper
pointing here. Do not maintain two active Cloudflare canonical docs.

Execution runbook for the actual cutover: `docs/PHASE_C_CUTOVER_RUNBOOK.md`.
That file remains the canonical trigger-day execution path. This file is readiness truth.

---

## Verified Provider State

| Field | Value |
|-------|-------|
| Cloudflare account | `cherinojoel@gmail.com` |
| Account ID | `043ec899a435f150995d89f402ed7b12` |
| Zone domain | `hsb-boden.de` |
| Zone ID | `2aefa04f69a2339b2f9f3f2876d7e35c` |
| Zone status | `pending` — NS not yet switched to Cloudflare |
| Wrangler version | `4.103.0` (verified 2026-06-24) |
| Wrangler login | Confirmed `cherinojoel@gmail.com` via `wrangler whoami` |

Zone becomes `active` only after the domain registrar switches NS records to Cloudflare.
Until then no routes can be created and no custom-domain traffic reaches any worker.

---

## Worker Inventory

### Production Worker: `hsb-boden`

| Parameter | Value |
|-----------|-------|
| Worker name | `hsb-boden` |
| Deployment URL | `https://hsb-boden.cherinojoel.workers.dev` |
| Routes | **none** — intentionally route-less until NS switch |
| ENVIRONMENT var | `production` (set via `--var ENVIRONMENT:production`, not `--env production`) |
| Secret `LEAD_WEBHOOK_URL` | Set; value never printed or committed |
| Session KV | `hsb-boden-session` (`dc91654846b546e39c273d85f559a5a2`) |
| Deploy command | `wrangler deploy --name hsb-boden --var ENVIRONMENT:production` |
| Last verified deploy | 2026-06-24 — route-less, end-to-end CRM write confirmed |

### Preview Worker: `hsb-boden-preview`

| Parameter | Value |
|-----------|-------|
| Worker name | `hsb-boden-preview` |
| workers_dev | `true` |
| ENVIRONMENT var | `preview` |

### Critical Adapter Bug — `--env production` is BROKEN

`wrangler deploy --env production` silently deploys to `hsb-boden-preview`, not production.

Cause: The Astro 6 Cloudflare adapter generates `.wrangler/deploy/config.json` from the
top-level `wrangler.toml` only. The `[env.production]` section is silently ignored.

**Never use `npm run deploy:production` or `--env production` for cutover.**
Use exclusively: `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
Documented with dry-run proof in `docs/PHASE_C_CUTOVER_RUNBOOK.md`.

---

## Zone and Route Prerequisites

Planned route patterns (not yet created — blocked until NS switch + approval):

```
hsb-boden.de/*          → Worker hsb-boden
www.hsb-boden.de/*      → Worker hsb-boden
```

Origin allowlist hard-coded in `src/pages/api/lead.ts:7–9`:
- `https://hsb-boden.de`
- `https://www.hsb-boden.de`

Route creation requires:
1. Zone status = `active` (NS switch completed)
2. Proxied A or CNAME records for `hsb-boden.de` and `www.hsb-boden.de`
3. Explicit operator approval documented before proceeding

---

## DNS/NS Trigger Conditions

The following must ALL be true before any route, DNS, or deploy action:

- [ ] Domain registrar (Kasserver) NS records point to Cloudflare nameservers
- [ ] Zone `hsb-boden.de` shows status `active` in Cloudflare dashboard
- [ ] Operator has explicitly approved the cutover in writing
- [ ] Production worker `hsb-boden` is confirmed route-less (no accidental route)
- [ ] Secret `LEAD_WEBHOOK_URL` verified to exist (do not print value)
- [ ] `docs/PHASE_C_CUTOVER_RUNBOOK.md` read and understood

---

## Cutover Readiness Checklist (Go / No-Go)

This checklist matches `docs/PHASE_C_CUTOVER_RUNBOOK.md`. Do not introduce alternate cutover logic here.

### Go conditions (all must be true)

- [ ] Zone `hsb-boden.de` = `active`
- [ ] DNS records for apex and www proxied through Cloudflare
- [ ] Mail DNS records (MX, SPF, DMARC, DKIM, autodiscover) in Cloudflare as DNS-only before switch
- [ ] Production worker confirmed route-less via `wrangler deployments list --name hsb-boden`
- [ ] Secret existence confirmed: `wrangler secret list --name hsb-boden` shows `LEAD_WEBHOOK_URL`
- [ ] Apps Script webhook alive: `curl -s "<LEAD_WEBHOOK_URL>"` → `{"ok":true,...}`
- [ ] Build passes: `npm run build`
- [ ] Tests pass: `npm run test:run`
- [ ] Type check passes: `npm run check`
- [ ] Explicit cutover approval obtained from Joel

### No-Go conditions (stop if any is true)

- Zone still `pending`
- No explicit approval documented
- Secret missing or value unknown
- Worker already has routes (unexpected state — investigate before proceeding)
- Build, test, or check failures

---

## Hidden Risks and Non-Trigger-Safe States

| Risk | Status | Action required |
|------|--------|----------------|
| `--env production` bug | Documented | Always use `--name hsb-boden --var ENVIRONMENT:production` |
| CI `actions/checkout@v4` unpinned | **Fixed** — commit `a28fbb2` SHA-pinned | None |
| CI `actions/setup-node@v4` unpinned | **Fixed** — commit `a28fbb2` SHA-pinned | None |
| `deploy-production.yml` used `--env production` | **Fixed** — commit `a28fbb2` | None |
| Mail DNS records not in Cloudflare yet | Pending (pre-switch) | Add before NS switch — see `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md` |
| DKIM selectors missing | Pending | Activate in M365 Admin Center before outreach |
| Stash `stash@{0}` | Preserved | Do not pop without explicit approval |
| Route-less worker serving workers.dev | Expected state | Not a risk until NS switch |

---

## Rollback Plan

### Rollback Triggers

Initiate rollback if any of the following occur after route activation:

- Live domain (`hsb-boden.de`) returns errors (5xx, connection refused, wrong content)
- CRM lead intake (`/api/lead`) stops writing to Google Sheet
- WordPress live site becomes unreachable and rollback is requested
- Unexpected secret loss or LEAD_WEBHOOK_URL misconfiguration detected
- Explicit operator decision to revert

### Route Removal Path

To remove routes and revert to WordPress fallback:

```bash
# List current routes to confirm
npx wrangler routes list --zone hsb-boden.de

# Delete each route by ID (get IDs from the list above)
npx wrangler routes delete <ROUTE_ID> --zone hsb-boden.de
```

After route removal: all traffic to `hsb-boden.de` falls back to the DNS A record
pointing to the Kasserver WordPress origin (`85.13.130.17`), provided the Cloudflare
proxy remains active and no A record was changed.

### Expected WordPress Fallback Behavior After Route Removal

- Cloudflare zone remains active; DNS A record still resolves to `85.13.130.17`
- Requests to `hsb-boden.de` reach the Kasserver WordPress origin
- WordPress serves content as before the cutover
- The Astro/Worker site is not reachable on the custom domain until routes are re-added
- `https://hsb-boden.cherinojoel.workers.dev` continues to serve the worker directly

### Post-Rollback Verification Steps

1. `curl -I https://hsb-boden.de` — confirm response comes from WordPress (check `Server:` header or content)
2. `npx wrangler routes list --zone hsb-boden.de` — confirm no routes remain
3. WordPress admin accessible at the usual admin path
4. Note: DNS propagation may take up to 5 minutes; wait before declaring rollback complete

### Boundary — What Rollback Does NOT Touch

Route removal is the only rollback action. The following are **not changed** by rollback:

- Mail DNS records (MX, SPF, DMARC, DKIM, autodiscover) — remain untouched
- Secret `LEAD_WEBHOOK_URL` — remains set on the worker
- Worker code, KV namespaces, session data — unchanged
- Cloudflare zone — remains active; only routes are removed
- GitHub Actions workflows — unchanged
- Any secrets, credentials, or environment variables not listed above

If mail DNS, secrets, or other settings require changes, those require separate explicit approval.

---

## Reference Links

- Execution runbook: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
- Email/mail DNS records: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`
- Operator handoff: `docs/handoff/JOEL_JORDI_OPERATOR_RUNBOOK.md`
- Historical Cloudflare audit (final evidence): `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md`
- Pre-go-live UI inventory: `docs/cloudflare/GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`
- WAF/cache/rate-limit readiness: `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`
- R2 asset strategy: `docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`
- Turnstile form protection: `docs/cloudflare/TURNSTILE_FORM_PROTECTION_READINESS.md`
- AI Gateway (future only): `docs/cloudflare/AI_GATEWAY_FUTURE_ARCHITECTURE.md`
- Master go-live checklist: `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md`
