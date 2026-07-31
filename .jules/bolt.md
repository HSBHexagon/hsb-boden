## 2024-07-31 - Eager Load LCP Images on Content Routes
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. When these images are configured with `loading="lazy"`, it delays their rendering, hurting the Largest Contentful Paint metric.
**Action:** Always configure critical above-the-fold images (LCP candidates) with `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` to prevent rendering delays.
