# WAF_CACHE_RATE_LIMIT_READINESS — HSB-Boden / HEXAFLOOR

Status: `waf-cache-rate-limit-documented-not-activated-awaiting-dns`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No WAF rule created. No cache rule created. No rate limit set. No bot protection activated.**
All Cloudflare security and performance rules require zone status `Active` (post-NS-switch).
This document defines what should be configured and when.

Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
Preflight checklist: `docs/cloudflare/GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`

---

## Current State

Zone `hsb-boden.de` is `pending`. No WAF rules, cache rules, or rate limits can be created
before the zone is `Active`. All items below are planned configuration for post-DNS-switch.

---

## WAF (Web Application Firewall)

### Plan Context

Cloudflare Free plan includes:
- Cloudflare Managed Ruleset (limited — not all rules available on Free)
- Custom WAF rules: 5 rules on Free, 20 on Pro

### Recommended Minimum WAF Rules (Post-Switch)

| Rule | Action | Priority |
|------|--------|----------|
| Block requests to `/api/lead` from non-browser User-Agents | Block | 1 |
| Challenge known bad IPs (Cloudflare Managed Rules) | Managed Challenge | 2 |
| Allow all other traffic | Allow | 100 |

The `/api/lead` endpoint has CORS allowlist hardcoded in `src/pages/api/lead.ts:7–9`
(only `https://hsb-boden.de` and `https://www.hsb-boden.de`). Worker-level CORS is the
primary protection. WAF is optional secondary hardening.

### WAF Dashboard Path

**Websites → hsb-boden.de → Security → WAF**

### Activation Gate

- [ ] Zone `Active`
- [ ] Basic traffic established (1–3 days minimum to observe before tuning)
- [ ] Joel approval for each rule before activation
- [ ] Test rule in `Log` mode before switching to `Block`

---

## Cache Rules

### Static Asset Caching Strategy

Cloudflare automatically caches responses where `Cache-Control` headers allow it.
The Worker `[assets]` binding serves static files with appropriate headers.

| Asset Type | Recommended TTL | Cloudflare Behavior |
|------------|----------------|---------------------|
| PDF flyers | 7 days (`max-age=604800`) | Cached at edge |
| Brand images/logos | 30 days (`max-age=2592000`) | Cached at edge |
| JS/CSS bundles (hashed names) | 1 year (`immutable`) | Cached at edge |
| HTML pages | No-store or short TTL | Not cached (dynamic) |
| `/api/lead` | No-store | Never cached |

### Cache Rules Dashboard Path

**Websites → hsb-boden.de → Rules → Cache Rules**

### Activation Gate

- [ ] Zone `Active`
- [ ] Static asset headers verified on production worker
- [ ] Cache rules created in `Log` mode first
- [ ] Joel approval before switching to `Cache` action

---

## Rate Limiting

### `/api/lead` Rate Limit (Recommended)

Prevent form spam by limiting the lead submission endpoint:

| Parameter | Value |
|-----------|-------|
| Path | `/api/lead` |
| Method | `POST` |
| Threshold | 5 requests per 10 minutes per IP |
| Action | `Block` (or `Managed Challenge` initially) |
| Duration | 1 hour block after threshold |

> **Important:** Rate limiting on Free plan is limited. Check current plan capabilities
> before configuring. Cloudflare Free includes basic rate limiting from 2024.

### General Rate Limit (Optional)

| Parameter | Value |
|-----------|-------|
| Path | `/*` |
| Threshold | 500 requests per 10 minutes per IP |
| Action | `Managed Challenge` |

Dashboard path: **Websites → hsb-boden.de → Security → WAF → Rate Limiting Rules**

### Activation Gate

- [ ] Zone `Active`
- [ ] Plan capabilities verified (Free vs Pro)
- [ ] Joel approval
- [ ] Test with a controlled burst before activating Block action

---

## Bot Protection

### Free Plan Bot Protection

Cloudflare Free includes:
- Bot Fight Mode (basic)
- JavaScript challenge for known bad bots

Dashboard path: **Websites → hsb-boden.de → Security → Bots**

### Activation Gate

- [ ] Zone `Active`
- [ ] Enable Bot Fight Mode (toggle — requires approval)
- [ ] Monitor analytics for 1 week before adding custom bot rules

---

## Page Rules / Transform Rules (HTTPS Redirect)

### HTTPS Enforcement

After zone is `Active`, enforce HTTPS:

Dashboard: **Websites → hsb-boden.de → SSL/TLS → Edge Certificates**
- [ ] Enable "Always Use HTTPS" toggle
- [ ] Set "Minimum TLS Version" to TLS 1.2

### www Redirect

If `www.hsb-boden.de` should redirect to apex (or vice versa), configure via:

Dashboard: **Websites → hsb-boden.de → Rules → Redirect Rules**

Example — www → apex:
- Match: `http://www.hsb-boden.de/*` or `https://www.hsb-boden.de/*`
- Action: Dynamic redirect → `https://hsb-boden.de/${1}` (301)

Worker routes currently handle both apex and www. Verify redirect behavior in Worker
before adding a separate Cloudflare redirect rule.

---

## Activation Sequence

Execute in this order after zone becomes `Active`:

1. Verify all DNS records (see `GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`)
2. Enable "Always Use HTTPS"
3. Enable Bot Fight Mode
4. Observe traffic for 48 hours
5. Add WAF rules in `Log` mode
6. After 48 hours of Log observation: switch to `Block` if no false positives
7. Add rate limiting on `/api/lead`
8. Add cache rules for static assets
9. Joel signs off each step

---

## Forbidden Actions

- No WAF rules before zone is `Active`
- No rate limits before zone is `Active`
- No cache rules before static asset headers are verified
- No rules activated without explicit Joel approval per rule
- No changes to Bot Fight Mode without reviewing analytics first

---

## Summary

| Feature | Status Today | When to Activate |
|---------|-------------|-----------------|
| WAF Managed Rules | Not active | After zone Active + 48h traffic |
| Custom WAF Rules | Not active | After WAF managed rules stable |
| Rate Limiting `/api/lead` | Not active | After zone Active + approval |
| Bot Fight Mode | Not active | After zone Active (toggle) |
| Cache Rules | Not active | After static header verification |
| HTTPS Always | Not active | Immediately after zone Active |
| www → apex redirect | Not active | After Worker route behavior verified |
