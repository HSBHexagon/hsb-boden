# PowerAgent Full-Stack Audit — 2026-07-18

## Scope

Repository, SEO, Analytics, Cloudflare Pages/Functions, Supabase and Vercel
for `HSBHexagon/hsb-boden`. Production deployment remains approval-gated.

## Executive summary

| Priority | Finding | Resolution |
| --- | --- | --- |
| P0 | A scheduled workflow exported full Notion databases into the public repository and pushed directly to `main`. | Workflow removed. No database export is stored in Git. |
| P1 | A `SECURITY DEFINER` Supabase helper was executable by `anon` and `authenticated`. | Execution revoked from `PUBLIC`, `anon` and `authenticated`; Supabase Security Advisor re-run with zero findings. |
| P1 | Three low-severity npm advisories affected Astro/esbuild and an unused Cloudflare adapter. | Unused adapter removed; Astro 7.1.1 and Vite 8.1.5 pinned. `npm audit`: zero vulnerabilities. |
| P1 | Cloudflare Pages Function responses did not receive the static `_headers` policy. | Lead API now sets `no-store`, `nosniff` and `no-referrer` itself. |
| P1 | Preview/project domains could compete with the canonical domain in search. | Host-specific `X-Robots-Tag: noindex, nofollow` rules added. |
| P2 | Duplicate Search Console verification tags and incomplete social metadata. | One current verification tag remains; Open Graph and Twitter metadata completed. |
| P2 | Sitemap emitted ignored priority/change-frequency values and an unverifiable build-date `lastmod`. | Sitemap now emits only canonical URLs from the central page registry. |
| P2 | Telephone links could contain the international optional-zero notation. | All affected links now derive a valid `tel:` value from central site data. |
| P2 | Notion Actions used mutable action tags, an unpinned SDK install and the wrong SHA for `workflow_run`. | Action SHAs and compatible SDK version pinned; unused checkout/input removed; originating deploy SHA used. |

## Platform assessment

### GitHub

Nine non-draft pull requests with successful required checks were squash-merged:
`#75`, `#76`, `#77`, `#78`, `#109`, `#115`, `#116`,
`#119` and `#122`. PRs `#117` and `#118` became conflicted after the
preceding merges; their still-valid SEO and telephone fixes were reconciled in
this change. Draft, conflicted, pending and failing PRs were not force-merged.

All remaining workflow `uses:` references are pinned to commit SHAs. A
high-confidence repository secret scan found no matching credentials or private
keys.

### SEO

Canonical URLs, hreflang, robots, JSON-LD and static route generation are
present. The generated homepage contains one Search Console verification tag,
complete social cards and no external Google Tag script before consent. The
generated sitemap contains the project-flow page and no fabricated `lastmod`.

Google documents that `priority` and `changefreq` are ignored and that
`lastmod` should only be used when it is consistently accurate:
<https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap>.

### Analytics

The current implementation uses Basic Consent: GA4 is loaded only after active
analytics consent, and lead events pass through a field allowlist before being
sent. The static HTML artifact contains no direct Google Tag Manager request.
Google's consent guidance:
<https://developers.google.com/tag-platform/security/guides/consent>.

### Cloudflare

Cloudflare Pages is the canonical runtime. Static headers include HSTS, CSP,
frame denial, MIME sniffing protection, permissions policy and immutable hashed
assets. Pages Functions set their own security/cache headers because static
`_headers` rules do not apply to Function responses:
<https://developers.cloudflare.com/pages/configuration/headers/>.

The static build and local Pages Functions bundle succeed. The final read-only
`wrangler pages deployment list` account query could not run in this session
because no `CLOUDFLARE_API_TOKEN` was available. No production deployment was
attempted.

### Supabase

Project `xviyivvuuqyzyatanufq` is healthy in `eu-west-1`, PostgreSQL 17.6,
with no public tables. The Security Advisor initially reported that
`public.rls_auto_enable()` (a `SECURITY DEFINER` event-trigger helper) was
executable by public client roles. Migration
`restrict_rls_auto_enable_execution` revoked those grants. Security and
Performance Advisors now return zero findings.

References:
<https://supabase.com/docs/guides/database/database-advisors> and
<https://www.postgresql.org/docs/current/sql-revoke.html>.

### Vercel

The connected team currently has no Vercel projects. The repository and live
headers identify Cloudflare Pages as the active platform. Keeping Vercel out of
the deployment path avoids dual-host drift.

## Verification evidence

- `npm run test:run`: 13 files, 124 tests passed.
- `npm run check`: 102 files, 0 errors, 0 warnings, 0 hints.
- `npm run build`: 37 static pages built.
- `wrangler pages functions build`: Worker compiled successfully.
- `npm audit --audit-level=low`: 0 vulnerabilities.
- All 12 GitHub workflow files parsed as YAML.
- All workflow action references SHA-pinned.
- Generated-artifact SEO/consent/header assertions passed.
- High-confidence local secret-pattern scan: no matches.

## Remaining operational controls

1. Let the pull-request preview and required GitHub checks complete.
2. Merge only when GitHub reports the branch mergeable and required checks green.
3. Run the approval-gated production workflow manually after preview acceptance.
4. Verify the deployed canonical page, consent behavior and lead endpoint headers.
5. Re-run the Cloudflare deployment-list/account checks with a scoped API token.
