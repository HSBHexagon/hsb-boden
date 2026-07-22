## 2024-07-22 - Form Required Indicators with CSS Grid
**Learning:** In CSS Grid layouts, directly appending a `<span>` to a text node inside a `<label>` can cause the grid to treat the text and the span as separate track items, forcing them onto separate rows or columns.
**Action:** When adding inline indicators (like a required asterisk) to a label within a CSS grid layout, always wrap the bare label text and the indicator together in an inline container element (like a `<span>`) to ensure they remain grouped as a single grid item.
