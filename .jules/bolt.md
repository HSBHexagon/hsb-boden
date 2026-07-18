## 2026-06-12 - Astro Frontmatter & Pre-computation
**Learning:** Pre-computing derived data (like `.filter()` and `.map()`) in Astro's frontmatter (`---` block) instead of in the JSX template significantly reduces redundant computations during SSR/SSG. Astro runs the frontmatter once per page build/render, whereas inline computations run during template evaluation.
**Action:** Always extract complex logic or array derivations into the frontmatter. Avoid pre-computing these at the module level (e.g., in `src/lib/content.ts`) as a micro-optimization since it introduces state mutation risks for minimal gain.

## 2026-06-12 - Explicit Image Prioritization for LCP
**Learning:** The Header logo is a critical above-the-fold asset in this application architecture. Not providing explicit fetching strategies can cause unnecessary rendering delays and affect Largest Contentful Paint (LCP) times.
**Action:** For critical LCP candidates like the header logo, always include `fetchpriority="high" loading="eager" decoding="async"` instead of relying on default browser behavior or `loading="lazy"`.
