## 2024-09-24 - Add loading spinner to async submit button
**Learning:** For async operations like form submissions, adding a visual loading spinner immediately communicates to the user that the system is processing their request. However, modifying a button's `textContent` directly using JavaScript will destroy any child SVG icons.
**Action:** When adding dynamic JS to update a button's text that also contains inline SVGs (like a loading spinner), wrap the text in a `<span>` and target the span's `.textContent`.
