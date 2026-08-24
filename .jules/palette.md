## 2024-08-24 - Form Field Layout with CSS Grid
**Learning:** When appending inline visual indicators (e.g., required asterisks) to form labels that use CSS grid layouts, the text and indicator must be wrapped in a `<span>` container. Otherwise, the grid layout will force the label text and the asterisk onto separate rows, breaking the design.
**Action:** Always wrap label text and indicators in a `<span>` when working within grid or flexbox parent containers to maintain inline rendering.
