## 2024-05-18 - Missing Focus Styles in Global CSS
**Learning:** Found that most interactive elements lack explicit keyboard focus styles (`focus-visible:ring`), particularly those not using the primary/secondary button classes, making keyboard navigation difficult to track. Also discovered `lang-suggest-dismiss` button in LanguageSuggest component lacks a descriptive `aria-label`.
**Action:** Always ensure interactive elements have a clear, high-contrast `focus-visible` outline for accessibility.
