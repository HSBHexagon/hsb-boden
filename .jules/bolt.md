## 2026-09-21 - Content-Visibility on below-the-fold components
**Learning:** Using `content-visibility: auto` along with `contain-intrinsic-size` on deep, heavy global components rendered below the fold (like `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Always consider `content-visibility: auto` for large UI sections consistently placed at the bottom of the page, ensuring to provide a `contain-intrinsic-size` to prevent layout shifts.
