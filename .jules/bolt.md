## 2024-08-15 - Optimize LCP Images Below PageHero Components
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) act as Largest Contentful Paint (LCP) candidates. Using the default `loading="lazy"` attribute on these images causes measurable rendering delays, degrading Core Web Vitals.
**Action:** Always configure these above-the-fold hero images with `fetchpriority="high" loading="eager" decoding="async"` instead of lazy loading.
