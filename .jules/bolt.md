
## 2026-10-05 - [Defer off-screen global components rendering]
**Learning:** Using `content-visibility: auto` along with `contain-intrinsic-size` on deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply this pattern to other heavy, below-the-fold components to reduce initial main-thread blocking.
