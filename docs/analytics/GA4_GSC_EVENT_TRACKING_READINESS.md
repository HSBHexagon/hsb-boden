# GA4_GSC_EVENT_TRACKING_READINESS — HSB-Boden / HEXAFLOOR

Status: `ga4-lead-events-in-pr-gsc-url-prefix-active-owner-gates-open`
Stand: 2026-07-15 | Verifizierter Implementierungs- und Owner-Gate-Stand.

**No analytics/property activation and no GSC dashboard mutation were performed here.**
PR #86 implements the lead-event delivery path. It is not production-active until
review, merge, and the approval-gated production deployment are complete.

Canonical analytics truth: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`

---

## GA4 Code State

| Item | Status | Location |
|------|--------|----------|
| GA4 Measurement ID | `G-VC4BJBEFTV` — present in code | `src/layouts/BaseLayout.astro:31–36` |
| gtag.js snippet | Present and deployed | `src/layouts/BaseLayout.astro:30–37` |
| Consent gate (DSGVO) | Active — CookieConsent component | `src/components/layout/CookieConsent.astro` |
| Consent Mode default | `denied` before the GA4 config command | `src/layouts/BaseLayout.astro` |
| Custom event privacy guard | `hsb:tracking`, `dataLayer`, and `gtag` require explicit analytics consent plus allowlisted parameter names and values | `src/lib/tracking.ts` |
| Custom event routing | `send_to` limits HSB custom events to the GA4 destination even if the Google tag has other linked destinations | `src/lib/tracking.ts` |
| Lead redirect delivery guard | Successful submits await the Google event callback or a bounded local fallback before navigation | `src/lib/tracking.ts`, `src/components/forms/LeadForm.astro` |
| Implemented call sites | `lead_form_start` on first focus; `generate_lead` only after a successful API response | `src/components/forms/LeadForm.astro` |

The branch is code-ready. Direct `gtag.js` does not require GTM for collection.
GA4 dashboard verification and the Key Event designation remain owner actions.
The live browser audit also exposed an existing Google Ads destination linked to
the Google tag. PR #86 prevents HSB custom events from being routed there; the
owner must separately review or unlink that destination in Google Tag settings.

---

## Production GA4 Event Plan

Only `lead_form_start` and `generate_lead` are wired by PR #86. Every other event
below remains a future plan and must not be reported as active. Events must be
measured without PII in event parameters.

### Core Conversion Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `generate_lead` | Form submitted successfully, server returns 200 | `method: "contact_form"` |
| `form_submit_success` (planned) | `/api/lead` returns success | `form_id: "lead_form"` |

### Form Funnel Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `lead_form_start` | User focuses any form field for the first time | none |
| `form_error` (planned) | Server returns error on submit OR client-side validation fails | `form_id: "lead_form"`, `error_type: "server_error"` or `"validation_error"` |

### Engagement Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `phone_click` | User clicks a `tel:` link | `phone_number`: omit PII — use placeholder `"contact"` |
| `email_click` | User clicks a `mailto:` link | `email_label: "info" | "outreach"` (never the actual address) |
| `pdf_download` | User clicks a PDF flyer link | `file_name: "HSB-Flyer-Joel-Cherino.pdf" | "HSB-Flyer-Jordi-Post.pdf" | "HSB-Flyer-Geschaeftsfuehrer.pdf"`, `link_text` |
| `scroll_depth` | User scrolls 25%, 50%, 75%, 90% of page | `percent_scrolled: 25 | 50 | 75 | 90` |
| `outbound_click` | User clicks any external link | `outbound_domain`, `link_text` |

### UTM and Campaign Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `qr_landing` | Page load where `utm_medium=qr` is present in URL | `utm_source`, `utm_campaign`, `utm_content` |
| `campaign_landing` | Page load with any UTM parameter | `utm_source`, `utm_medium`, `utm_campaign` |

GA4 automatically captures UTM parameters via `page_view` in sessions where the URL
contains `utm_*` parameters. Custom `qr_landing` event is supplementary for QR-specific reporting.
PR #86 intentionally does not copy the user-controlled `utm_campaign` value into
`generate_lead`; the conversion keeps GA4 session attribution without adding a
second URL-controlled custom parameter that could contain personal data.

---

## GTM (Google Tag Manager) — Optional Layer

GTM is not currently configured. GA4 fires directly via `gtag.js` snippet.

**Recommendation:** Add GTM only if multiple tags need management (e.g., GA4 + LinkedIn
Insight Tag + Hotjar simultaneously). For current scope, direct `gtag.js` is sufficient.

If GTM is added:
- Create GTM container in Google Tag Manager dashboard
- Add GTM snippet to `src/layouts/BaseLayout.astro` (replace or supplement gtag.js)
- Migrate GA4 config from hardcoded snippet to GTM → GA4 configuration tag
- All events below implemented as GTM custom HTML or trigger configurations
- GTM container ID must not be committed if it links to PII collection

---

## Implementation Notes for GA4 Events

### Recommended Implementation Pattern (Client-Side)

```typescript
import { trackEvent, trackEventAndWait, TrackingEvent } from "../../lib/tracking";

// First form interaction:
trackEvent(TrackingEvent.LeadFormStart);

// Only after /api/lead returned success; waits briefly before navigation:
await trackEventAndWait(TrackingEvent.LeadFormSubmit);
```

### PDF Download Tracking

PDF download tracking is not implemented. Before adding it, extend the validated
external parameter map in `src/lib/tracking.ts`, add tests, and emit through
`trackEvent`; do not add inline `gtag` calls that bypass the consent/privacy guard.

---

## Google Search Console (GSC)

### Current State

| Item | Status |
|------|--------|
| GSC property | URL-prefix property `https://www.hsb-boden.de/` is accessible in the interactive `Jordie (HEXAGON)` Chrome profile |
| Coverage snapshot | Same-day views showed 28–29 indexed and 5 not indexed; counts are time-dependent and require live recheck |
| API automation | Blocked: the available Google connector resolves to a different account than the interactive property access |
| `robots.txt` | Present — `src/pages/robots.txt.ts` |
| `sitemap.xml` | Present — `src/pages/sitemap.xml.ts` |
| Canonical URLs | Present — multilingual (de/en/fr/nl/pl/tr) + hreflang |

### GSC Owner Actions

1. Confirm which of the two visible Google properties is canonical for reporting.
2. Re-authenticate the automation connector with the same account that owns the
   `https://www.hsb-boden.de/` property.
3. Confirm the submitted sitemap and inspect the live reasons for the five
   non-indexed URLs before requesting validation.
4. Link the canonical GSC property to the intended GA4 property after both have
   been unambiguously identified.

### Sitemap Submission

No command needed — submit via GSC UI:
**GSC → Property → Sitemaps → Add sitemap URL**
Enter: `sitemap.xml` only if the live property does not already show that sitemap.

---

## Activation Gate

### GA4 Events Activation

- [ ] DNS/NS switch complete — `hsb-boden.de` live
- [ ] GA4 property `G-VC4BJBEFTV` exists and is accessible in GA4 dashboard
- [ ] Event implementation code merged and deployed
- [ ] Consent gate verified working (test incognito — GA4 must NOT fire before consent)
- [ ] `generate_lead` event visible in GA4 DebugView after test form submission
- [ ] Existing linked Google Ads destination reviewed/unlinked by the Google property owner
- [ ] Owner: after DebugView verification, mark `generate_lead` as a Key Event in the GA4 dashboard (this is not activated by the website code)
- [ ] Joel approval

### GSC Completion

- [x] URL-prefix property is interactively accessible
- [ ] Canonical property selected from the two visible properties
- [ ] Correct owner account connected for API/automation access
- [ ] Sitemap status and non-indexed reasons rechecked live
- [ ] Canonical GSC property linked to the intended GA4 property

---

## Forbidden

- No analytics events that capture PII (name, email, phone) in event parameters
- No GA4 events firing before DSGVO consent is granted by user
- No duplicate property creation or GA4/GSC linking before the owner identifies the canonical properties
- No GTM container linked to paid ad platforms without separate approval
