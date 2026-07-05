## 2026-07-05 - Optimize getPublicReferences using Caching
**Learning:** In Astro components, calling expensive data fetching functions multiple times can negatively impact performance. `getPublicReferences` used `.filter` and `.map` on each call which is inefficient.
**Action:** When a function that performs expensive array operations is called repeatedly, cache its result to improve performance. This avoids redundant operations without changing functionality.
