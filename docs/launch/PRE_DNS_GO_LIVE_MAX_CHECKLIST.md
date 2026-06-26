# PRE_DNS_GO_LIVE_MAX_CHECKLIST — HSB-Boden / HEXAFLOOR

Status: `checklist-ready-waiting-for-dns-trigger`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

This is the master go-live checklist. Work through it in order.
All items marked ❌ are **blocking**. Do not proceed past a blocking item without resolving it.

Canonical Cloudflare execution: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
Canonical Cloudflare readiness: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`

---

## HARD STOP — Read Before Starting

Two external blockers must exist before this checklist is meaningful:

1. **DNS/NS switch for `hsb-boden.de`** — domain registrar must switch NS records to Cloudflare
2. **Real 5,000-lead dataset** — actual lead list for outreach

If neither exists, **stop here**. Do not invent work.

---

## Block 1 — Pre-Switch Verification (Do Anytime, Safe)

### 1.1 Worker State

```bash
npx wrangler whoami
# Expected: cherinojoel@gmail.com

npx wrangler deployments list --name hsb-boden
# Expected: latest deployment listed, no routes

npx wrangler secret list --name hsb-boden
# Expected: LEAD_WEBHOOK_URL listed
```

- [ ] Wrangler authenticated as `cherinojoel@gmail.com`
- [ ] Worker `hsb-boden` deployed, no routes
- [ ] Secret `LEAD_WEBHOOK_URL` present

### 1.2 Code State

```bash
git status
# Expected: nothing to commit, main up to date

npm run check
# Expected: 0 type errors

npm run test:run
# Expected: all tests pass
```

- [ ] `git status` clean
- [ ] Type check passes
- [ ] Tests pass

### 1.3 Build State

```bash
npm run build
git ls-files dist | head
rm -rf dist
```

- [ ] Build succeeds
- [ ] `dist/` removed after check (never committed)

### 1.4 Workers.dev End-to-End Test

```bash
curl -o /dev/null -s -w "%{http_code}" https://hsb-boden.cherinojoel.workers.dev/
# Expected: 200
```

- [ ] Homepage returns 200 on workers.dev
- [ ] Submit one test form submission — verify new row in CRM-Light
- [ ] All three PDF flyers accessible on workers.dev (internal test only)

---

## Block 2 — Email/DKIM (Required Before Outreach)

### 2.1 DKIM Activation

- [ ] M365 Admin Center: DKIM enabled for `hsb-boden.de`
- [ ] DKIM CNAME values retrieved from M365 Admin Center
- [ ] CNAMEs added to current DNS (Kasserver) or Cloudflare (after NS switch)

```bash
dig CNAME selector1._domainkey.hsb-boden.de
dig CNAME selector2._domainkey.hsb-boden.de
# Both must return CNAME values — not empty
```

- [ ] `selector1._domainkey.hsb-boden.de` resolves
- [ ] `selector2._domainkey.hsb-boden.de` resolves

### 2.2 Test Mail

- [ ] Send test from `j-cherino@hsb-boden.de` to a Gmail account
- [ ] Check headers: `dkim=pass`, `spf=pass`, `dmarc=pass`
- [ ] Inbox delivery confirmed (not spam folder)

---

## Block 3 — DNS/NS Switch (External Trigger)

This block starts when the domain registrar switches NS to Cloudflare.

### 3.1 NS Switch Verification

```bash
dig NS hsb-boden.de
# Expected: Cloudflare NS values (not ns5.kasserver.com / ns6.kasserver.com)
```

- [ ] NS records point to Cloudflare nameservers
- [ ] Zone `hsb-boden.de` shows `Active` in Cloudflare Dashboard

### 3.2 DNS Record Verification in Cloudflare

Dashboard: **Websites → hsb-boden.de → DNS → Records**

- [ ] MX: `hsbboden-de0i.mail.protection.outlook.com.` — DNS-only
- [ ] SPF TXT: `v=spf1 include:spf.protection.outlook.com -all` — DNS-only
- [ ] DMARC TXT: `v=DMARC1; p=none;` — DNS-only
- [ ] Autodiscover CNAME: `autodiscover.outlook.com.` — DNS-only
- [ ] DKIM selector1 CNAME — DNS-only
- [ ] DKIM selector2 CNAME — DNS-only
- [ ] MS= TXT verification record (from M365) — DNS-only

### 3.3 HTTPS Enforcement

Dashboard: **Websites → hsb-boden.de → SSL/TLS → Edge Certificates**

- [ ] "Always Use HTTPS" enabled
- [ ] "Minimum TLS Version" set to TLS 1.2

---

## Block 4 — Cutover (Requires Explicit Approval)

**Do not execute Block 4 without Joel's explicit approval after Block 3 is complete.**

Follow `docs/PHASE_C_CUTOVER_RUNBOOK.md` exactly.

### 4.1 Production Deploy (Final Pre-Route Deploy)

```bash
wrangler deploy --name hsb-boden --var ENVIRONMENT:production
npx wrangler deployments list --name hsb-boden
```

- [ ] Deployment successful
- [ ] Latest deployment shows `ENVIRONMENT=production`

### 4.2 Worker Route Creation

**Only after zone is `Active` AND Joel approval is explicit.**

Routes to create in Cloudflare Dashboard:
```
hsb-boden.de/*          → Worker: hsb-boden
www.hsb-boden.de/*      → Worker: hsb-boden
```

- [ ] Route `hsb-boden.de/*` created
- [ ] Route `www.hsb-boden.de/*` created

### 4.3 Post-Route Verification

```bash
curl -o /dev/null -s -w "%{http_code}" https://hsb-boden.de/
# Expected: 200

curl -o /dev/null -s -w "%{http_code}" https://www.hsb-boden.de/
# Expected: 200 or 301 redirect to apex

curl -o /dev/null -s -w "%{http_code}" https://hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf
# Expected: 200 (PDF served)
```

- [ ] `hsb-boden.de` returns 200
- [ ] `www.hsb-boden.de` returns 200 or redirects correctly
- [ ] PDF flyers accessible on production domain

### 4.4 Form End-to-End on Production Domain

- [ ] Submit test form on `https://hsb-boden.de/`
- [ ] New row appears in CRM-Light
- [ ] Status = `neu`, Quelle = `website-form`

---

## Block 5 — Post-Launch Setup (First Week)

### 5.1 Google Search Console

- [ ] GSC property `hsb-boden.de` verified (DNS TXT method)
- [ ] Sitemap submitted: `https://hsb-boden.de/sitemap.xml`

### 5.2 Cloudflare Security (Basic)

Dashboard: **Websites → hsb-boden.de → Security → Bots**

- [ ] Bot Fight Mode enabled (after Joel approval)

### 5.3 Analytics Verification

- [ ] GA4 events firing after consent (test in DebugView)
- [ ] `generate_lead` event visible after test form submission

### 5.4 Cloudflare Web Analytics (Optional)

- [ ] Decide: use GA4 only, or add Cloudflare Web Analytics
- [ ] If added: verify beacon ID matches code, no duplicate counting

---

## Block 6 — Outreach Gate

**Do not start outreach without all items in this block.**

- [ ] DKIM active and test mail shows `dkim=pass`
- [ ] Real lead dataset available and reviewed by Joel
- [ ] `docs/launch/PHASE_7_COMPLIANCE_GATE.md` completed with real data
- [ ] `Versandfreigabe = yes` set per recipient in CRM
- [ ] `Opt-out-Status ≠ opted_out` per recipient
- [ ] Recipient basis documented in CRM (`Beziehung / Kontaktgrund`)
- [ ] First batch approved (Joel + JORDIE joint approval)
- [ ] Production domain live (Block 4 complete)

---

## External Blockers Remaining

After this checklist is complete, only two external blockers remain before outreach can begin:

| Blocker | Owner | Status |
|---------|-------|--------|
| DNS/NS switch for `hsb-boden.de` | Domain registrar (external) | ❌ Pending |
| Real 5,000-lead dataset | External input | ❌ Pending |

Everything else in this repo is internally completable once those two inputs arrive.

---

## Rollback Reference

If anything goes wrong during Blocks 3–4:
See `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` → **Rollback Plan** section.

Primary rollback: delete Worker routes → traffic falls back to existing WordPress origin.
