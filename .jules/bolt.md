## 2026-09-23 - Optimize Footer rendering
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply this pattern to other heavy, below-the-fold components to improve initial load performance.
