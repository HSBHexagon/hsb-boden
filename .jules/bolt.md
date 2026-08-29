## 2025-02-27 - LCP Image Optimization
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and should not be lazy-loaded.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` for critical above-the-fold images to prevent rendering delays.
