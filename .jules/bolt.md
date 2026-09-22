
## 2024-05-24 - [Footer Render Optimization]
**Learning:** Using `content-visibility: auto` along with `contain-intrinsic-size` on deep, heavy global components that are consistently rendered below the fold (like `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply `[content-visibility:auto] [contain-intrinsic-size:<height>]` classes to large below-the-fold container elements to defer their rendering.
