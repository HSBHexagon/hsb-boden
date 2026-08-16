## 2024-08-16 - Eager load LCP candidates
**Learning:** Images injected immediately below the textual PageHero components on content routes (like service, industry, references) are LCP candidates and should not be lazy-loaded.
**Action:** Use fetchpriority="high" loading="eager" decoding="async" instead of loading="lazy" for critical above-the-fold images to prevent rendering delays.
