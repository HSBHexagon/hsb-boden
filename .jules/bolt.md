## 2024-05-18 - Eager Loading LCP Images Below PageHero
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and must not be lazy-loaded.
**Action:** Always configure LCP images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) to prevent rendering delays.
