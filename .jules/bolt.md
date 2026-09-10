
## 2024-05-15 - LCP Images Below PageHero
**Learning:** Images injected immediately below textual PageHero components on content routes (like service and industry pages) are LCP candidates and should not be loaded with `loading="lazy"`. Doing so delays the largest contentful paint and negatively impacts performance metrics.
**Action:** Explicitly configure these LCP candidate images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) to ensure they are fetched as early as possible.
