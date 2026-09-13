## 2025-03-13 - Eager Loading LCP Candidates
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates. Using `loading="lazy"` on these delays rendering.
**Action:** Always configure critical above-the-fold images (LCP candidates) with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`).
