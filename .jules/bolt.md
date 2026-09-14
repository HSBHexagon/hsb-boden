## 2024-09-14 - LCP Image Pattern on Content Routes
**Learning:** Images injected immediately below textual `PageHero` components on service and industry pages are LCP candidates but were configured with `loading="lazy"`. This codebase-specific pattern delays critical rendering.
**Action:** Always use `fetchpriority="high" loading="eager" decoding="async"` for primary imagery directly following `PageHero` components to optimize above-the-fold content delivery.
