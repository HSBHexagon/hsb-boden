## 2025-05-14 - Optimize LCP Images Above the Fold
**Learning:** Images injected immediately below textual PageHero components on content routes (like service and industry pages) are LCP candidates. This codebase's architecture previously defaulted to lazy loading for these critical images, causing rendering delays.
**Action:** Always configure critical above-the-fold images (LCP candidates) with `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"`.
