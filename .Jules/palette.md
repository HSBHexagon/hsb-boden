## 2026-10-02 - Add loading state to async forms
**Learning:** In Astro, when adding a loading spinner (SVG) to a submit button that dynamically changes text, updating the button's `textContent` directly deletes the child elements (e.g., the SVG). This breaks the loading state on subsequent submissions or errors.
**Action:** Wrap the button text in a `<span>` element and target the span's `textContent` instead. Also, add `aria-busy="true"` on the button while async requests are active to communicate the loading state to screen readers.
