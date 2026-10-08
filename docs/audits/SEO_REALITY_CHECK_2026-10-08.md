# SEO Reality Check — HSB-Boden — 2026-10-08

## Scope and safety
Evidence-based SEO audit, not a production deployment. Current code source of truth: `HSBHexagon/hsb-boden`, website in `apps/website/`; production served from Cloudflare Pages under `www.hsb-boden.de`. Do not touch Sales OS, CRM, email dispatch, DNS, secrets or production deployment.

## Verified externally (2026-10-08)
- `https://www.hsb-boden.de/` returned HTTP 200. Existing title: `Ingenieurbau, Rüttelkeramik & Säureschutz | HSB Hexagon`. Existing description refers to industrial floors, Rüttelkeramik, WHG, food/pharma/chemicals.
- `https://www.hsb-boden.de/robots.txt` returned 200 and contains `User-agent: *`, `Allow: /`, `Sitemap: https://www.hsb-boden.de/sitemap.xml`.
- `https://www.hsb-boden.de/sitemap.xml` returned 200; includes separate service and industry URLs (Molkerei, Brauerei, Chemie, Lebensmittel, WHG, PU-Beton, keramische Industrieböden, Bodensanierung). Do not duplicate existing pages.
- `https://www.hsb-boden.de/sitemap-index.xml` returns 404: **not a defect**, as robots.txt points to `/sitemap.xml`.
- Source `apps/website/astro.config.mjs` uses `site: "https://www.hsb-boden.de"` and static output; `apps/website/src/layouts/BaseLayout.astro` already uses `SEOHead`, an optional `jsonLd` prop, GA consent gating, and Cloudflare Analytics loader.
- Existing `apps/website/package.json` offers `npm run check`, `npm run test:run`, `npm run build`, and `npm run check:sitemap`.

## Original recommendation adjudication
- “Too few indexed pages”: **not established** without GSC URL indexing dataset.
- “Too few industry/service landing pages”: **false in general**; they exist. Audit content overlap/intent before creating new URLs.
- “Generic homepage title”: **false** (see live title above).
- “Structured data missing”: **unverified**; inspect actual rendered scripts and `SEOHead` before adding markup.
- “FAQPage drives rich results”: **obsolete**. Google removed FAQ rich-result functionality in May/June 2026.
- “600–1,200 words per landing page”: **not a Google rule**. Optimize for audience usefulness and search intent, not fixed word counts.
- “No off-page links”: **unverified**; compare GSC Links / independent backlink index.
- “Core Web Vitals poor”: **unverified**; read CrUX field data at p75, then targeted Lighthouse lab data.

## Execution backlog (evidence before change)
1. **P0 Measurement**: obtain GSC Web Search performance (last 3/6/12 months by query/page/device) and Pages indexing export; distinguish no impressions vs low CTR vs non-indexing. Cross-check GA4 acquisition and consent rates. No fabricated traffic diagnosis.
2. **P0 Crawl audit**: derive canonical indexable URLs from sitemap and routes; for each check HTTP status, rendered title/description/H1, canonical, robots meta, JSON-LD, hreflang reciprocal references, inbound internal links; record errors. Do not assume one H1 or fixed title pixel count is a hard Google ranking rule.
3. **P0 Conversion measurement**: verify consent-aware `generate_lead` event only after successful form submission and verify CRM receipt independently; no live lead injection without owner clearance.
4. **P1 On-page optimization**: map each existing industry/service URL to one primary buyer intent, add real implementation evidence and sector-specific process constraints; avoid reworded near-duplicate SEO pages. Review names, customer logos, WHG/AGI statements against documented proof before publishing.
5. **P1 Schema**: verify Organization/LocalBusiness/WebSite/Service and BreadcrumbList graph by page. Only add truthful visible facts and use Google-supported rich-result types when appropriate. Avoid FAQ rich-result promises and false certificates.
6. **P1 Technical**: verify Core Web Vitals at 75th percentile on mobile, optimize only identified regressions; verify `www`/apex redirect and language canonicals/hreflang; no DNS changes within this work.
7. **P2 Off-page**: benchmark topical competitors and source verified references, partner mentions and useful industry citations. No target backlink quota or paid link schemes.

## Sources (primary)
- https://developers.google.com/search/docs/appearance/title-link
- https://developers.google.com/search/updates (FAQ rich results deprecated May 7, 2026; docs removed June 2026)
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/advanced/crawling/managing-multi-regional-sites
- https://web.dev/articles/vitals

## Gate
This branch adds an audit only. It does **not** assert SEO fixes, indexation, new page launches, passing test commands, Search Console access, or production changes. Before implementation: review actual `SEOHead` and route generators, get missing GSC evidence, then run `python3 scripts/verify_ssot.py` or the verified monorepo equivalent, `npm run check`, `npm run test:run`, `npm run build`, and `npm run check:sitemap` from `apps/website`. Follow `AGENTS.md` and `PROJECT_TRUTH.md`; production remains manual.
