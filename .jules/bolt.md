## 2026-09-24 - Optimize Footer Render Performance
**Learning:** Applying `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Always consider using `[content-visibility:auto]` and `[contain-intrinsic-size:400px]` utility classes on large footer or below-the-fold components.
