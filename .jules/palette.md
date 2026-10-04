## 2026-10-04 - Add focus visible styles to LanguageSuggest
**Learning:** Interactive elements in dynamically rendered overlays (like LanguageSuggest) need explicit focus-visible classes (e.g. `focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none`) to ensure keyboard navigation visibility, as native focus outlines are often insufficient or stripped.
**Action:** Add `focus-visible` utility classes to all interactive elements within overlays or banners.
