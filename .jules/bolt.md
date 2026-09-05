## 2024-09-05 - LCP Images Below Text-Only Heros
**Learning:** In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. They were previously configured with `loading="lazy"`, which causes a rendering delay.
**Action:** Always configure critical above-the-fold images (LCP candidates) with `fetchpriority="high" loading="eager" decoding="async"` instead of lazy loading.
