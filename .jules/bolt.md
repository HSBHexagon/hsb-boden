
## 2024-05-24 - LCP candidates incorrectly lazy-loaded
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and should not use `loading="lazy"`.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` for LCP candidates to prevent rendering delays.
