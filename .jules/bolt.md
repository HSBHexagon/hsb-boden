## 2024-05-20 - Pre-computing module-scope static data operations
**Learning:** In Astro, content getter functions operating on static data arrays (like in `src/lib/content.ts`) that use `.filter()` and `.map()` run synchronously on every invocation. This causes redundant O(N) operations and object allocations during SSR and build processes.
**Action:** Pre-compute and cache the results of expensive array operations at the module scope when dealing with static data to avoid redundant processing.
