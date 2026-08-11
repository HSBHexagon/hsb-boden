## 2024-08-11 - LCP Image Loading Optimization
**Learning:** Images injected immediately below textual PageHero components on content routes (like service and industry pages) are Above-The-Fold (LCP candidates). Lazy loading these images (`loading="lazy"`) causes a delay in rendering the Largest Contentful Paint.
**Action:** Always use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` for these specific LCP candidate images to prevent rendering delays.
