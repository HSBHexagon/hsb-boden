
## 2024-03-09 - LCP Candidate Image Eager Loading
**Learning:** In this codebase's layout, images injected immediately below the textual PageHero components on content routes (service and industry pages) are LCP candidates. Using `loading="lazy"` on these delays the LCP.
**Action:** For LCP candidates, always use `fetchpriority="high" loading="eager" decoding="async"` instead of lazy loading.
