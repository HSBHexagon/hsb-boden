## 2024-08-18 - Eager Load LCP Images Below PageHero
**Learning:** Images injected immediately below the textual PageHero components on content routes (like service and industry pages) are LCP candidates and must be configured with eager loading attributes. Lazy loading these critical images causes rendering delays and hurts Core Web Vitals.
**Action:** When implementing new content page layouts that feature an image prominent above the fold (e.g. right below the header), ensure the <img> tag uses `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"`.
