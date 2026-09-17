## 2024-09-17 - LCP Image Loading on Referenzen Page
**Learning:** Images injected immediately below textual `PageHero` components (like on the referenzen page) are LCP candidates.
**Action:** Always configure these LCP candidates with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of lazy loading.
