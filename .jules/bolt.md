## 2024-05-24 - LCP Images Below PageHero
**Learning:** In this codebase's layout, images injected immediately below textual PageHero components are LCP candidates, and if they use `loading="lazy"`, it delays rendering.
**Action:** Use `fetchpriority="high" loading="eager" decoding="async"` for above-the-fold LCP candidates instead of `loading="lazy"`.
