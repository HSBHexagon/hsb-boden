## 2024-05-24 - Loading states and text content replacement
**Learning:** When adding inline SVG elements (like spinners) to buttons, their text must be wrapped in `<span>` tags. Updating the `.textContent` property of the button element directly destroys any child elements, removing the spinner icon entirely.
**Action:** Always wrap text inside buttons in spans when dynamic JS updates are involved, or update the `span` element explicitly.
