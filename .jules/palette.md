## 2026-09-26 - Focus States in LanguageSuggest Banner
**Learning:** The dynamically rendered LanguageSuggest banner interactive elements (`<a>` and `<button>`) required explicit focus-visible classes (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red`) for proper keyboard navigation visibility, as native outlines were insufficient.
**Action:** Always verify that interactive elements in dynamically injected overlays receive explicit Tailwind focus classes to ensure keyboard accessibility.
