## 2026-09-09 - Optimized LCP image loading
**Learning:** Found an anti-pattern where critical above-the-fold images (LCP candidates) in `.astro` files were configured with `loading="lazy"`. This delays the rendering of the most important images in the viewport.
**Action:** Changed the image tag attributes from `loading="lazy"` to `fetchpriority="high" loading="eager" decoding="async"` on `src/pages/leistungen/[slug].astro` and `src/pages/branchen/[slug].astro` which are the main content pages to improve Core Web Vitals (Specifically Largest Contentful Paint).
