## 2026-10-05 - Wrap Button Text for Dynamic JS Updates with SVGs
**Learning:** When a button contains inline SVGs (like a loading spinner), updating its `.textContent` directly will destroy the child SVG elements.
**Action:** Wrap the button text in a `<span>` and target the span's `.textContent` when applying dynamic text updates.
