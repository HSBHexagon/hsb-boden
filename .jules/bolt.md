## 2026-07-06 - LCP Optimization for Hero Images
**Learning:** Found that hero images (LCP candidates) in `branchen` and `leistungen` pages were incorrectly marked with `loading="lazy"`. This delays the Largest Contentful Paint because the browser waits for layout computation before requesting the image.
**Action:** Always verify that critical above-the-fold images use `fetchpriority="high" loading="eager" decoding="async"` to prioritize loading.

## 2026-07-07 - Wrangler CLI authentication in GitHub Actions
**Learning:** The `cloudflare/wrangler-action` fails in non-interactive CI environments when the token is only provided via `with: apiToken`. It explicitly requires the `CLOUDFLARE_API_TOKEN` to be set in the `env` block.
**Action:** Always provide `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` via `env` in `.github/workflows` when using `wrangler-action`.
