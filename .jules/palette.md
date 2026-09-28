## 2026-09-28 - [LanguageSuggest Focus]
**Learning:** Dynamically rendered overlays (like LanguageSuggest) often have native focus outlines that are stripped or insufficient. Interactive elements in such overlays need explicit focus-visible classes for keyboard navigation.
**Action:** Always add explicit focus-visible classes (e.g., focus-visible:ring-2 focus-visible:ring-hsb-red) to links and buttons within dynamically injected UI components.
