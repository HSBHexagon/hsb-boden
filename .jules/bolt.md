## 2026-10-01 - Optimizing Global Deep Elements with content-visibility
**Learning:** Adding `[content-visibility:auto]` alongside `[contain-intrinsic-size:400px]` is an effective, non-intrusive way to optimize heavy, below-the-fold global components (like the footer) in this codebase without needing architectural changes.
**Action:** When inspecting heavy, deep DOM subtrees that are consistently rendered off-screen on initial load, consider applying `content-visibility: auto` to defer layout and paint, freeing up main thread resources.
