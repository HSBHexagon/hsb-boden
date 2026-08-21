## 2024-05-24 - [Optimize LCP Images]
**Learning:** Images injected immediately below the textual `PageHero` components on content routes (like service and industry pages) are LCP candidates. Using `loading="lazy"` on these delays rendering and hurts Core Web Vitals.
**Action:** Always use `fetchpriority="high" loading="eager" decoding="async"` for LCP candidate images above the fold instead of lazy loading.
