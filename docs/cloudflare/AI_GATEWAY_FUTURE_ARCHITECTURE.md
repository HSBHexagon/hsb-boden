# AI Gateway — HSB-Boden / HEXAFLOOR

Status: `PREVIEW_POC_CONFIGURED_TESTED_DISABLED`

Inference status: `BLOCKED_CUSTOM_PROVIDER_FORWARDING`

Stand: 2026-07-12

Canonical Cloudflare website readiness: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
PoC execution evidence: `docs/cloudflare/GITHUB_MODELS_POC_EXECUTION_REPORT.md`
Architecture decision: `docs/adr/ADR-0001-github-models-cloudflare-poc.md`

## Current boundary

The production website has no active AI feature. The active production
architecture remains a static Astro site on Cloudflare Pages with `/api/lead`
for lead intake and the existing CRM-Light destination. No AI model receives
lead, customer, CRM, or form data.

The GitHub Models work is restricted to branch
`agent/github-models-cloudflare-poc` and draft PR #74. It was configured and
tested on a Cloudflare Pages Preview deployment only. The final Preview state
is disabled; there was no production deployment, production Pages-variable
mutation, DNS change, WordPress change, CRM change, or merge.

## Verified Preview configuration

| Component | Verified state |
|---|---|
| Pages project | `hsb-boden` |
| Final Preview deployment | `https://9fb64336.hsb-boden.pages.dev` |
| Preview gate | `AI_POC_ENABLED=false` |
| Production PoC variables | None; production retained only `LEAD_WEBHOOK_URL` |
| AI Gateway | `hsb-boden-ai`, authenticated, `collect_logs=false`, `cache_ttl=0` |
| Custom provider | `github-models`, enabled, base URL `https://models.github.ai` |
| Provider credential | Active Secret Store key scoped to `ai_gateway` |
| Provider configuration | Default alias configured |

For the PoC, Preview contains only the gate, caller token, Cloudflare account
identifier, gateway identifier, and scoped AI Gateway runtime token. The GitHub
Models credential is stored in Cloudflare's provider credential flow; it is not
a Pages variable and is never stored in the repository, `.env`, `.dev.vars`,
issue, PR text, or logs.

## Request path and controls

```text
Authorized internal caller
  -> Cloudflare Pages Function /api/github-models
  -> Cloudflare AI Gateway custom provider github-models
  -> GitHub Models inference API
```

The Pages Function calls the provider-specific Cloudflare endpoint:

```text
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/custom-github-models/inference/chat/completions
```

Implemented controls:

| Control | Current behavior |
|---|---|
| Default state | Every method returns `404` unless `AI_POC_ENABLED=true` |
| Enabled methods | Only `POST`; non-POST methods return `405` |
| Caller authentication | Separate internal bearer token |
| Model access | Explicit three-model allowlist |
| Request size | 16 KiB maximum |
| Response size | 256 KiB maximum |
| Message count | 1–12 |
| Message length | 1–4,000 characters |
| Output tokens | 1–2,000 |
| Temperature | 0–1 |
| Upstream timeout | 15 seconds |
| Gateway cache | Gateway `cache_ttl=0` and request header `cf-aig-skip-cache: true` |
| Logging | Metadata only; no prompt, response, credential, or bearer-token logging |
| Browser access | No CORS support |

The approved allowlist is:

- `openai/gpt-5`
- `deepseek/deepseek-v3-0324`
- `meta/Llama-4-Scout-17B-16E-Instruct`

The DeepSeek identifier was corrected test-first to the exact current catalog
casing. No new model was added.

## Completed Preview checks

The final Preview URL returned `200` for the home page with
`x-robots-tag: noindex`. With the final disabled flag, `GET`, `HEAD`, `PUT`,
`PATCH`, `DELETE`, `OPTIONS`, and `POST` to `/api/github-models` each returned
`404`; the `HEAD` response had no body.

During the temporary enabled test window, the following negative controls were
verified: missing or wrong caller token (`401`), malformed JSON (`400`),
non-allowlisted model (`400`), and over-size request (`413`). Valid requests
reached the Pages handler but returned its sanitized `502 upstream_unavailable`
response when the custom-provider call failed.

The final local gates passed:

```text
npm run test:run       73/73 passed
npm run check          0 errors, 0 warnings, 0 hints
npm run build          35 pages built successfully
npm run deploy:dry-run Worker compilation succeeded
```

## Inference blocker

The preferred `openai/gpt-5` was present in the GitHub Models catalog but a
direct synthetic inference request returned the safe classification
`unavailable_model`. The first existing allowed fallback,
`deepseek/deepseek-v3-0324`, succeeded directly against GitHub Models with
`200`; its response content was not retained.

The exact Cloudflare custom-provider endpoint returned a GitHub-shaped `404`
for the allowed fallback model in two independent credential modes: the
configured BYOK/default-alias path and a transient in-memory inline
provider-authentication test. This leaves a reproducible Cloudflare
custom-provider forwarding incompatibility or defect as the remaining blocker.
It is not evidence of a failed GitHub credential, unavailable fallback model,
or Pages validation defect.

No successful inference through Cloudflare AI Gateway was observed. The
performance warm-up and three sequential inference measurements were therefore
not performed; failure timings are not reported as inference latency.

## Next permitted action

Keep the Preview route disabled. Reopen a Preview-only test window only after
the Cloudflare custom-provider forwarding issue is resolved. The required
re-test sequence is: disabled route check, enabled authentication and
validation checks, one successful synthetic inference, warm-up plus three
sequential measurements, then a final disabled deployment and `404` check.

Production activation, frontend integration, CRM use, lead scoring, automated
outreach, DNS changes, and changes to `/api/lead` remain out of scope and
require separate approval.

## Rollback options

The immediate runtime rollback is already in effect: `AI_POC_ENABLED=false` in
Preview. If the experiment is abandoned, an owner may additionally remove the
Preview variables, disable or delete the custom provider, revoke the scoped
tokens, and close draft PR #74. None of those actions changes the website,
lead endpoint, CRM, DNS, or production domain.

## Future use cases requiring a separate decision

| Use case | Trigger | Current status |
|---|---|---|
| Internal lead scoring assistant | Manual scoring becomes operationally slow | Not approved |
| Follow-up draft assistant | Operators request controlled drafting | Not approved |
| Internal product-document search | Knowledge-base project approved | Not approved |
| Customer-facing chatbot | Product, privacy and legal approval | Not approved |
