## 2026-09-27 - Add explicit focus indicators to dynamic banner
**Learning:** Interactive elements within dynamically rendered DOM overlays (like LanguageSuggest banner) often lack native focus indicators that are visibly prominent, making keyboard navigation difficult for accessibility users.
**Action:** Always ensure dynamic actionable elements (buttons, links) in banners have explicit Tailwind `focus-visible` classes (e.g., `focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none`).
