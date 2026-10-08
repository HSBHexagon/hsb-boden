
## 2026-10-08 - Defer Rendering of Below-the-Fold Components
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Always consider using `content-visibility: auto` (with appropriate `contain-intrinsic-size` values) for complex UI elements like footers that are out of the viewport on initial load.
