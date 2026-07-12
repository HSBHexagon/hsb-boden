# AI_GATEWAY_FUTURE_ARCHITECTURE — HSB-Boden / HEXAFLOOR

Status: `isolated-poc-code-implemented-not-configured-not-active`
Stand: 2026-07-12

Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
Architecture decision: `docs/adr/ADR-0001-github-models-cloudflare-poc.md`
Implementation plan: `docs/superpowers/plans/2026-07-12-github-models-cloudflare-poc.md`

---

## Current production boundary

The production website has no active AI feature. The active architecture remains:

- static Astro 6 site on Cloudflare Pages;
- Pages Function `/api/lead` for website lead intake;
- Google Apps Script and Google Sheets CRM-Light as the verified lead destination;
- no AI inference in the lead path;
- no runtime use of customer, lead or CRM data by an AI model.

The GitHub Models work exists only on branch `agent/github-models-cloudflare-poc` and draft PR #74. It is not merged, configured or active.

---

## Approved isolated PoC

The project owner explicitly approved an isolated proof of concept on 2026-07-12.

```text
Authorized internal caller
  -> POST /api/github-models
  -> Cloudflare AI Gateway custom provider github-models
  -> GitHub Models inference API
```

The implementation is deliberately inert by default:

- `AI_POC_ENABLED` must equal `true` or the route returns 404;
- a separate `AI_POC_ACCESS_TOKEN` bearer token is required;
- there is no frontend caller and no CORS support;
- model names are restricted to a three-model allowlist;
- prompt and response data are not logged;
- AI Gateway caching is disabled;
- no production deployment or merge is authorized by this document.

Allowed PoC models:

- `openai/gpt-5`
- `deepseek/DeepSeek-V3-0324`
- `meta/Llama-4-Scout-17B-16E-Instruct`

---

## Credential model

### Cloudflare Pages environment

Configure only as encrypted server-side values:

```text
AI_POC_ENABLED=false
AI_POC_ACCESS_TOKEN=<generated internal bearer token>
CF_ACCOUNT_ID=<Cloudflare account identifier>
CF_AI_GATEWAY_ID=hsb-boden-ai
CF_AIG_TOKEN=<scoped AI Gateway token>
```

### Cloudflare AI Gateway custom provider

```text
Provider slug: github-models
Base URL: https://models.github.ai
Credential header: Authorization
Credential value: Bearer <fine-grained GitHub token>
Required GitHub permission: models:read only
```

The GitHub Models token must not be placed in Pages variables, `.env`, `.dev.vars`, repository files, GitHub issues, PR text or logs.

---

## Manual Cloudflare setup gate

No Cloudflare setting was changed by the repository implementation. An authorized operator must perform these dashboard steps before any live PoC test:

1. Open Cloudflare AI Gateway.
2. Create or select gateway `hsb-boden-ai`.
3. Create custom provider `github-models` with base URL `https://models.github.ai`.
4. Store a fine-grained GitHub token with `models:read` only in the provider credential configuration.
5. Create a scoped AI Gateway authentication token.
6. Add the five Pages values in a non-production or preview environment first.
7. Keep `AI_POC_ENABLED=false` until a specific test window is approved.
8. Use synthetic prompts only; do not use leads, CRM records, customer data or confidential project documents.

Expected provider-specific route used by the Pages Function:

```text
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/custom-github-models/inference/chat/completions
```

---

## Implemented controls

| Control | Implementation |
|---|---|
| Default state | 404 unless `AI_POC_ENABLED=true` |
| Caller authentication | Separate bearer token |
| Allowed methods | POST only |
| Model access | Explicit allowlist |
| Request size | 16 KiB maximum |
| Response size | 256 KiB maximum |
| Message count | 1–12 |
| Message length | 1–4,000 characters |
| Output tokens | 1–2,000 |
| Upstream timeout | 15 seconds |
| AI Gateway cache | Disabled with `cf-aig-cache-ttl: 0` |
| Logging | Timestamp, result, model, duration and upstream status only |
| Error handling | Sanitized client responses; no upstream body exposure |

---

## Explicitly out of scope

- customer-facing chatbot;
- lead scoring from real CRM data;
- automated outreach or email generation;
- automatic follow-up decisions;
- website content generation at runtime;
- AI Search, Vectorize, D1, R2 or Workers AI bindings;
- production activation;
- changes to `/api/lead`;
- DNS, routes, apex redirect or production deployment.

Any of these requires a separate ADR, privacy review and owner approval.

---

## Verification gate

Before this PoC can be considered code-ready, the draft PR must show successful:

```bash
npm run test:run
npm run check
npm run build
```

The preview deployment may compile the route, but the route must remain disabled without environment configuration.

A real inference test is a separate manual step and must verify:

- disabled mode returns 404;
- missing/invalid bearer token returns 401 when enabled;
- one synthetic request succeeds through AI Gateway;
- AI Gateway logs contain no credential or prompt leakage;
- disabling the flag immediately closes the route.

---

## Rollback

1. Set `AI_POC_ENABLED=false` or remove it.
2. Remove the PoC Pages environment values.
3. Delete or disable custom provider `github-models`.
4. Revoke both the GitHub token and the Cloudflare AI Gateway token.
5. Close draft PR #74 and delete branch `agent/github-models-cloudflare-poc` if abandoned.

Rollback does not touch the website, lead endpoint, CRM, DNS or production domain.

---

## Future use cases requiring a separate decision

| Use case | Trigger | Current status |
|---|---|---|
| Internal lead scoring assistant | Manual scoring becomes operationally slow | Not approved |
| Follow-up draft assistant | Operators request controlled drafting | Not approved |
| Internal product-document search | Knowledge-base project approved | Not approved |
| Customer-facing chatbot | Product, privacy and legal approval | Not approved |
