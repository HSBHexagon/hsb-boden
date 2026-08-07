## 2024-08-07 - Optimize LCP for Hero Images in Astro Content Routes
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. Astro's default `loading="lazy"` on these images causes measurable render delays.
**Action:** Always identify above-the-fold content images and apply `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"`.
