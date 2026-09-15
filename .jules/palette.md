## 2024-05-20 - [LeadForm required indicators]
**Learning:** HTML5 `required` attribute validation isn't accessible to sighted users without a visual indicator. Also, native focus outlines are insufficient for keyboard navigation.
**Action:** Appended an accessible red asterisk (`<span class="text-hsb-red" aria-hidden="true">*</span>`) wrapped with the label text to prevent grid layout breakage. Added `focus-visible` Tailwind classes to input fields, selects, textareas, checkboxes, and buttons.
