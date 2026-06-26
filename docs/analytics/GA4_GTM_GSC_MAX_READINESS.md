# GA4_GTM_GSC_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `analytics-code-present-consent-gated-gsc-pending-domain`
Stand: 2026-06-26 | Canonical since this sweep.
Source baseline: `SEO_GO_LIVE_CHECKLIST.md`

No analytics activation, no property creation on external platforms, no consent bypass
performed here. This document is readiness truth only.

---

## What Is Already Present in Code

### Google Analytics 4 (GA4)

| Item | Status | Location |
|------|--------|----------|
| GA4 measurement ID | `G-VC4BJBEFTV` (present in code) | `src/layouts/BaseLayout.astro:31–36` |
| gtag.js snippet | Present — loaded via `<script async>` | `src/layouts/BaseLayout.astro:30–37` |
| Consent gate (DSGVO) | Present — `CookieConsent.astro` controls loading | `src/components/layout/CookieConsent.astro:2` |
| i18n consent copy | 6 languages | `src/lib/i18n.ts:55,70,85,100,115,130` |

GA4 code is in the build and deployed on the production worker.
It fires only after user consent via the cookie consent component.

### Cookie Consent (DSGVO)

| Item | Status |
|------|--------|
| CookieConsent component | Present — DSGVO-compliant gating |
| LocalStorage persistence | Documented as present |
| Consent before GA4 load | Enforced in code |

### Technical SEO (relevant to GSC)

| Item | Status |
|------|--------|
| `robots.txt` | Dynamic route `src/pages/robots.txt.ts` — present |
| `sitemap.xml` | Dynamic route `src/pages/sitemap.xml.ts` — present |
| Canonical URLs | Present per page (incl. multilingual de/en/fr/nl/pl/tr + hreflang) |
| Structured Data (JSON-LD) | Present — LocalBusiness and related schemas |
| Open Graph / Twitter Cards | Present — OG images implemented |
| Lighthouse (2026-06-26) | Performance 95, Accessibility 100, Best Practices 100, SEO 100 |

---

## What Is Only Prepared, Not Activated

| Item | State |
|------|-------|
| Google Search Console property | Not yet created / not yet verified for `hsb-boden.de` |
| GSC domain verification | Blocked — requires live domain active on Cloudflare |
| GA4 property configuration | ID present in code; dashboard configuration not verified |
| GA4 events / goals | Not configured in GA4 dashboard |
| GTM container | Not present in code; not required currently |

---

## What Can Be Pre-Created Before DNS

Before the NS switch and domain cutover, these steps can be completed:

1. **Google Search Console** — add property for `hsb-boden.de` using DNS TXT verification:
   - GSC → Add property → Domain property → `hsb-boden.de`
   - GSC generates a TXT record: `google-site-verification=<value>`
   - Add that TXT to Kasserver DNS (or Cloudflare DNS before NS switch)
   - Verification completes when DNS propagates; does not require live domain

2. **GA4 dashboard review** — confirm `G-VC4BJBEFTV` property is configured correctly
   with correct domain, data retention, and GDPR settings in the GA4 interface

3. **Consent settings in GA4** — configure consent mode if required by policy

---

## What Must Wait for Live Domain Cutover

- GSC verification via HTML meta tag (requires live domain serving the tag)
- Sitemap submission to GSC (`https://hsb-boden.de/sitemap.xml`)
- GSC indexing requests
- Real GA4 traffic data collection (consent-gated, live domain required)
- Core Web Vitals field data in GSC (real user data, live domain required)

---

## Consent Dependency Before Activation

GA4 fires only after explicit user consent. This is enforced in code.
No consent bypass is permitted.
Any changes to consent logic require separate code approval and rebuild.

---

## Activation Blocked Until

- [ ] DNS/NS switch complete — zone `hsb-boden.de` active
- [ ] Explicit approval to activate GA4 in production
- [ ] GSC property verified
- [ ] Consent implementation confirmed compliant for go-live

---

## Reference

- SEO baseline: `SEO_GO_LIVE_CHECKLIST.md`
- Technical architecture: `docs/ARCHITECTURE.md`
- Cutover runbook: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
- Operator handoff: `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`
