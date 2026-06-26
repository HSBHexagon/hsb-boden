# FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT — HSB-Boden / HEXAFLOOR

> **Historical/Final-Audit Evidence Only**
> This document records the Cloudflare Workers readiness state as audited up to 2026-06-26.
> It is preserved as final audit evidence and is no longer the active canonical source.
>
> **Canonical Cloudflare provider-readiness document:**
> `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
>
> **Cutover execution runbook:**
> `docs/PHASE_C_CUTOVER_RUNBOOK.md`
>
> Do not maintain two active canonical Cloudflare readiness documents.
> Use `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` for all new decisions.

---

## Verdict (at time of audit)

`cloudflare-workers-ready-awaiting-dns-ns-switch`

## Verified readiness

- Worker config: [wrangler.toml](/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/wrangler.toml) exists; top-level worker is `hsb-boden-preview`, production worker is `hsb-boden`
- Preview worker: documented as `hsb-boden-preview`
- Production worker: documented as `hsb-boden`, route-less until cutover
- Production routes: only documented, not created; target patterns remain `hsb-boden.de/*` and `www.hsb-boden.de/*`
- Zone status: repo truth and runbook still describe `hsb-boden.de` as `pending`
- Secrets: `LEAD_WEBHOOK_URL` is documented as set; value not printed
- Cutover runbook: [docs/PHASE_C_CUTOVER_RUNBOOK.md](/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden/docs/PHASE_C_CUTOVER_RUNBOOK.md) exists and remains the canonical trigger path
- Read-only Wrangler verification: `npx wrangler --version` = `4.103.0`; `npx wrangler whoami` confirms logged-in account `cherinojoel@gmail.com` / `043ec899a435f150995d89f402ed7b12`
- Required trigger: DNS/NS active plus explicit approval

## Hidden repo risks

- `.github/workflows/deploy-production.yml` used `deploy --env production` (broken for production) — **RESOLVED in commit `a28fbb2`**: replaced with `--name hsb-boden --var ENVIRONMENT:production`
- `.github/workflows/ci.yml` used unpinned `actions/checkout@v4` and `actions/setup-node@v4` — **RESOLVED in commit `a28fbb2`**: all action refs pinned to full commit SHAs

All workflow risks from this audit have been resolved. See `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` for current state.

## Not executed

- no deploy
- no route creation
- no DNS mutation
- no secret mutation
- no Cloudflare setting mutation

## Route trigger checklist

Only after DNS/NS is active and explicit approval exists:

1. verify zone active
2. verify DNS records and proxied hostnames
3. verify production Worker route-less state
4. verify secret exists without printing value
5. execute documented route setup from runbook
6. verify `https://hsb-boden.de`
7. verify `/kontakt/` real form to CRM
