## 2026-09-28 - Defer rendering of heavy global components
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global Footer) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply this optimization to global elements that are guaranteed to be off-screen during initial load to improve metrics like TBT (Total Blocking Time) and LCP (Largest Contentful Paint).
