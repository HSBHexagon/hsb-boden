## 2026-07-21 - Optimize getPublishableTeamProfiles and getPublishableCaseStudies
**Learning:** In V8/Node.js, using `.flatMap()` for combined mapping and filtering operations can degrade performance because it often causes overhead from allocating small intermediate arrays for every single item.
**Action:** Use `.reduce()` when performing combined mapping and filtering on collections to prevent intermediate array allocations and reduce garbage collection overhead, thereby boosting execution speed.
