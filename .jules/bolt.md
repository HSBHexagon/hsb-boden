## 2024-05-15 - Optimize LCP Image Loading
**Learning:** Images injected immediately below the textual PageHero components on content routes (like service and industry pages) are LCP candidates and should not use `loading="lazy"`.
**Action:** Always use `fetchpriority="high" loading="eager" decoding="async"` for above-the-fold LCP candidates to prevent rendering delays.
