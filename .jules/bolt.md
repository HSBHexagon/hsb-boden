## 2026-09-22 - [content-visibility for Footer]
**Learning:** Heavy global components below the fold (like Footer) can impact initial render times significantly. Using `content-visibility: auto` along with `contain-intrinsic-size` defers rendering and paint for these elements.
**Action:** Apply `[content-visibility:auto]` and `[contain-intrinsic-size:400px]` via Tailwind arbitrary values to deep, below-the-fold components to reduce initial paint times.
