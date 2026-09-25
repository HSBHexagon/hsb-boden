## 2026-09-25 - Content Visibility on Global Footer
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Always consider `content-visibility` for large below-the-fold elements to defer rendering until they approach the viewport.
