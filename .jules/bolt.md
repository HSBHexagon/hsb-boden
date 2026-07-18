## ReferenceMap.astro Loop Optimization

When working with Astro components processing mapped arrays for components (like `ReferenceMap.astro`), redundant array iterations can be safely combined. Even though V8 heavily optimizes `.map()` combined with `for` loops making the absolute performance impact marginal (~0.5-1% improvement over large datasets), it's a good architectural standard to perform both map-like transformations and data collection in a single iteration pass where possible to avoid unnecessary allocations.
