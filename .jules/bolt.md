## 2026-07-06 - LCP Optimization for Hero Images
**Learning:** Found that hero images (LCP candidates) in `branchen` and `leistungen` pages were incorrectly marked with `loading="lazy"`. This delays the Largest Contentful Paint because the browser waits for layout computation before requesting the image.
**Action:** Always verify that critical above-the-fold images use `fetchpriority="high" loading="eager" decoding="async"` to prioritize loading.
