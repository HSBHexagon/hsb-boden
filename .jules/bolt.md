
## 2024-09-07 - LCP Candidate Optimization in Astro Content Routes
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. Lazy loading them delays rendering and harms performance.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` for these above-the-fold images to optimize LCP.
