## 2024-05-15 - [LCP Image Optimization in Content Layouts]
**Learning:** In this codebase, images injected immediately below the textual PageHero components on content routes (like service and industry pages) are Above-the-Fold LCP candidates, and should not use `loading="lazy"`.
**Action:** Always configure LCP candidate images with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) to prevent rendering delays.
