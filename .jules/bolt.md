## 2026-09-27 - Content Visibility Optimization for Footer
**Learning:** Adding `content-visibility: auto` along with `contain-intrinsic-size` to deep, heavy global components that are consistently rendered below the fold (like the global `<Footer>`) is an effective performance optimization in this codebase to reduce initial rendering and paint times.
**Action:** Apply these CSS properties using Tailwind arbitrary values `[content-visibility:auto] [contain-intrinsic-size:400px]` to heavy below-the-fold components to improve initial page load performance without affecting visual layout.
