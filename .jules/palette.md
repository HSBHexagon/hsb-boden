## 2026-09-08 - Accessible Forms
**Learning:** Added `span` wrapping around labels and asterisks so the grid layout doesn't break when adding asterisks. Added `aria-hidden="true"` to asterisks for screen readers to avoid reading out "*". Ensured interactive elements have `focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none` for keyboard navigation visibility.
**Action:** Always wrap inline visual indicators and text in a span when using CSS grids, and make sure required form elements are visually indicated and have accessible keyboard focus states.
