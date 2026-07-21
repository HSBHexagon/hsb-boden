## 2026-07-21 - LCP Optimization for dynamic pages
**Learning:** Avoid using `loading="lazy"` on above-the-fold hero images as this delays the Largest Contentful Paint (LCP) and degrades perceived load performance.
**Action:** For hero images (e.g., in template pages like `[slug].astro`), apply `fetchpriority="high" loading="eager" decoding="async"` to prioritize their fetch and ensure quick rendering without blocking the main thread.
