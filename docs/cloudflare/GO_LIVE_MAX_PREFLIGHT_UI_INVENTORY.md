# GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY — HSB-Boden / HEXAFLOOR

Status: `preflight-documented-awaiting-dns-ns-switch`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No Cloudflare mutation performed here. No routes created. No DNS changed.**
This document inventories the Cloudflare Dashboard UI state that must be verified
before and after the DNS/NS switch. Execute only after NS switch + explicit approval.

Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
Cutover execution: `docs/PHASE_C_CUTOVER_RUNBOOK.md`

---

## Cloudflare Account Context

| Field | Value |
|-------|-------|
| Account | `cherinojoel@gmail.com` |
| Account ID | `043ec899a435f150995d89f402ed7b12` |
| Zone | `hsb-boden.de` |
| Zone ID | `2aefa04f69a2339b2f9f3f2876d7e35c` |
| Zone status | `pending` — NS not yet switched |
| Wrangler version | `4.103.0` |

---

## Pre-Switch UI Inventory (Verify Before NS Switch)

### Workers

| Worker | Expected Status | Verification Command |
|--------|----------------|---------------------|
| `hsb-boden` | Deployed, route-less, `workers.dev` accessible | `npx wrangler deployments list --name hsb-boden` |
| `hsb-boden-preview` | Deployed, preview-only | `npx wrangler deployments list --name hsb-boden-preview` |

Verify in Cloudflare Dashboard: **Workers & Pages → hsb-boden → Deployments**

### KV Namespaces

| Namespace | ID | Purpose |
|-----------|-----|---------|
| `hsb-boden-session` | `dc91654846b546e39c273d85f559a5a2` | Session storage |

Dashboard path: **Workers & Pages → KV**

### Worker Secrets

| Secret | Worker | Status |
|--------|--------|--------|
| `LEAD_WEBHOOK_URL` | `hsb-boden` | Set — value never printed |

Dashboard path: **Workers & Pages → hsb-boden → Settings → Variables and Secrets**

### DNS Records (Current — Kasserver)

These must be replicated to Cloudflare Dashboard before or during NS switch:

| Type | Name | Value | Proxy |
|------|------|-------|-------|
| A | `hsb-boden.de` | `85.13.130.17` | DNS-only until cutover |
| A | `www.hsb-boden.de` | `85.13.130.17` | DNS-only until cutover |
| MX | `hsb-boden.de` | `hsbboden-de0i.mail.protection.outlook.com.` | DNS-only |
| TXT | `hsb-boden.de` | `v=spf1 include:spf.protection.outlook.com -all` | DNS-only |
| TXT | `hsb-boden.de` | `MS=ms97748082` | DNS-only |
| TXT | `_dmarc.hsb-boden.de` | `v=DMARC1; p=none;` | DNS-only |
| CNAME | `autodiscover.hsb-boden.de` | `autodiscover.outlook.com.` | DNS-only |
| CNAME | `selector1._domainkey.hsb-boden.de` | (from M365 Admin Center — retrieve before switch) | DNS-only |
| CNAME | `selector2._domainkey.hsb-boden.de` | (from M365 Admin Center — retrieve before switch) | DNS-only |

> **Mail records must be DNS-only (grey cloud). Cloudflare does not proxy mail.**
> DKIM selector values must be obtained from M365 Admin Center before entry.

---

## Post-Switch UI Checklist (Execute Only After NS Switch + Zone Active)

### 1. Verify Zone Status

Dashboard: **Websites → hsb-boden.de → Overview**

- [ ] Zone status shows `Active`
- [ ] Nameservers show Cloudflare NS values

### 2. Verify DNS Records

Dashboard: **Websites → hsb-boden.de → DNS → Records**

- [ ] A record for apex pointing to production (or Worker route after cutover)
- [ ] A record for `www` pointing to production (or Worker route after cutover)
- [ ] MX record present — DNS-only
- [ ] SPF TXT record present — DNS-only
- [ ] DMARC TXT record present — DNS-only
- [ ] Autodiscover CNAME present — DNS-only
- [ ] DKIM selector CNAMEs present — DNS-only

### 3. Verify Worker Routes (Create Only After Explicit Approval)

Planned routes — **do not create until cutover approval**:

```
hsb-boden.de/*          → Worker: hsb-boden
www.hsb-boden.de/*      → Worker: hsb-boden
```

Dashboard path: **Workers & Pages → hsb-boden → Settings → Triggers → Routes**

- [ ] Routes created ONLY after zone is `Active` AND cutover approval granted
- [ ] Verify no route exists before approval: check dashboard and `wrangler routes list`

### 4. Verify Production Worker Environment

```bash
npx wrangler deployments list --name hsb-boden
```

Expected: latest deployment with `ENVIRONMENT=production` visible.

### 5. Cloudflare Web Analytics (Optional)

Dashboard: **Analytics & Logs → Web Analytics**

If enabled, verify the beacon script ID matches `src/layouts/BaseLayout.astro`.
Cloudflare Web Analytics is privacy-first and does not require cookie consent.
This is optional — GA4 (already code-present) is the primary analytics tool.

---

## Forbidden UI Actions Before Approval

- No route creation before zone is `Active` AND explicit cutover approval
- No WAF rule activation before approval (`docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`)
- No Turnstile site key activation before server-side validation is confirmed
- No R2 public bucket exposure before asset strategy approval (`docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`)
- No Email Routing activation before M365 DKIM is resolved
- No Access policy creation without approval
- No AI Gateway creation before AI feature is built and approved

---

## Verification Commands (Pre-Switch, Safe to Run Anytime)

```bash
# Confirm worker is deployed and route-less
npx wrangler deployments list --name hsb-boden

# Confirm zone status
npx wrangler zone list 2>/dev/null | grep hsb-boden || echo "Use dashboard to verify zone status"

# Confirm wrangler identity
npx wrangler whoami

# Confirm production URL is accessible
curl -o /dev/null -s -w "%{http_code}" https://hsb-boden.cherinojoel.workers.dev/
```

---

## Go/No-Go Gate

| Gate | Status |
|------|--------|
| Zone `hsb-boden.de` shows `Active` | ❌ Pending NS switch |
| All DNS records entered in Cloudflare Dashboard | ❌ Pending NS switch |
| DKIM CNAMEs retrieved from M365 and entered | ❌ Pending M365 activation |
| Cutover approval explicitly granted | ❌ Pending |
| Worker routes created | ❌ Blocked until all gates above pass |

If any gate shows ❌, stop. Do not proceed with route creation or cutover.
