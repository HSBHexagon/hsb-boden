## 2024-10-25 - [Frontend Performance] LCP Images should use eager loading
**Learning:** Images injected immediately below textual PageHero components on content routes (like service, industry, and references pages) are Largest Contentful Paint (LCP) candidates. By default, they were using `loading="lazy"`, which causes significant rendering delays for the critical above-the-fold content.
**Action:** For all LCP candidate images (above-the-fold), use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` to optimize render times.
