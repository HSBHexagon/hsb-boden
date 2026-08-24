## 2024-05-23 - [LCP Image Optimization]
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and must be configured with eager loading attributes instead of lazy loading to prevent rendering delays.
**Action:** Always verify that above-the-fold LCP candidates use `fetchpriority="high" loading="eager" decoding="async"`.
