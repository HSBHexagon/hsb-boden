## 2026-07-14 - CSS Grid and Inline Visual Indicators
**Learning:** When appending inline visual indicators (e.g., required asterisks) to form labels using CSS grid layouts, the grid will force them onto separate rows if they are direct children. Wrapping the label text and the indicator in a `<span>` container prevents this.
**Action:** Always wrap text and inline indicators inside a container element when the parent uses a grid or flex layout.
