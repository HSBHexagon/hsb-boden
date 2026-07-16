## 2024-07-16 - CSS Grid and Inline Form Indicators
**Learning:** When adding inline visual indicators (like required asterisks) to form labels that use CSS Grid layouts, appending the indicator directly inside the `<label>` causes the grid to force the label text and the indicator onto separate rows, ruining the layout.
**Action:** Wrap the label text and the indicator in a `<span>` container within the `<label>` to preserve the inline layout while utilizing CSS Grid.
