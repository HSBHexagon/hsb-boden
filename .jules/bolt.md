## 2024-09-02 - Image Loading Strategy
**Learning:** Images injected immediately below `PageHero` components are LCP (Largest Contentful Paint) candidates. Astro's default `loading="lazy"` on these images delays their rendering.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` for LCP candidate images on route templates like `/leistungen/[slug].astro`, `/branchen/[slug].astro`, and `/referenzen/index.astro`.
