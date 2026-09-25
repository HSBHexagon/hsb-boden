## 2026-09-25 - Focus States on Dynamically Rendered Components
**Learning:** Even utility-like banners that appear dynamically (like language suggestions based on locale) need explicit focus indicators for keyboard navigation, as native outlines are often insufficient or stripped by CSS resets.
**Action:** Always verify keyboard accessibility (`focus-visible` classes) on conditionally rendered overlay components, not just main page content.
