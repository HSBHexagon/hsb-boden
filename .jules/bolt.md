## 2026-07-14 - Optimize Above-The-Fold Images
**Learning:** Found instances where primary images (above the fold) on dynamic routing pages were set to `loading="lazy"`. This delays the loading of Large Contentful Paint (LCP) candidates.
**Action:** When working on Astro/frontend templates, ensure above-the-fold images use `fetchpriority="high" loading="eager" decoding="async"` and never use `loading="lazy"`.
