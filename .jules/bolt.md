## 2024-05-24 - LCP Image Loading Optimization
**Learning:** Images injected immediately below `PageHero` components (e.g., on `leistungen` and `branchen` routes) are LCP candidates and must not be lazy-loaded.
**Action:** Always configure LCP images with `fetchpriority="high" loading="eager" decoding="async"` to prevent rendering delays.
