## 2024-08-06 - LCP Images Optimization
**Learning:** Images injected immediately below textual PageHero components on content routes (e.g. `leistungen`, `branchen`, `referenzen`) are often LCP (Largest Contentful Paint) candidates. When they are loaded with `loading="lazy"`, it delays rendering and impacts performance scores.
**Action:** Always identify above-the-fold images and configure them with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) to ensure they are prioritized by the browser, optimizing LCP times.
