## 2026-10-01 - Added focus styles to language suggestion banner dismiss button
**Learning:** Dismiss buttons on dynamic notification banners (like `LanguageSuggest`) often lack visible focus indicators because they use bare text styles without native button padding or borders. When users navigate with keyboards, these elements become invisible focus traps.
**Action:** Always ensure that interactive elements on dynamically injected or absolute positioned overlays contain explicit `focus-visible` styling, even if they visually appear as plain text links.
