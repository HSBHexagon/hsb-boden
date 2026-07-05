## 2026-07-05 - [React Removal for Zero-JS Hydration]
**Learning:** Even if only one component uses `client:visible`, Astro includes the entire framework runtime (React, 140KB) in a `client.js` bundle. Migrating a single interactive form to vanilla JS allowed removing the entire framework dependency.
**Action:** Always check `client.js` size and grep for `client:` directives. If interactivity is low (forms, toggles), prefer vanilla JS in Astro `<script>` tags to eliminate framework overhead.

## 2026-07-05 - [Astro-6 Cloudflare Adapter Cutover-Bug]
**Learning:** The Astro-6 Cloudflare adapter generates a flattened `dist/server/wrangler.json` from the top-level wrangler.toml. This causes `wrangler deploy --env` to be ignored if the top-level (preview) doesn't have matching environment blocks.
**Action:** Use explicit flags `--name <worker-name> --var ENVIRONMENT:<env>` in CI workflows to bypass the adapter's configuration flattening and ensure correct environment delivery.
