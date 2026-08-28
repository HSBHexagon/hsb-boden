## 2024-03-24 - LCP Image Optimization in Astro
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. Using `loading="lazy"` on these images causes rendering delays.
**Action:** Always configure LCP candidates with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of lazy loading.
