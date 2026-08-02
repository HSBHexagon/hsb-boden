## 2026-08-02 - Above-the-fold image lazy loading anti-pattern
**Learning:** Found above-the-fold `PageHero` candidate images configured with `loading="lazy"` which negatively impacted Largest Contentful Paint (LCP) as the browser delayed fetching them.
**Action:** Always configure primary hero or LCP candidate images with `fetchpriority="high" loading="eager" decoding="async"` to ensure the browser prioritizes them immediately.
