
## 2024-07-25 - Native Focus and Grid Labels
**Learning:** Native focus outlines on interactive elements in this app are often insufficient or stripped entirely by default styles. Additionally, appending inline visual indicators (like required asterisks) directly next to label text can cause CSS grid layouts to split the text and asterisk onto separate rows.
**Action:** Always apply explicit Tailwind `focus-visible` classes (e.g., `focus-visible:ring-1 focus-visible:ring-hsb-red focus-visible:outline-none`) to interactive elements. Wrap label text and inline indicators together within a `<span>` container to prevent grid-induced wrapping issues.
