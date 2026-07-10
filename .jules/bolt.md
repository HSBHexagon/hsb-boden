## 2026-07-10 - Pre-computing Astro Render Functions
**Learning:** In Astro templates, inline operations like `Array.filter` inside `.map` calls are re-evaluated on every render. Given Astro's server-first rendering, this can become a minor bottleneck on pages with heavy iteration.
**Action:** Extract list filtering and other derived state calculations into the Astro component's frontmatter (`---` block) so they execute exactly once per component lifecycle.
