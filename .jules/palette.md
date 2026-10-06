## 2026-10-06 - Add focus visible styles for dynamically rendered overlays
**Learning:** Interactive elements in dynamically rendered overlays (like the LanguageSuggest banner) need explicit Tailwind `focus-visible` classes because native focus outlines are often insufficient or stripped by default styles.
**Action:** Always explicitly add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color]` to buttons and links in dynamic banners/overlays to ensure keyboard accessibility.
