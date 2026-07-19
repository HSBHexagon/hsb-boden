## 2026-07-19 - Avoid .flatMap() for single-element mapping
**Learning:** In V8/Node.js, `.flatMap()` allocates a small intermediate array for every processed element. For operations that only map to a single element (or filter items out by mapping to an empty array), this creates unnecessary garbage collection overhead compared to using `.reduce()`.
**Action:** When performing combined filter-map operations where the mapping usually returns a single element or nothing, prefer `.reduce()` pushing to an accumulator array over `.flatMap()` returning an array for each item.
