# Palette Journal

## 2024-08-08 - Accessible Required Form Fields & Focus States
**Learning:** Native `required` asterisks are often visually ambiguous or missing entirely for sighted users, and browsers default focus rings are frequently insufficient or inconsistent across form elements (inputs, selects, textareas, checkboxes).
**Action:** When creating forms, explicitly render a visual required indicator (like a red asterisk) associated with the `required` attribute. Ensure the indicator uses `aria-hidden="true"` to prevent redundant screen reader announcements (as screen readers already announce the `required` attribute). Additionally, enforce consistent, high-visibility keyboard focus states using Tailwind's `focus-visible:` utilities across all interactive form elements to support users navigating via keyboard.
