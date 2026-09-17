## 2024-05-24 - Explicit Focus Indicators for Keyboard Navigation
**Learning:** Native focus outlines on interactive elements (links, buttons, logos) can be insufficient or unintentionally hidden, especially against dark backgrounds or with custom CSS resets. Without explicit indicators, keyboard navigation becomes difficult.
**Action:** Always add explicit Tailwind `focus-visible` classes (e.g., `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white`) to ensure robust visual focus states for interactive UI components, adhering to WCAG 2.4.7 guidelines.
