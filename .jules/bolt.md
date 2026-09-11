## 2024-09-12 - Eager Loading for LCP Candidate Images
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and should be configured with eager loading.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` for these images to prevent rendering delays.
