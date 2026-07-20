## 2024-05-24 - Fix Form Label and Required Indicator Alignment
**Learning:** CSS Grid layouts can force inline elements (like a text node and an appended red asterisk indicator for required fields) onto separate rows if they are direct children of the grid container (the `<label>`).
**Action:** Always wrap the text and its accompanying inline visual indicators (like the required asterisk) together within a `<span>` to ensure they flow together and remain on the same line when placed inside a CSS grid or flexbox container.
