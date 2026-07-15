## 2024-07-15 - LCP Optimization for Astro Components
**Learning:** For dynamic pages built via Astro components (`[slug].astro`), make sure above-the-fold images like `serviceImage` and `industryImage` are eagerly loaded with `fetchpriority="high"` instead of lazily. Since they are rendered near the top, this prevents LCP delays caused by standard lazy loading.
**Action:** Always inspect hero and immediately-below-hero images to verify they do not use `loading="lazy"` when optimizing LCP metrics.
