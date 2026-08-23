## 2024-08-23 - Eager load LCP candidates
**Learning:** Images injected immediately below `PageHero` components on content routes (e.g., service and industry pages) are LCP candidates. Lazy loading them delays the LCP event and hurts performance.
**Action:** Always configure LCP candidate images with `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"`.
