## 2026-07-28 - CSS Grid and Form Labels
**Learning:** When adding inline visual indicators (like required asterisks) to form labels styled with CSS Grid, directly appending the element causes the grid to forcefully place the text and the indicator on separate rows.
**Action:** Always wrap the label text and the inline indicator inside a `<span>` container to ensure they stay on the same line and flow correctly.
