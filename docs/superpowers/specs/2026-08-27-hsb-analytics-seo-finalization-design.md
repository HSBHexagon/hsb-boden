# HSB Analytics / SEO Finalization Design

Date: 2026-08-27
Status: Approved in chat, awaiting written-spec review before implementation
Repository: HSBHexagon/hsb-boden

## Goal

Bring the HSB production website to a verifiable final state across GA4, GSC, GitHub CI and Cloudflare Pages. Closure is reached only when production traffic is measured correctly, preview traffic cannot pollute production analytics, lead conversion tracking matches the website event contract, SEO release gates are clean, and the deployed state is independently verified.

## Current evidence

1. Search Console access to `https://www.hsb-boden.de/` works and GSC Wizard can query production data.
2. GA4 property `properties/543244027` (`HSBBODENCLOUDFLAIRE`) is linked to the production site.
3. Measurement ID in source is `G-VC4BJBEFTV`.
4. On 2026-08-27 GA4 received a real production visit on `/`: one session, one active user and one page view. Therefore the base transport `www.hsb-boden.de -> gtag -> GA4` is working.
5. Existing GA4 key events are `close_convert_lead`, `purchase` and `qualify_lead`, while the website contract maps a successful lead submission to `generate_lead`.
6. `src/lib/analytics.ts` currently has a globally hard-coded production measurement ID and does not gate production analytics by hostname. Any preview build that executes the same bundle can send to the production GA4 property after consent.
7. `src/layouts/BaseLayout.astro` also loads the Cloudflare Web Analytics beacon without production-host isolation.
8. Production lead delivery is build-time gated by `PUBLIC_LEAD_FORM_ENABLED`; the production workflow sets it to `true`, but the public source default is false and runtime Pages bindings are separate. This creates a configuration-drift risk that must be verified against the real deployment.
9. PR #301 implements `noindex, follow` for `/danke-projektanfrage/` and removes the thank-you URL from the sitemap. Its CI/QA/Security/Lighthouse/Preview checks were green and it remains unmerged.

## Architecture decision

Use one canonical production analytics surface only:

- Production host: `www.hsb-boden.de` (and canonical redirect handling for bare domain as applicable).
- Production GA4: `G-VC4BJBEFTV` / property `543244027`.
- Production Cloudflare Web Analytics: enabled only on canonical production host.
- Preview, branch, Pages and localhost builds: no events may be sent to the production GA4 or production Cloudflare Analytics dataset.

Do not create a new GA4 property unless new evidence shows the current property is unusable. Existing production history should be preserved.

## Components and changes

### 1. GA4 production isolation

Refactor analytics initialization so the production measurement ID is used only when the browser hostname matches the canonical production host. The decision must be testable as a pure predicate where possible.

Required behavior:

- No Google Tag request before analytics consent.
- No production Google Tag request on preview/Pages/localhost even after consent.
- Exactly one GA4 config/page-view initialization on production after consent.
- Consent withdrawal in the current tab continues to set analytics storage to denied.
- No PII or raw lead data enters GA4 events.

### 2. Conversion contract

Keep the website event contract centered on the GA4 recommended lead event `generate_lead` for a successful project inquiry.

Required behavior:

- `lead_form_start`: first meaningful form interaction after analytics consent.
- `generate_lead`: only after `/api/lead` returns success and before redirect to thank-you page.
- Optional click events such as phone/email/CTA remain non-key events unless there is a specific business requirement.
- No `purchase` event for this B2B lead website.

The current GA4 Admin key-event configuration must be reconciled with this contract. The target key event is `generate_lead`; unrelated key-event definitions should not be used for website lead reporting.

Because GSC Wizard and the official Google Analytics MCP are read-only for this administrative mutation, the implementation must clearly separate code-complete status from GA4-admin-complete status. If no connected write-capable Google Analytics Admin action is available, the single unavoidable GA4 UI action is documented precisely and the rest is completed automatically.

### 3. Cloudflare analytics isolation

The Cloudflare Web Analytics beacon must be production-only, matching the same canonical-host policy as GA4. Preview deployments remain useful for functional testing but do not contaminate production RUM analytics.

No CSP expansion is included unless verification shows current headers block required production requests. Do not add speculative CSP changes.

### 4. Lead-form deployment consistency

Verify the actual production deployment against the intended workflow contract:

- Build with `PUBLIC_LEAD_FORM_ENABLED=true` only for production.
- Runtime Pages environment must have a valid `LEAD_WEBHOOK_CONFIG` (preferred) or documented temporary fallback plus `RATE_LIMIT_KV`.
- If runtime bindings are absent, the form must fail closed rather than collect PII without delivery.
- A real customer lead must not be used for verification. Use an internal synthetic test payload only if the endpoint is confirmed isolated/safe and the existing project rules permit it.

### 5. SEO closure

Integrate the already-tested thank-you-page fix from PR #301:

- `/danke-projektanfrage/` => `noindex, follow`.
- Remove from sitemap.
- Preserve navigation/redirect behavior after successful form submission.

After production deploy, verify the live page headers/meta and sitemap, then record the expected Search Console transition. Google may take time to deindex the URL; closure requires the live directive and sitemap state to be correct, not instantaneous removal from the index.

### 6. GSC Wizard final configuration

Retain the current production property, brand terms, groups and indexing tracker. Re-run after deployment:

- GSC property access.
- Sitemap status.
- Indexing tracker.
- Key landing pages.
- GSC + GA4 blended landing pages after enough settled GA4 data exists.

Do not claim GA4 historical quality is repaired retroactively; polluted/invalid historical rows remain historical data.

## Test strategy

Follow strict TDD for every code change.

### RED tests first

Add or extend tests to prove the current defects:

1. Analytics loader must not load production GA4 on non-production hosts even with stored consent.
2. Production host must load exactly once after consent.
3. Cloudflare Web Analytics must not render/load on preview host.
4. Production layout must retain Cloudflare beacon on the canonical host.
5. Lead event mapping remains `generate_lead` and sends no disallowed payload fields.
6. Thank-you page remains excluded from sitemap and carries `noindex, follow`.

### GREEN implementation

Make the smallest implementation required to pass those tests. Avoid unrelated refactors.

### Full verification

Run at minimum:

- `npm run check`
- `npm run test:run`
- production build
- existing Quality Assurance workflow
- Security Analysis
- Lighthouse
- Cloudflare branch preview

No merge until all required checks are green.

## Release flow

1. Implement on an isolated feature branch based on current `main`.
2. Rebase/cherry-pick the tested PR #301 changes into the final feature branch or merge #301 first if doing so preserves a clean release history.
3. Open one final PR describing analytics isolation, conversion contract and SEO fix.
4. Obtain green CI/QA/Security/Lighthouse and a successful Cloudflare preview.
5. Merge only after verification.
6. Trigger the repository's explicit production deployment workflow.
7. Verify production HTML/JS behavior and analytics transport.
8. Query GA4 via GSC Wizard for the deployment day and confirm production paths, sessions and events.
9. Verify GSC sitemap/indexability state.
10. Update project documentation from readiness/partial status to the exact verified state.

## Closure criteria

`FINAL=PASS` only when all applicable items below are proven:

- `GA4_PRODUCTION_TRANSPORT=PASS`
- `GA4_PREVIEW_ISOLATION=PASS`
- `GA4_CONVERSION_EVENT_CONTRACT=PASS`
- `GA4_KEY_EVENT_ADMIN=PASS` or explicitly `OWNER_UI_GATE` if no write-capable connector exists
- `CLOUDFLARE_PRODUCTION_ANALYTICS_ISOLATION=PASS`
- `LEAD_FORM_DEPLOYMENT_CONSISTENCY=PASS` or fail-closed with documented runtime-binding blocker
- `THANK_YOU_NOINDEX_LIVE=PASS`
- `THANK_YOU_REMOVED_FROM_SITEMAP_LIVE=PASS`
- `CI=PASS`
- `QA=PASS`
- `SECURITY=PASS`
- `LIGHTHOUSE=PASS`
- `CLOUDFLARE_PRODUCTION_DEPLOY=PASS`
- `GSC_POST_DEPLOY_VERIFY=PASS`

If a capability cannot be mutated through available connected tools, do not misreport it as complete. Mark the exact external gate and provide the minimum one-time action required.

## Non-goals

- No GA4 property rebuild without evidence.
- No GTM migration merely for architecture preference.
- No broad website redesign.
- No unrelated SEO content expansion in this release.
- No speculative CSP overhaul.
- No use of real personal lead data for testing.

## Rollback

All production code changes must be contained in a normal GitHub PR and reversible by commit/revert. Production analytics isolation must fail closed: a host mismatch means no production analytics rather than routing to an alternate property. The manual production deployment gate remains intact.