## 2025-03-08 - LCP Images Eager Loading
**Learning:** Found above-the-fold hero images in `src/pages/leistungen/[slug].astro` and `src/pages/branchen/[slug].astro` configured with `loading="lazy"`. This is a performance anti-pattern as it delays loading Largest Contentful Paint (LCP) candidates.
**Action:** Replace `loading="lazy"` with `fetchpriority="high" loading="eager" decoding="async"` on images immediately below page heroes or directly in the initial viewport to signal priority to the browser and ensure immediate fetching.
