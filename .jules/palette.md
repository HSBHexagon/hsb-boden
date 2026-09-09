
## 2024-05-18 - Form Required Indicators and Focus Outline
**Learning:** Native `required` attributes and focus outlines are insufficient for accessibility; explicit visible indicators (e.g., `*` with `aria-hidden="true"`) and defined focus-visible classes are necessary for clear user guidance, especially inside CSS Grid structures where `<span>` wrappers prevent layout breaks.
**Action:** Always wrap label text and indicators in a `<span>` in grid layouts and apply explicit `focus-visible` Tailwind classes to interactive elements.
