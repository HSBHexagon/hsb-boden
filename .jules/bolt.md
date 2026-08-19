## 2024-03-08 - Prioritize LCP Images on Content Routes
**Learning:** Images injected immediately below textual PageHero components (like on `/branchen/[slug]` and `/leistungen/[slug]`) act as LCP (Largest Contentful Paint) candidates. Applying `loading="lazy"` delays their rendering, hurting performance metrics.
**Action:** Always configure above-the-fold LCP candidate images with `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"`.
