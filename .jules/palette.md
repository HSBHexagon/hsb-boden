## 2026-10-03 - Focus States in Dark Headers
**Learning:** In dark mode or inverted headers (like Header.astro with background #161a20), native browser focus rings are often invisible. Explicit `focus-visible:ring-offset-2 focus-visible:ring-offset-[#161a20]` is necessary to guarantee keyboard accessibility visibility over the dark background.
**Action:** Always add explicit ring offsets matching the dark background color when styling inverted header navigations.
