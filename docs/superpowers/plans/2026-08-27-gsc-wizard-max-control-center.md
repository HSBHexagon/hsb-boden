# HSB GSC Wizard Maximum Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn GSC Wizard into the authoritative production SEO/analytics control center for HSB Boden, with clean production-only monitoring, complete segmentation, indexing hygiene, GA4/GSC correlation, and explicit external gates for Bing/IndexNow/CrUX/GA4 Admin settings.

**Architecture:** Keep `https://www.hsb-boden.de/` as the sole production business truth, keep preview only as a contamination sentinel, and use GSC Wizard metadata/analysis features rather than creating redundant Search Console sub-properties. Apply reversible configuration first, then establish a reproducible analysis baseline, and finally verify external account-level dependencies that GSC Wizard cannot provision itself.

**Tech Stack:** GSC Wizard MCP, Google Search Console API, GA4 Data API (read-only through GSC Wizard), Bing Webmaster Tools integration, IndexNow, Chrome UX Report, GitHub for spec/plan provenance.

**Spec:** `docs/superpowers/specs/2026-08-27-gsc-wizard-max-control-center-design.md`

## Global Constraints

- Production property is exactly `https://www.hsb-boden.de/`.
- Preview property is exactly `https://hsb-boden-preview.cherinojoel.workers.dev/` and must never be included in production reporting.
- Production sitemap metadata must be exactly `https://www.hsb-boden.de/sitemap.xml`.
- The live sitemap has 43 canonical/indexable URLs.
- `/danke-projektanfrage/` must not be part of the index-success tracker.
- Page-level GSC totals are the traffic truth when query-level totals differ because of anonymized queries.
- `generate_lead` is the website lead-conversion event. `purchase` is not a website lead conversion.
- Do not create redundant folder-level GSC properties where content groups already provide the needed segmentation.
- Do not create SEO experiments until the property has enough traffic to make them statistically useful.
- Do not write opaque saved-filter payloads until the dashboard filter schema is known.
- Any unavailable CrUX, Bing production, IndexNow key, or GA4 Admin write capability must be reported as an explicit external gate rather than silently skipped.

---

### Task 1: Normalize production and preview property metadata

**Interfaces:**
- Consumes: current GSC Wizard site registry.
- Produces: clean production/preview metadata used by all later reports.

- [ ] Verify `https://www.hsb-boden.de/` exists and is readable.
- [ ] Verify `https://hsb-boden-preview.cherinojoel.workers.dev/` exists and is readable.
- [ ] Set production tags exactly to `HSB`, `HSB Boden`, `Production`, `B2B`, `Industrieboden`.
- [ ] Set production branded keywords to the exact list from the spec, excluding overly broad `hsb`.
- [ ] Set production sitemap URLs exactly to `https://www.hsb-boden.de/sitemap.xml`.
- [ ] Verify preview has `HSB Boden` and `Preview`, and does not carry `Production`.
- [ ] Re-read both properties and record the normalized state.

### Task 2: Clean the Indexing Tracker

**Interfaces:**
- Consumes: live 43-URL sitemap and current 44-URL tracker.
- Produces: a tracker containing only canonical URLs intended to be indexed.

- [ ] Confirm current tracker contains `/danke-projektanfrage/`.
- [ ] Remove `https://www.hsb-boden.de/danke-projektanfrage/` from the tracker.
- [ ] Re-read tracker stats; expected total is 43.
- [ ] Verify errors=0 and warnings=0.
- [ ] Keep historical URL-inspection records for the thank-you page; do not delete inspection history.
- [ ] Run a fresh explicit inspection of the thank-you page only if quota permits, to observe Google's current indexed snapshot after the `noindex` deployment.

### Task 3: Expand content-group segmentation

**Interfaces:**
- Consumes: existing groups `Leistungen`, `Branchen`, `Wissen`, `Standorte`.
- Produces: additional non-overlapping reporting cuts.

- [ ] Create `Core & Conversion` using exact-match rules for `https://www.hsb-boden.de/`, `/kontakt/`, `/projektablauf/`, `/referenzen/`.
- [ ] Create `International` for `/en/`, `/fr/`, `/nl/`, `/pl/`, `/tr/`.
- [ ] Create `Corporate & Legal` for `/karriere/` and `/impressum/`.
- [ ] Re-list content groups and verify all seven groups exist without duplicates.

### Task 4: Expand topic clusters from actual GSC demand

**Interfaces:**
- Consumes: existing six clusters and current visible-query data.
- Produces: fourteen focused clusters for dashboard aggregation.

- [ ] Create `WHG & AwSV` with the exact keyword set from the spec.
- [ ] Create `Molkerei & Milchsäure` with the exact keyword set from the spec.
- [ ] Create `Brauerei & Getränke` with the exact keyword set from the spec.
- [ ] Create `Keramik & Feinsteinzeug` with the exact keyword set from the spec.
- [ ] Create `PU-Beton & Beschichtung` with the exact keyword set from the spec.
- [ ] Create `HACCP, Hygiene & Rutschhemmung` with the exact keyword set from the spec.
- [ ] Create `Fugen, Hohlkehlen & Details` with the exact keyword set from the spec.
- [ ] Create `Region & Einsatzgebiet` with the exact keyword set from the spec.
- [ ] Re-list clusters and verify no duplicate names and no accidental loss of the existing six.

### Task 5: Add durable release and setup annotations

**Interfaces:**
- Consumes: production release commit `f392eda5081497388d2409d40ce405c43d46994f` and current chart annotations.
- Produces: causal markers for later ranking/traffic analysis.

- [ ] Create property annotation dated `2026-08-27`, label `Analytics/SEO Production Hardening f392eda`, category `analytics`, describing production GA4/Cloudflare host isolation, generate_lead contract protection, sitemap cleanup and thank-you noindex release.
- [ ] Create property annotation dated `2026-08-27`, label `GSC Wizard Control Center Finalized`, category `SEO`, describing tracker cleanup, segmentation expansion, analysis baseline, and external-gate inventory.
- [ ] Re-list annotations and verify both are present exactly once.

### Task 6: Establish the full Search Console analysis baseline

**Interfaces:**
- Consumes: normalized metadata, tracker, groups, clusters.
- Produces: a complete baseline for future optimization work.

- [ ] Generate the 28-day full SEO report with sitemap join.
- [ ] Run ranking changes by query.
- [ ] Run ranking changes by page.
- [ ] Run decaying-content analysis by query.
- [ ] Run decaying-content analysis by page.
- [ ] Run query decay matrix using monthly granularity where history permits.
- [ ] Run page decay matrix using monthly granularity where history permits.
- [ ] Run CTR curve against all supported benchmarks.
- [ ] Run page-poaching opportunities for positions 4-20 with at least 10 impressions.
- [ ] Run impression-weighted opportunity scoring.
- [ ] Run cannibalization analysis with at least 5 impressions so the current small-site signal is visible.
- [ ] Run path breakdown depth 1 and depth 2.
- [ ] Run query/page sampling-impact analysis and preserve the privacy/anonymization warning.
- [ ] Run 90-day anomaly scans for clicks, impressions, CTR, and position.
- [ ] Run 180-day change-point scans for clicks and impressions when history is sufficient.
- [ ] Run long-tail clustering with `small_site` preset and zero-click pages included.
- [ ] Run traffic forecasting only if the model accepts the available history; otherwise classify `PASS_NO_DATA/NOT_YET_USEFUL`.
- [ ] Query web, image, video, news, Discover, and Google News where supported; classify empty channels as `PASS_NO_DATA`, not failures.

### Task 7: Establish the complete GA4/GSC measurement baseline

**Interfaces:**
- Consumes: linked GA4 property `543244027` and production GSC property.
- Produces: measurement-quality baseline and explicit GA4 Admin gate list.

- [ ] Verify GA4 property `properties/543244027` is still linked to production.
- [ ] Run GA4 overview with timeseries.
- [ ] Run GA4 event breakdown.
- [ ] Run GA4 page and landing-page breakdowns.
- [ ] Run GA4 channel and source/medium breakdowns.
- [ ] Run GA4 country and device breakdowns.
- [ ] Run GA4 key-event report and record all available key-event names.
- [ ] Confirm whether `generate_lead` is present as a key event.
- [ ] Confirm `purchase`, `qualify_lead`, and `close_convert_lead` are not falsely interpreted as website-form conversions.
- [ ] Run blended GSC+GA4 landing pages with `organicOnly=true`.
- [ ] Run GA4 LLM referral report with daily split.
- [ ] Run GA4 ecommerce as a negative control; expected `hasEcommerce=false` unless a real ecommerce flow has been introduced.
- [ ] If `generate_lead` is not a key event, classify `GA4_KEY_EVENT_ADMIN=EXTERNAL_GATE` because the current connector is read-only for Analytics Admin.

### Task 8: Verify production/preview analytics isolation evidence

**Interfaces:**
- Consumes: current deployed website code/release facts plus GA4/GSC observations.
- Produces: contamination-risk status.

- [ ] Verify production GSC reporting references only `https://www.hsb-boden.de/`.
- [ ] Verify preview remains separately tagged and excluded from production tag aggregation.
- [ ] Review GA4 page paths for legacy `/client/*` pollution and record whether new post-hardening traffic is on canonical production paths.
- [ ] Treat legacy polluted rows as historical data, not current production health.
- [ ] Record `PRODUCTION_PREVIEW_ISOLATION=PASS` only if current metadata and current event/page evidence are consistent.

### Task 9: Audit Core Web Vitals / CrUX readiness

**Interfaces:**
- Consumes: GSC Wizard CrUX configuration state.
- Produces: either field-data baseline or explicit external gate.

- [ ] Call origin-level Core Web Vitals for ALL devices.
- [ ] If configured, also query PHONE and DESKTOP.
- [ ] If not configured, record the exact requirement: Google Cloud API key with `Chrome UX Report API` enabled.
- [ ] Classify missing key as `CRUX_API_KEY=EXTERNAL_GATE`, not an SEO failure.
- [ ] Do not claim field-data performance from Lighthouse alone; Lighthouse remains lab data.

### Task 10: Audit Bing Webmaster and IndexNow readiness

**Interfaces:**
- Consumes: connected Bing Webmaster account and GSC Wizard IndexNow tools.
- Produces: production search-engine coverage state.

- [ ] List Bing sites.
- [ ] Verify whether `https://www.hsb-boden.de/` is present.
- [ ] If present, run Bing traffic, queries, pages, crawl stats, crawl issues, feeds, backlinks and URL-submission quota.
- [ ] If absent, classify `BING_PRODUCTION_PROPERTY=EXTERNAL_GATE` and note that Bing supports importing a verified GSC site.
- [ ] Check production IndexNow submission history.
- [ ] If no IndexNow key is configured, classify `INDEXNOW_KEY=EXTERNAL_GATE`.
- [ ] Do not bulk-submit unchanged URLs merely to populate history.
- [ ] Once a key exists, submit only URLs that were genuinely added/updated/deleted, with the recent SEO hardening pages eligible as an initial one-time changed set.

### Task 11: Validate non-production features and avoid misleading enablement

**Interfaces:**
- Consumes: experiment list, saved-filter list, historical traffic volume.
- Produces: explicit `NOT_YET_USEFUL` decisions.

- [ ] Verify SEO experiments count.
- [ ] Keep experiments disabled while the property lacks enough recurring clicks for statistically useful control/variant comparisons.
- [ ] Verify saved filters count.
- [ ] Do not create saved filters until the opaque dashboard filter schema is known.
- [ ] Record both decisions in the final setup report so they are not mistaken for omissions.

### Task 12: Final verification and closure

**Interfaces:**
- Consumes: outputs from Tasks 1-11.
- Produces: final PASS/EXTERNAL_GATE matrix.

- [ ] Re-run `get_site_summary` for the production property.
- [ ] Re-run `list_sitemaps` and `get_sitemap_performance`.
- [ ] Re-run `get_indexing_tracker` and require total=43, errors=0, warnings=0.
- [ ] Re-list content groups and topic clusters.
- [ ] Re-list annotations.
- [ ] Re-check GA4 overview, event report and key events.
- [ ] Re-check CrUX readiness.
- [ ] Re-check Bing/IndexNow readiness.
- [ ] Produce final statuses for `GSC_SETUP`, `INDEXING_TRACKER`, `SEGMENTATION`, `ANALYSIS_BASELINE`, `GA4_READ_INTEGRATION`, `GA4_KEY_EVENT_ADMIN`, `CRUX`, `BING_PRODUCTION`, `INDEXNOW`, `PREVIEW_ISOLATION`.
- [ ] Set overall `FINAL=PASS` only if all executable GSC Wizard work is complete and every non-executable dependency is explicitly identified as an external gate with no hidden blocker.
