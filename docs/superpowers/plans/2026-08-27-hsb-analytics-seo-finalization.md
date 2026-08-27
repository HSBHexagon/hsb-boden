# HSB Analytics / SEO Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish HSB production analytics/SEO hardening so production traffic is measured only on the canonical host, lead conversions use `generate_lead`, the thank-you page is noindexed/out of sitemap, release checks are green, and post-deploy GSC/GA4 evidence is collected.

**Architecture:** Keep the existing GA4 property and event model. Add hostname-gated loaders for GA4 and Cloudflare Web Analytics, preserve consent gating and non-PII event payloads, integrate the already-tested thank-you-page SEO patch, and release through the existing GitHub/Cloudflare Pages pipeline. Administrative GA4 key-event changes are treated as a separate capability gate because available connected analytics tools are read-only.

**Tech Stack:** Astro 7, TypeScript, Vitest/jsdom, GitHub Actions, Cloudflare Pages/Functions, GA4, Google Search Console, GSC Wizard.

**Spec:** `docs/superpowers/specs/2026-08-27-hsb-analytics-seo-finalization-design.md`

## Global Constraints

- Production GA4 measurement ID remains `G-VC4BJBEFTV` / property `543244027`.
- Only canonical production hostname `www.hsb-boden.de` may send production GA4 or Cloudflare Web Analytics events.
- Preview, Pages and localhost must fail closed: no production analytics.
- No Google Tag request before explicit analytics consent.
- No PII or raw lead data in analytics events.
- Successful lead event remains GA4 recommended `generate_lead`.
- No speculative CSP overhaul.
- No new GA4 property and no GTM migration.
- No real customer lead data in verification.
- Production deployment remains approval-gated through the existing workflow.

---

### Task 1: GA4 production-host isolation

**Files:**
- Modify: `src/lib/analytics.ts`
- Modify: `tests/analytics.test.ts`

**Interfaces:**
- Produces: `PRODUCTION_ANALYTICS_HOST = "www.hsb-boden.de"`
- Produces: `isProductionAnalyticsHost(hostname: string): boolean`
- `createAnalyticsLoader(...)` must suppress production GA4 when `window.location.hostname` is not the canonical host.

- [ ] **Step 1: Write failing tests**

Add tests that explicitly construct a loader with a testable hostname input and assert:

```ts
expect(isProductionAnalyticsHost("www.hsb-boden.de")).toBe(true);
expect(isProductionAnalyticsHost("hsb-boden.pages.dev")).toBe(false);
expect(isProductionAnalyticsHost("preview.hsb-boden.pages.dev")).toBe(false);
expect(isProductionAnalyticsHost("localhost")).toBe(false);
```

and that stored consent on a preview hostname still creates neither `gtag` nor the Google script.

- [ ] **Step 2: Verify RED**

Run `npm run test:run -- tests/analytics.test.ts`.
Expected: FAIL because hostname isolation does not yet exist.

- [ ] **Step 3: Minimal implementation**

Add the pure hostname predicate and gate `loadAfterConsent()` before any `gtag`, dataLayer, or script creation. Preserve current production behavior, consent update behavior and exactly-one initialization.

- [ ] **Step 4: Verify GREEN**

Run `npm run test:run -- tests/analytics.test.ts`.
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `fix(analytics): isolate production GA4 by hostname`

---

### Task 2: Cloudflare Web Analytics production-host isolation

**Files:**
- Create: `src/lib/cloudflareAnalytics.ts`
- Create: `tests/cloudflare-analytics.test.ts`
- Modify: `src/layouts/BaseLayout.astro`

**Interfaces:**
- Produces: `CLOUDFLARE_WEB_ANALYTICS_TOKEN = "8631653d94cb4fcead06570ed2275043"`
- Produces: `initializeCloudflareAnalytics(window, document)` that injects the existing beacon only on `www.hsb-boden.de` and only once.

- [ ] **Step 1: Write failing tests**

Tests must assert production creates one script with:

```ts
expect(script?.src).toBe("https://static.cloudflareinsights.com/beacon.min.js");
expect(script?.dataset.cfBeacon).toContain("8631653d94cb4fcead06570ed2275043");
```

while preview/localhost create no beacon.

- [ ] **Step 2: Verify RED**

Run `npm run test:run -- tests/cloudflare-analytics.test.ts`.
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Minimal implementation**

Move the existing static Cloudflare beacon behavior into the new runtime loader and call it from `BaseLayout.astro`. Do not change the token or add cookies/PII.

- [ ] **Step 4: Verify GREEN**

Run the Cloudflare analytics test and existing analytics tests.

- [ ] **Step 5: Commit**

Commit message: `fix(analytics): isolate Cloudflare RUM to production host`

---

### Task 3: Conversion-event contract regression

**Files:**
- Modify: `tests/tracking.test.ts`
- Modify only if test proves necessary: `src/lib/tracking.ts`

**Interfaces:**
- Successful lead submission maps to `generate_lead` with `method: "contact_form"` and `send_to: GA4_MEASUREMENT_ID`.

- [ ] **Step 1: Add regression assertions**

Assert successful lead submission never emits `purchase`, `qualify_lead` or `close_convert_lead`, and sanitized payload cannot forward name/email/phone/message.

- [ ] **Step 2: Run RED/GREEN check**

Run `npm run test:run -- tests/tracking.test.ts`.
If already green, record that the website contract was already correct and make no production-code change.

- [ ] **Step 3: Commit only test hardening if needed**

Commit message: `test(analytics): lock lead conversion contract`

---

### Task 4: Integrate thank-you page SEO fix

**Files:**
- Modify: `src/pages/danke-projektanfrage.astro`
- Modify: `src/pages/sitemap.xml.ts`
- Create: `tests/sitemap-indexability.test.ts`

**Interfaces:**
- Thank-you page carries `robots="noindex, follow"`.
- `GET()` sitemap output must not contain `/danke-projektanfrage/`.

- [ ] **Step 1: Reuse the already-reviewed PR #301 tests and patch exactly**

Apply the three-file change from PR #301 without unrelated edits.

- [ ] **Step 2: Run focused test**

Run `npm run test:run -- tests/sitemap-indexability.test.ts`.
Expected: PASS.

- [ ] **Step 3: Run sitemap consistency check**

Run `npm run check:sitemap` after build if required by the script.

- [ ] **Step 4: Commit**

Commit message: `fix(seo): remove thank-you page from index signals`

---

### Task 5: Release verification on feature branch

**Files:** no source changes unless a test exposes a real defect.

- [ ] **Step 1:** Run `npm run check`.
- [ ] **Step 2:** Run `npm run test:run`.
- [ ] **Step 3:** Run `PUBLIC_LEAD_FORM_ENABLED=true npm run build`.
- [ ] **Step 4:** Run `npm run deploy:dry-run` where credentials are not required.
- [ ] **Step 5:** Open final PR against `main`.
- [ ] **Step 6:** Require CI, Quality Assurance, Security Analysis, Lighthouse and Cloudflare preview to be green.

If any check fails, stop and return to systematic debugging; do not merge around a failing gate.

---

### Task 6: Production merge and deployment

**Files:** no new source change unless release verification requires it.

- [ ] **Step 1:** Merge only the verified final PR into `main` using the repository's normal merge policy.
- [ ] **Step 2:** Trigger `.github/workflows/deploy-production.yml` with its existing manual/production approval gate.
- [ ] **Step 3:** Verify live `https://www.hsb-boden.de/` and `/sitemap.xml` reflect the merged release.
- [ ] **Step 4:** Verify `https://www.hsb-boden.de/danke-projektanfrage/` carries `noindex, follow` and is absent from sitemap.

If the connected GitHub surface cannot dispatch a workflow, record `PRODUCTION_DEPLOY=OWNER_UI_GATE` and provide only the single workflow-dispatch action; do not claim deployment occurred.

---

### Task 7: Post-deploy GA4/GSC verification and closure

**Files:**
- Update after verification: `docs/analytics/GA4_GSC_EVENT_TRACKING_READINESS.md`
- Optionally update project checkpoint docs only with observed facts.

- [ ] **Step 1: GA4 production transport**

Query the deployment day and confirm production page paths are present. Preview `/client/*` history must not be treated as valid production traffic.

- [ ] **Step 2: GA4 conversion administration**

Read current key-event names. Target is `generate_lead`.
If no write-capable GA4 Admin connector is available, mark `GA4_KEY_EVENT_ADMIN=OWNER_UI_GATE` and specify the minimum one-time GA4 UI action: create/mark `generate_lead` as key event and retire unrelated website lead key-event definitions as appropriate.

- [ ] **Step 3: GSC**

Verify Search Console access, sitemap status and indexability tracking. Deindexing of the thank-you URL may lag; the release passes when the live directive and sitemap state are correct.

- [ ] **Step 4: Final state**

Only set `FINAL=PASS` if all automatable release gates are proven and no unresolved capability gate affects correctness. Otherwise use `FINAL=DEGRADED` with the exact single owner/UI gate, never a vague blocker.
