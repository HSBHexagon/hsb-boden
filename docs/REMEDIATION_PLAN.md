# Remediation Plan & Repository Audit

## 1. Unused Files & Components
The following files are not imported or used anywhere in the current application source code. However, following the strict rule of "never delete production files", they should be reviewed manually before any deletion is performed.

*   `src/data/germanyMap.ts`: Not imported. `ReferenceMap.astro` currently uses a hardcoded SVG instead of this file.
*   `src/components/localization/LanguageOffer.tsx`: Not imported. Language selection is currently handled via `LanguageSuggest.astro`.
*   `src/components/layout/Breadcrumbs.astro`: Not imported. Breadcrumbs are not currently used in the layout.

## 2. Unused Assets & Oversized Images
*   All images in `public/media/` should be reviewed. No explicitly unused media files were detected in this pass, but a full cross-reference of all used strings against the public folder would be needed to guarantee no orphans.
*   The `ProofMediaSection` has multiple images loaded as `.webp` which is optimal. Ensure source images are adequately compressed.

## 3. SEO & Accessibility
*   **Sitemap & Robots.txt:** Verified working and correctly generated via Astro endpoints (`src/pages/robots.txt.ts`, `src/pages/sitemap.xml.ts`).
*   **Structured Data:** The site uses `buildLocalBusinessJsonLd` in `src/lib/schema.ts` which provides a solid baseline for local business schema coverage.
*   **OpenGraph:** SEO component handles OG meta tags appropriately.

## 4. Cloudflare & Wrangler Configuration
*   `wrangler.toml` has `nodejs_compat` correctly configured.
*   Assets are bound correctly to `./dist`.

## 5. Duplicate Components / Dead Code
*   No other significant dead code detected beyond the unused files mentioned in section 1.
*   Header component had an unused `lang` prop declaration which has been safely removed.
