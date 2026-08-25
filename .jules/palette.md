## 2024-05-30 - Focus States and Required Indicators on Forms
**Learning:** Relying on native focus rings often leads to inconsistent or missing keyboard navigation cues. Furthermore, using CSS grid on `<label>` elements can break inline required indicators if they aren't explicitly wrapped in a container.
**Action:** Always add explicit Tailwind `focus-visible` classes to all interactive form elements, and wrap label text + required asterisks in a `<span>` when using CSS grid layouts.
