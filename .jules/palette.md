## 2024-05-24 - Clear Required Indicators & Focus Rings
**Learning:** Native focus outlines are often insufficient or stripped in Tailwind projects. Also, users need a clear visual indicator for required HTML5 form fields to improve accessibility.
**Action:** Always add explicit `focus-visible` classes (like `focus-visible:ring-2`) to interactive elements and append an `aria-hidden="true"` red asterisk to required labels.
