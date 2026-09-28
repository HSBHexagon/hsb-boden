## 2026-09-26 - [content-visibility: auto]
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply `[content-visibility:auto] [contain-intrinsic-size:<estimated-height>]` via Tailwind to heavy below-the-fold elements (e.g. footers, complex hidden sections).
