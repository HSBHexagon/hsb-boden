## 2025-05-24 - LeadForm Grid Layout Accessibility
**Learning:** When appending inline visual indicators (like required asterisks) to form labels using CSS grid layouts, the text and indicator must be wrapped in a `<span>`. Otherwise, the grid forces the asterisk onto a separate row, breaking the visual association.
**Action:** Always wrap label text and inline indicators in a common `<span>` container when they are direct children of a CSS grid container.
