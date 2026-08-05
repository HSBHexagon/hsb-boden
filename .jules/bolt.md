## 2024-05-30 - Eager Load LCP Images After PageHero
**Learning:** Images injected immediately below textual PageHero components (like on content routes for service and industry pages) are LCP candidates, and using default lazy loading delays rendering.
**Action:** Always configure these LCP candidate images with fetchpriority="high" loading="eager" decoding="async" instead of loading="lazy".
