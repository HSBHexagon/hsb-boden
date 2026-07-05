## 2026-07-05 - [React Removal for Zero-JS Hydration]
**Learning:** Even if only one component uses `client:visible`, Astro includes the entire framework runtime (React, 140KB) in a `client.js` bundle. Migrating a single interactive form to vanilla JS allowed removing the entire framework dependency.
**Action:** Always check `client.js` size and grep for `client:` directives. If interactivity is low (forms, toggles), prefer vanilla JS in Astro `<script>` tags to eliminate framework overhead.
