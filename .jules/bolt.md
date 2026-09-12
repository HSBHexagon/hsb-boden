## 2024-05-24 - LCP Images Below PageHero
**Learning:** Images injected immediately below textual PageHero components on content routes (like service and industry pages) are LCP candidates.
**Action:** Always configure these specific images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of `loading="lazy"` to prevent rendering delays.
