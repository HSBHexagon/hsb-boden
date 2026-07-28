## 2024-07-28 - LCP Candidate Image Eager Loading
**Learning:** In this codebase's layout, images injected immediately below the textual PageHero components (e.g., on content routes like service and industry pages) are LCP candidates and should not be lazy-loaded.
**Action:** Always use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` for LCP candidate images to prevent rendering delays.
