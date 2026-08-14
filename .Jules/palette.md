## 2026-08-14 - Prevent CSS Grid Layout Issues for Form Labels with Inline Indicators
**Learning:** When appending inline visual indicators (like an asterisk for required fields) to form labels that use CSS grid layouts, the grid will force the label text and the indicator onto separate rows if they are direct children.
**Action:** Always wrap the main label text and the inline indicator within a single `<span>` element to ensure they flow together nicely and prevent layout breakage in grid containers.
