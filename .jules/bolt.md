## 2026-08-12 - LCP Image Eager Loading
**Learning:** Found above-the-fold hero and LCP candidate images in content pages (leistungen, branchen, referenzen) using `loading="lazy"`. This delays rendering of critical visual components on initial page load, impacting the LCP metric.
**Action:** Always apply `fetchpriority="high" loading="eager" decoding="async"` to LCP candidates, and ensure `loading="lazy"` is only applied to below-the-fold assets.
