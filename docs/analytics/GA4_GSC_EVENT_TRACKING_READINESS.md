# GA4_GSC_EVENT_TRACKING_READINESS — HSB-Boden / HEXAFLOOR

Status: `ga4-code-present-events-planned-gsc-pending-domain-verification`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No analytics activation, no property creation, no GSC verification performed here.**
This document defines the production event tracking plan for GA4 and GSC.
GA4 code is already present in the build. Events fire after user consent.

Canonical analytics truth: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`

---

## GA4 Code State

| Item | Status | Location |
|------|--------|----------|
| GA4 Measurement ID | `G-VC4BJBEFTV` — present in code | `src/layouts/BaseLayout.astro:31–36` |
| gtag.js snippet | Present and deployed | `src/layouts/BaseLayout.astro:30–37` |
| Consent gate (DSGVO) | Active — CookieConsent component | `src/components/layout/CookieConsent.astro` |
| GA4 fires only after consent | Enforced in code | — |

GA4 is code-ready. Events below fire in production once custom measurement is configured
in the GA4 property and/or GTM container (if GTM is added).

---

## Production GA4 Event Plan

All events below follow GA4 recommended event naming conventions.
Events must be measured without PII in event parameters.

### Core Conversion Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `generate_lead` | Form submitted successfully, server returns 200 | `method: "contact_form"`, `campaign` (from UTM if present) |
| `form_submit_success` | `/api/lead` returns success | `form_id: "lead_form"` |

### Form Funnel Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `form_start` | User focuses any form field for the first time | `form_id: "lead_form"` |
| `form_error` | Server returns error on submit OR client-side validation fails | `form_id: "lead_form"`, `error_type: "server_error" | "validation_error"` |

### Engagement Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `phone_click` | User clicks a `tel:` link | `phone_number`: omit PII — use placeholder `"contact"` |
| `email_click` | User clicks a `mailto:` link | `email_label: "info" | "outreach"` (never the actual address) |
| `pdf_download` | User clicks a PDF flyer link | `file_name: "HSB-Flyer-Joel-Cherino.pdf" | "HSB-Flyer-Jordie-Post.pdf" | "HSB-Flyer-Geschaeftsfuehrer.pdf"`, `link_text` |
| `scroll_depth` | User scrolls 25%, 50%, 75%, 90% of page | `percent_scrolled: 25 | 50 | 75 | 90` |
| `outbound_click` | User clicks any external link | `outbound_domain`, `link_text` |

### UTM and Campaign Events

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `qr_landing` | Page load where `utm_medium=qr` is present in URL | `utm_source`, `utm_campaign`, `utm_content` |
| `campaign_landing` | Page load with any UTM parameter | `utm_source`, `utm_medium`, `utm_campaign` |

GA4 automatically captures UTM parameters via `page_view` in sessions where the URL
contains `utm_*` parameters. Custom `qr_landing` event is supplementary for QR-specific reporting.

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
// In form submit handler (src/pages/index.astro or form component)
// After successful API response:
if (typeof gtag !== 'undefined') {
  gtag('event', 'generate_lead', {
    method: 'contact_form',
  });
  gtag('event', 'form_submit_success', {
    form_id: 'lead_form',
  });
}

// On first field focus (form_start):
formElement.addEventListener('focusin', (e) => {
  if (!formStarted) {
    formStarted = true;
    gtag('event', 'form_start', { form_id: 'lead_form' });
  }
}, { once: false });

// On form error:
gtag('event', 'form_error', {
  form_id: 'lead_form',
  error_type: 'server_error',
});
```

### PDF Download Tracking

```html
<!-- In PDF link markup -->
<a href="/HSB-Flyer-Joel-Cherino.pdf"
   onclick="gtag('event', 'pdf_download', {
     file_name: 'HSB-Flyer-Joel-Cherino.pdf',
     link_text: 'Flyer herunterladen'
   })">
  Flyer herunterladen
</a>
```

---

## Google Search Console (GSC)

### Current State

| Item | Status |
|------|--------|
| GSC property | Not yet verified — `hsb-boden.de` DNS pending |
| `robots.txt` | Present — `src/pages/robots.txt.ts` |
| `sitemap.xml` | Present — `src/pages/sitemap.xml.ts` |
| Canonical URLs | Present — multilingual (de/en/fr/nl/pl/tr) + hreflang |

### GSC Verification (After DNS/NS Switch)

1. Log into Google Search Console with `cherinojoel@gmail.com`
2. Add property: `hsb-boden.de` (domain property preferred)
3. Verify via DNS TXT record:
   - Value provided by GSC (e.g., `google-site-verification=XXXXXXXX`)
   - Add to Cloudflare DNS as TXT on apex — DNS-only
4. Submit sitemap: `https://hsb-boden.de/sitemap.xml`
5. Monitor Index Coverage after 1–2 weeks

### Sitemap Submission Commands (After Verification)

No command needed — submit via GSC UI:
**GSC → Property → Sitemaps → Add sitemap URL**
Enter: `sitemap.xml`

---

## Activation Gate

### GA4 Events Activation

- [ ] DNS/NS switch complete — `hsb-boden.de` live
- [ ] GA4 property `G-VC4BJBEFTV` exists and is accessible in GA4 dashboard
- [ ] Event implementation code merged and deployed
- [ ] Consent gate verified working (test incognito — GA4 must NOT fire before consent)
- [ ] `generate_lead` event visible in GA4 DebugView after test form submission
- [ ] Joel approval

### GSC Activation

- [ ] DNS/NS switch complete — zone `Active`
- [ ] GSC TXT verification record added to Cloudflare DNS
- [ ] Sitemap submitted
- [ ] Initial crawl requested

---

## Forbidden

- No analytics events that capture PII (name, email, phone) in event parameters
- No GA4 events firing before DSGVO consent is granted by user
- No GSC verification before DNS/NS switch
- No GTM container linked to paid ad platforms without separate approval
