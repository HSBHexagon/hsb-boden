## 2026-09-30 - CSS content-visibility for global below-fold components
**Learning:** Adding content-visibility: auto along with contain-intrinsic-size to deep, heavy global components that are consistently rendered below the fold (like the global Footer) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Always apply [content-visibility:auto] and [contain-intrinsic-size:400px] using full bracket notation in Tailwind CSS for large global below-the-fold components like footers.
