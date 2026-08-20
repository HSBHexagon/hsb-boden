## 2024-08-20 - [LCP Image Eager Loading]
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and utilizing lazy loading delays rendering.
**Action:** Always configure critical above-the-fold LCP candidate images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of `loading="lazy"`.
