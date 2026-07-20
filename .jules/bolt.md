
## 2024-05-18 - Avoid flatMap overhead in map/filter operations
**Learning:** In V8/Node.js, using `.flatMap()` to combine `map` and `filter` operations can degrade performance. This happens because `.flatMap()` creates small intermediate arrays for every element before flattening them into the final result.
**Action:** Use `.reduce()` instead of `.flatMap()` when combining `map` and `filter` operations to avoid the overhead of intermediate array allocations.
