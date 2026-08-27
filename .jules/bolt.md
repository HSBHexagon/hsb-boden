## 2026-08-27 - Optimize LCP images with eager loading
**Learning:** Images injected immediately below textual PageHero components on content routes (like service and industry pages) are LCP (Largest Contentful Paint) candidates. Using loading="lazy" on these images delays rendering and negatively impacts performance.
**Action:** Always configure LCP candidate images with fetchpriority="high" loading="eager" decoding="async" instead of lazy loading to prioritize their fetch and rendering.
