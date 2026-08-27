# HSB GSC Wizard Maximum Control Center Design

**Date:** 2026-08-27  
**Status:** Awaiting written-spec approval  
**Repository:** `HSBHexagon/hsb-boden`  
**Primary production property:** `https://www.hsb-boden.de/`  
**Production GA4 property:** `properties/543244027` (`HSBBODENCLOUDFLAIRE`)  
**GA4 measurement ID:** `G-VC4BJBEFTV`

## 1. Goal

Turn GSC Wizard into the authoritative, production-focused SEO/analytics control center for HSB Boden, using every currently useful capability without creating duplicate properties, noisy monitoring, misleading metrics, or unnecessary operational complexity.

The final setup must cover:

- Google Search Console production monitoring
- sitemap/indexing health
- production-vs-preview separation
- GA4 integration and data-quality checks
- search-to-behavior landing-page analysis
- topic-cluster and content-group segmentation
- query opportunity, CTR, ranking, cannibalization, decay, anomaly, change-point and forecasting analyses
- deployment/algorithm annotations
- Bing Webmaster / IndexNow readiness
- Core Web Vitals / CrUX readiness
- LLM referral monitoring
- a documented external-gate list for settings that GSC Wizard cannot write

The objective is not to switch on every feature blindly. Features that would produce misleading or statistically underpowered output must be explicitly classified as `NOT_YET_USEFUL` rather than enabled for appearance's sake.

## 2. Current verified state

### 2.1 Account and scopes

GSC Wizard is authenticated through `info@hsb-boden.de` with Google Search Console write access and Google Analytics read-only access. The GSC Wizard API surface itself exposes write-capable property metadata/configuration operations.

Current Google scopes include:

- `webmasters`
- `analytics.readonly`

Therefore:

- Search Console/GSC Wizard metadata operations are executable through the connector.
- GA4 reporting is executable.
- GA4 Admin writes such as creating/removing key events are not executable through the current GSC Wizard connector.

### 2.2 Properties

Registered in GSC Wizard:

1. `https://www.hsb-boden.de/` — production
2. `https://hsb-boden-preview.cherinojoel.workers.dev/` — preview sentinel

The preview property remains useful only as an accidental-indexation/preview sentinel and must never be aggregated into production reporting.

Production tags currently include:

- `HSB`
- `HSB Boden`
- `Production`
- `B2B`
- `Industrieboden`

Preview is tagged separately with `Preview`.

### 2.3 Current GSC performance

Latest 28-day production baseline:

- Clicks: 52
- Impressions: 4,705
- CTR: ~1.11%
- Average position: ~34.3

### 2.4 Query-data privacy limitation

GSC totals show 52 clicks, but the query-level dataset exposes only a small fraction of those clicks. GSC Wizard's sampling-impact analysis reports:

- query missing-click share: 94.23%
- query missing-impression share: 26.04%
- page missing-click share: 0%
- page missing-impression share: 0%

This is consistent with Google's anonymized-query behavior. Therefore:

- page-level click/impression data is the primary traffic truth for this property;
- query-level work is valid for visible-query opportunity discovery, impressions and position analysis;
- query-level summed clicks must never be treated as the property's total organic clicks;
- cluster/opportunity prioritization must explicitly account for this privacy gap.

### 2.5 Sitemap and indexing

The live sitemap currently contains 43 canonical/indexable URLs.

GSC Wizard sitemap-performance analysis sees:

- 43 URLs in the live sitemap
- 43/43 with GSC performance visibility

The Search Console sitemap-status endpoint still reports the previously submitted 44-URL snapshot because Google last downloaded it before the latest deployment. This is a normal refresh lag, not evidence that the live sitemap still contains 44 URLs.

The Indexing Tracker currently contains 44 URLs and is therefore stale by one URL: `/danke-projektanfrage/` remains tracked even though it is now intentionally `noindex` and excluded from the sitemap.

### 2.6 Thank-you page

Production live state:

- `/danke-projektanfrage/` returns HTTP 200
- has `noindex`
- is non-indexable by design
- is absent from the live sitemap

Google's indexed snapshot still reflects the older version because its latest stored crawl predates the deployment. The page must be removed from the "must be indexed" tracker and monitored only through explicit inspection history until Google recrawls it.

### 2.7 Existing content groups

Existing groups:

- Leistungen
- Branchen
- Wissen
- Standorte

### 2.8 Existing topic clusters

Existing clusters:

- Industrieboden Kern
- Säureschutz & Chemie
- Lebensmittel & Hygiene
- Entwässerung & Gefälle
- Sanierung & Reparatur
- ESD & Ableitfähigkeit

### 2.9 GA4

GSC Wizard is linked to:

- property `properties/543244027`
- display name `HSBBODENCLOUDFLAIRE`
- linked production site `https://www.hsb-boden.de/`

Fresh production data has now arrived for `/`, proving the basic production transport is active.

Current website code sends successful lead submissions as the recommended GA4 event `generate_lead` and restricts production GA4 loading to hostname `www.hsb-boden.de`.

Current GA4 key-event list visible through GSC Wizard is still:

- `close_convert_lead`
- `purchase`
- `qualify_lead`

`generate_lead` is not yet visible as a key event. This remains a GA4 Admin gate unless the connected Analytics permissions/tooling are expanded.

### 2.10 Cloudflare production analytics

Website code also restricts Cloudflare Web Analytics loading to the canonical production hostname. Preview should therefore not pollute production RUM via application code.

The merged production release is deployed through Cloudflare Pages from commit `f392eda5081497388d2409d40ce405c43d46994f`.

### 2.11 CrUX / Core Web Vitals

GSC Wizard currently returns `notConfigured` for CrUX because no Chrome UX Report API key is configured.

A Google Cloud API key with the Chrome UX Report API enabled is required before GSC Wizard can monitor origin/page-level LCP, INP, CLS, FCP and TTFB field data.

### 2.12 Bing / IndexNow

The connected Bing Webmaster account currently exposes only the preview Workers property, not production `www.hsb-boden.de`.

Production Bing queries currently fail authorization because production is not registered/verified in that Bing account.

IndexNow history for production is empty.

Production Bing verification and IndexNow key provisioning are external account/setup gates because the current GSC Wizard connector has read/query and IndexNow submission tools but no production-site provisioning or IndexNow-key creation operation.

### 2.13 Experiments and saved filters

- SEO experiments: none
- saved filters: none

No experiment should be created merely to populate the feature. With only 52 GSC clicks in the current 28-day window, most split tests would be statistically underpowered. Experiments become eligible only when control/variant groups have enough recurring clicks/impressions to produce meaningful confidence intervals.

Saved-filter creation must not be attempted through the MCP until the dashboard filter schema is explicitly known; the tool documents the payload as opaque.

## 3. Design principles

### 3.1 Production is the sole business truth

`https://www.hsb-boden.de/` is the canonical production property for business reporting.

Preview data may be monitored only to detect accidental indexation or contamination. It must not share production tags such as `Production`, and must not be used in production aggregates.

### 3.2 Avoid unnecessary GSC property proliferation

Do not create URL-prefix properties for `/wissen/`, `/leistungen/`, `/branchen/`, etc. unless a future requirement cannot be met by content groups or regex filters.

Content groups already provide the section segmentation needed without duplicating Search Console data and management overhead.

A domain property `sc-domain:hsb-boden.de` may be registered in GSC Wizard only if it already exists and is verified in the connected Search Console account. If it does not exist, DNS verification is an optional account hardening task, not a blocker for the current canonical `www` URL-prefix property.

### 3.3 Index only intended search pages

The production sitemap and Indexing Tracker must describe canonical URLs intended to appear in search results.

`/danke-projektanfrage/` must remain outside both.

Legal/corporate pages may remain discoverable/indexable through internal links even when not intentionally promoted through the sitemap; no indexation change is made without a separate SEO decision.

### 3.4 Use recommended GA4 lead semantics

Website lead submission is `generate_lead`.

`purchase` is not a website lead conversion for HSB and must not be treated as one unless an actual ecommerce/payment flow is introduced.

`qualify_lead` and `close_convert_lead` are valid later-stage B2B lead-lifecycle events only if they are intentionally populated from CRM/offline workflows. They should not substitute for the website's initial `generate_lead` event.

### 3.5 Data-quality-first reporting

When GSC totals and query rows differ because of anonymization:

- total/page data wins for traffic volume;
- visible query rows are used for opportunity/ranking diagnostics only;
- no false reconciliation is attempted by summing visible queries.

## 4. Target GSC Wizard property configuration

### 4.1 Production tags

Production tag set remains exactly:

- HSB
- HSB Boden
- Production
- B2B
- Industrieboden

No `Preview` tag may exist on production.

### 4.2 Preview tags

Preview remains:

- HSB Boden
- Preview

No `Production` tag may exist on preview.

### 4.3 Production sitemap metadata

GSC Wizard production sitemap URL list must be exactly:

- `https://www.hsb-boden.de/sitemap.xml`

### 4.4 Branded keyword set

The production branded-keyword list must include the meaningful variants below and exclude overly broad `hsb` by itself:

- hsb boden
- hsb-boden
- hsb hexagon
- hsb hexagon säurebau
- hsb hexagon saeurebau
- hsb hexagon säurebau gmbh
- hsb hexagon saeurebau gmbh
- hexagon säurebau
- hexagon saeurebau
- hexagon säurebau gmbh
- hexagon saeurebau gmbh
- hexafloor
- hsb hexafloor
- hsb säurebau
- hsb saeurebau

## 5. Target content groups

Keep the existing four groups and add only groups that create genuinely new reporting cuts.

### 5.1 Core & Conversion

Exact-match pages:

- `/`
- `/kontakt/`
- `/projektablauf/`
- `/referenzen/`

Purpose: business-entry and conversion-intent pages.

### 5.2 International

Paths:

- `/en/`
- `/fr/`
- `/nl/`
- `/pl/`
- `/tr/`

Purpose: isolate multilingual search visibility from German-language core performance.

### 5.3 Corporate & Legal

Exact pages:

- `/karriere/`
- `/impressum/`

Purpose: keep brand/corporate traffic from distorting service/content evaluation.

`/danke-projektanfrage/` is intentionally excluded from performance groups.

## 6. Target topic-cluster expansion

Keep the existing six clusters and add focused clusters derived from actual GSC visibility.

### 6.1 WHG & AwSV

Keywords should cover:

- whg abdichtung
- whg bodenbeschichtung
- bodenbeschichtung nach whg
- whg fugen
- whg fugenabdichtung
- fugen nach whg
- awsv boden
- awsv abdichtung
- flüssigkeitsdichte fläche
- auffangfläche whg

### 6.2 Molkerei & Milchsäure

- boden molkerei
- molkerei boden
- böden beständig gegen milchsäure
- milchsäurebeständiger boden
- bodenbeläge für milchverarbeitung
- bodenbeläge für milchsäurebakterienproduktionsbereiche
- industrieboden molkerei

### 6.3 Brauerei & Getränke

- brauerei boden
- industrieboden brauerei
- getränkeindustrie boden
- säurebeständiger feinsteinzeugboden für brauerei
- bodenbeläge für alkoholische getränkeproduktionsbereiche

### 6.4 Keramik & Feinsteinzeug

- keramischer industrieboden
- keramische industrieböden
- industriefliesen
- feinsteinzeug industrieboden
- säurefeste fliesen
- säurebeständige fliesen
- hochbelastbare industriefliesen

### 6.5 PU-Beton & Beschichtung

- pu beton industrieboden
- pu-beton industrieboden
- pu beton boden
- epoxidharz bodenbeschichtung
- epoxidharz industrieboden
- bodenbeschichtung industrie

### 6.6 HACCP, Hygiene & Rutschhemmung

- haccp konformer boden
- haccp industrieboden
- hygienischer industrieboden
- rutschhemmung industrieboden
- r9 industrieboden
- r10 industrieboden
- r11 industrieboden
- r12 industrieboden
- r13 industrieboden

### 6.7 Fugen, Hohlkehlen & Details

- fugensanierung industrieboden
- dehnungsfugen industrieboden
- whg fugen
- hohlkehle industrieboden
- hohlkehle sockelbereich
- sockelausbildung industrieboden
- rammschutz industrie

### 6.8 Region & Einsatzgebiet

- industrieboden nrw
- industrieboden bayern
- industrieboden hamburg
- industrieboden baden-württemberg
- industrieboden rheinland-pfalz
- industrieboden deutschland
- industrieboden europa

## 7. Indexing Tracker target state

Target after cleanup:

- total tracked: 43 canonical sitemap URLs
- `/danke-projektanfrage/`: removed
- errors: 0
- warnings: 0
- pending: 0 after next scheduled/explicit checks

The thank-you URL remains in inspection history but is not part of the success score for indexable production content.

After Google recrawls it, expected URL Inspection state is non-indexed due to `noindex`. The exact wording may vary and is not a deployment blocker once the live page is verified non-indexable.

## 8. Required analysis baseline after setup

Run and record, without changing site content automatically:

1. full 28-day SEO report
2. 90-day anomaly scan for clicks, impressions and position
3. 180-day change-point scan where enough history exists
4. ranking changes by query and page
5. decaying content by query and page
6. monthly/weekly decay matrix where enough history exists
7. CTR curve against all supported benchmarks
8. page-poaching opportunities
9. opportunity scoring
10. cannibalization analysis
11. path breakdown
12. sampling/anonymization impact
13. sitemap performance
14. indexing tracker report
15. GA4 overview
16. GA4 event breakdown
17. GA4 key-event report
18. GA4 + GSC blended landing pages
19. GA4 LLM referral traffic
20. ecommerce report only as a negative-control check; expected `hasEcommerce=false`
21. forecast only if the available history satisfies the model's minimum requirements
22. long-tail clustering using the `small_site` preset, interpreted cautiously because query/page data coverage may differ

The output of these analyses becomes the post-configuration baseline, not an automatic instruction to rewrite pages.

## 9. Monitoring annotations

Create a property-scoped annotation for the production release:

- Date: 2026-08-27
- Label: `Analytics/SEO Production Hardening f392eda`
- Category: `analytics`
- Description: production GA4/Cloudflare host isolation, `generate_lead` contract protection, sitemap cleanup and thank-you noindex release.

Create a second annotation when this GSC Wizard maximal-control-center setup is completed:

- Date: 2026-08-27
- Label: `GSC Wizard Control Center Finalized`
- Category: `SEO`
- Description: property metadata, tracker cleanup, content groups, topic clusters and monitoring baseline finalized.

Do not delete official Google algorithm-update annotations.

## 10. GA4 final target

### 10.1 Required

- property remains `properties/543244027`
- production site remains `https://www.hsb-boden.de/`
- basic production page/session collection continues
- preview does not send production analytics
- `generate_lead` is the website lead key event

### 10.2 Later-stage B2B events

`qualify_lead` and `close_convert_lead` may remain only if a real CRM/offline lifecycle integration intentionally emits them.

If there is currently no such pipeline, they are not evidence of functioning website conversions and must be documented as dormant lifecycle events.

### 10.3 Ecommerce

`purchase` should not be a primary HSB website key event because the public website is not an ecommerce checkout. If no separate ecommerce flow exists, it should be removed from the key-event set in GA4 Admin.

### 10.4 External GA4 Admin gate

GSC Wizard cannot perform the required Analytics Admin write with the current `analytics.readonly` scope.

Required owner/admin action or expanded tooling:

- mark `generate_lead` as a key event
- remove `purchase` as a key event unless justified
- retain/remove `qualify_lead` and `close_convert_lead` according to real CRM lifecycle usage
- verify the official GA4 Search Console product link points to the correct production web stream and production Search Console property

Closure may be `FINAL=DEGRADED_EXTERNAL_GATE` until these settings are verified.

## 11. CrUX target

Configure a Google Cloud API key with Chrome UX Report API enabled in GSC Wizard.

After configuration, collect:

- origin ALL
- PHONE
- DESKTOP
- individual high-value URLs when page-level data exists

Metrics:

- LCP
- INP
- CLS
- FCP
- TTFB

If CrUX returns `noData` because HSB lacks sufficient real-user Chrome volume, that is an acceptable `PASS_NO_FIELD_DATA`, not a failure.

## 12. Bing / IndexNow target

### 12.1 Bing Webmaster

Production `https://www.hsb-boden.de/` must be added/verified in the connected Bing Webmaster account. Preferred setup is import from the already verified Google Search Console property where available.

Preview may remain in Bing only as a test property, but it must not be mistaken for production.

### 12.2 Sitemap

Submit/monitor:

- `https://www.hsb-boden.de/sitemap.xml`

### 12.3 IndexNow

Provision a production IndexNow key and ensure the public key file is reachable on `www.hsb-boden.de`.

After configuration, use IndexNow only for newly added, materially updated, or deleted URLs. Do not repeatedly submit unchanged URLs.

Record submission responses in GSC Wizard.

These steps remain external gates until production Bing ownership and IndexNow key configuration exist.

## 13. SEO experiments

Do not create an experiment during this setup solely to use the feature.

Eligibility rule for a future experiment:

- clear control/variant URL groups
- a specific title/content/internal-link hypothesis
- enough recurring impressions/clicks to avoid obviously low power
- pre-recorded start annotation

Current state is `NOT_YET_USEFUL_LOW_TRAFFIC`, not missing configuration.

## 14. Saved filters

Do not write opaque saved-filter payloads without a confirmed dashboard schema.

If schema documentation becomes available, recommended presets are:

- Production German core
- Non-brand opportunities
- Positions 4-20
- High-impression zero-click queries
- International pages
- WHG cluster
- Molkerei/Milchsäure cluster

Until then, these are dashboard/UI presets, not an MCP write requirement.

## 15. Search-type coverage

As part of the baseline, probe whether the production property has meaningful data for:

- web
- image
- video
- news
- discover

Do not create separate properties because a search type has no data.

`NO_DATA` for unsupported content types is acceptable.

## 16. Data integrity and contradiction handling

If two GSC Wizard tools disagree:

1. compare date ranges and search types;
2. compare `dataSource` values;
3. prefer direct Search Console totals/page rows for current traffic volume;
4. account for query anonymization before calling the data inconsistent;
5. record true unresolved contradictions instead of averaging them away.

No `FINAL=PASS` may be declared while a material contradiction remains unexplained.

## 17. What will not be done

- No unnecessary new folder-level GSC properties.
- No automatic content rewrites based only on one 28-day window.
- No indexing request spam for all 43 pages.
- No repeated IndexNow submission of unchanged URLs.
- No fake experiment with insufficient traffic.
- No treatment of query-row click sums as total Search traffic.
- No GA4 ecommerce assumptions.
- No Preview data mixed into Production.
- No destructive deletion of official algorithm annotations or historical inspection evidence.

## 18. Implementation workstreams

### Workstream A — GSC Wizard production configuration

- normalize production property metadata
- normalize sitemap metadata
- write branded keyword set
- add content groups
- add topic clusters
- create release/setup annotations
- remove thank-you URL from tracker
- confirm resulting tracker count

### Workstream B — GSC/SEO analytics baseline

- run complete analysis suite listed in section 8
- explicitly capture privacy/sampling limitations
- identify only evidence-backed opportunity priorities

### Workstream C — GA4 closure

- verify current production collection
- verify `generate_lead` code contract
- verify linked property
- identify remaining Admin changes
- complete them only through an authorized Analytics Admin write surface

### Workstream D — CrUX/Core Web Vitals

- configure CrUX API key externally
- validate origin/device reports
- classify `PASS`, `PASS_NO_FIELD_DATA`, or `EXTERNAL_GATE`

### Workstream E — Bing/IndexNow

- verify/add production Bing site externally
- submit/monitor sitemap
- configure IndexNow key
- submit only release-changed URLs when appropriate

### Workstream F — final consistency audit

- rerun property, sitemap, tracker, GA4, group/cluster and external-gate checks
- compare against this spec
- report every remaining external gate explicitly

## 19. Final acceptance criteria

### GSC Wizard core = PASS only if

- production property metadata is normalized
- sitemap metadata points only to production sitemap
- production and preview tags are isolated
- branded keyword set is complete and non-ambiguous
- required content groups exist
- required topic clusters exist
- Indexing Tracker has exactly 43 canonical intended-index URLs
- tracker has no active errors/warnings
- thank-you page is absent from the tracker
- live thank-you page remains noindex and absent from sitemap
- full analysis baseline has been executed
- query anonymization is documented in the interpretation rules

### GA4 = PASS only if

- production collection works
- preview isolation remains enforced
- `generate_lead` is a key event
- unrelated `purchase` is removed unless justified
- later-stage lifecycle key events are either justified or removed
- official GA4/Search Console production link is verified

### CrUX = PASS only if

- API key is configured and data can be queried, or
- API is configured but HSB legitimately returns no field data (`PASS_NO_FIELD_DATA`)

### Bing/IndexNow = PASS only if

- production Bing property is verified
- production sitemap is known to Bing
- IndexNow ownership/key is configured
- a valid changed-URL submission can be recorded

### Overall closure

`FINAL=PASS` requires all executable work and all required external-account gates to be complete.

If GSC Wizard core is complete but one or more non-writable external account gates remain, report:

`FINAL=DEGRADED_EXTERNAL_GATES`

with an exact gate list. Never claim full closure based only on code or GSC Wizard metadata.
