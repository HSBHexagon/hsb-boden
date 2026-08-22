## 2024-05-15 - [Optimize LCP Image Loading for Better Performance]
**Learning:** In Astro, images that are considered Largest Contentful Paint (LCP) candidates (like hero images immediately following text components) should not be lazy-loaded, as it delays their loading and hurts performance metrics.
**Action:** When implementing pages with above-the-fold images, configure them with `fetchpriority="high" loading="eager" decoding="async"` instead of the default `loading="lazy"` to ensure they are fetched as early as possible without blocking parsing.
