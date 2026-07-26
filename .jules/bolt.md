## 2026-07-26 - LCP Images Optimization
**Learning:** Found that LCP candidate images (images placed immediately below `PageHero` headers on main landing pages like `leistungen`, `branchen`, and `referenzen`) were incorrectly optimized using `loading="lazy"`. This delays the main image render and negatively affects performance metrics (LCP).
**Action:** Always verify that critical above-the-fold images use `fetchpriority="high" loading="eager" decoding="async"` to prevent rendering delays. Ensure that lazy loading is only applied to images located below the fold.
