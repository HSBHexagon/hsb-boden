## 2026-09-20 - [Add content-visibility to global footer]
**Learning:** Heavy global components that are consistently rendered below the fold (like the global <Footer>) can significantly impact initial rendering and paint times.
**Action:** Apply `[content-visibility:auto]` along with `[contain-intrinsic-size:400px]` to these components to reduce initial rendering load.
