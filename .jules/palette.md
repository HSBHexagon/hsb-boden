## 2024-09-18 - Missing Focus States on Global Buttons
**Learning:** In this application, native buttons and global CSS classes (`.button-primary`, etc) lack built-in focus-visible states, which severely impacts keyboard navigation visibility.
**Action:** Always verify keyboard accessibility (`focus-visible`) when auditing interactive elements in this codebase, and explicitly add focus outline/ring classes or CSS rules.
