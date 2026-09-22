## 2026-09-18 - Deferring Footer Rendering
**Learning:** Heavy global components like footers that are consistently below the fold can negatively impact initial paint time if rendered synchronously. Adding `content-visibility: auto` skips their rendering work until they are scrolled into view.
**Action:** Use `content-visibility: auto` alongside `contain-intrinsic-size` for heavy, deep-DOM elements below the fold.
