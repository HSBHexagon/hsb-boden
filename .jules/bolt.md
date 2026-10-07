## 2026-10-07 - Optimize below-the-fold heavy components with content-visibility
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply `[content-visibility:auto]` and `[contain-intrinsic-size:auto_500px]` to large, off-screen elements via Tailwind classes to defer rendering.
