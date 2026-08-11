# Palette UX/Accessibility Learnings

## 2026-08-11 - Form Accessibility and Focus Visibility
**Learning:** In Astro templates using CSS grid layouts, adding inline elements like a required asterisk directly next to text can cause the grid to force them onto separate rows. Additionally, native browser focus rings are easily stripped or not sufficiently visible, making keyboard navigation difficult.
**Action:** When adding inline visual indicators (like asterisks) inside labels that are part of a CSS grid, wrap both the label text and the indicator in a `<span>` container to maintain them on the same line. Furthermore, proactively apply explicit Tailwind `focus-visible` classes (`focus-visible:ring-2 focus-visible:ring-[color] focus-visible:outline-none`) to all interactive elements (inputs, selects, textareas, buttons) to ensure clear, robust keyboard navigation indicators.
