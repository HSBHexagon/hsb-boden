## 2024-05-24 - LCP Image Eager Loading
**Learning:** Images injected immediately below the textual PageHero components on dynamic content routes are LCP candidates. Using `loading="lazy"` on these delays the Largest Contentful Paint.
**Action:** Always configure above-the-fold LCP candidate images with `fetchpriority="high" loading="eager" decoding="async"` instead of lazy loading.
