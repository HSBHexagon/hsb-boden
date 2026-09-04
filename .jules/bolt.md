## YYYY-MM-DD - [Bolt Initialization]
**Learning:** Initializing Bolt journal.
**Action:** Ready to record critical performance learnings.

## 2024-05-14 - [Optimize LCP Image Loading]
**Learning:** Images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and should not be lazy-loaded.
**Action:** Always configure critical above-the-fold images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) to prevent rendering delays.
