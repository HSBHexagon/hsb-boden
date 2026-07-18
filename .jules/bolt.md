## 2026-07-18 - Eager loading LCP hero images
**Learning:** Using `loading="lazy"` on above-the-fold hero images (LCP candidates) in Astro dynamic routes causes a severe Largest Contentful Paint (LCP) performance bottleneck. The browser's preload scanner cannot fetch lazy-loaded images immediately, delaying the render until layout calculation is complete.
**Action:** Always identify above-the-fold hero images and ensure they use `fetchpriority="high" loading="eager" decoding="async"` to instruct the browser to prioritize fetching these assets.
