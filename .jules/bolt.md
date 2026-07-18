## `getRequiredConsentCategories` Optimization

- **Date:** 2026-07-18
- **File:** `src/data/consent.ts`
- **Change:** Replaced `.filter().map()` array chain with a single `.reduce()` for `getRequiredConsentCategories()`.
- **Baseline (filter+map):** 59.62ms (per 1,000,000 iterations)
- **Optimized (reduce):** 39.94ms (per 1,000,000 iterations)
- **Improvement:** ~33% performance increase over the baseline due to eliminating the intermediate array allocation.
