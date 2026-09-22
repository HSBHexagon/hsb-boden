## 2024-05-23 - Wrap Button Text when using Inline SVGs
**Learning:** When adding dynamic JS to update a button's text that also contains inline SVGs (like a loading spinner), updating the button's `.textContent` directly will destroy its child elements.
**Action:** Wrap the text in a `<span>` and target the span's `.textContent` to preserve the SVG spinner.
