## 2024-05-18 - Optimize LCP Image Loading
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and must be configured with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of `loading="lazy"` to prevent rendering delays.
**Action:** Always check the position of images relative to the fold and hero sections to ensure correct loading strategies are applied.
