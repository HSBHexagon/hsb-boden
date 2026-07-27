## 2024-07-27 - LCP Images Below PageHero
**Learning:** Images injected immediately below textual PageHero components on content routes (e.g., /leistungen/, /branchen/, /referenzen/) are LCP candidates, and lazy loading them delays rendering.
**Action:** Use fetchpriority="high" loading="eager" decoding="async" instead of loading="lazy" for critical above-the-fold images to optimize LCP.
