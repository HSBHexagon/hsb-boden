# ADR-0001: GitHub Models via Cloudflare AI Gateway PoC

- **Status:** Approved for isolated PoC branch only
- **Date:** 2026-07-12
- **Decision owner:** HSBHexagon project owner
- **Repository:** `HSBHexagon/hsb-boden`

## Context

The project currently has no runtime AI feature. The website is a static Astro deployment on Cloudflare Pages with server-side Pages Functions. The owner explicitly approved implementing a controlled proof of concept for GitHub Models while retaining Cloudflare as the central runtime and observability layer.

This decision does not authorize production activation, customer-facing AI, automated outreach, CRM processing, or transmission of lead/customer data.

## Decision

Implement a disabled-by-default Pages Function at `/api/github-models` that routes a small allowlist of model requests through a Cloudflare AI Gateway custom provider.

Data flow:

```text
Authorized internal caller
  -> Cloudflare Pages Function /api/github-models
  -> Cloudflare AI Gateway custom provider: github-models
  -> GitHub Models inference API
```

The GitHub Models credential is stored in the Cloudflare AI Gateway custom-provider credential store. It is not stored in the repository and is not required as a Pages project environment variable.

The Pages Function uses:

- `AI_POC_ENABLED`: feature gate; only the exact value `true` enables the route.
- `AI_POC_ACCESS_TOKEN`: separate bearer token for the internal PoC caller.
- `CF_ACCOUNT_ID`: Cloudflare account identifier.
- `CF_AI_GATEWAY_ID`: AI Gateway identifier.
- `CF_AIG_TOKEN`: Cloudflare AI Gateway authentication token.

The custom provider uses:

- Slug: `github-models`
- Base URL: `https://models.github.ai`
- Upstream credential: fine-grained GitHub token with `models:read` only

Allowed models:

- `openai/gpt-5`
- `deepseek/DeepSeek-V3-0324`
- `meta/Llama-4-Scout-17B-16E-Instruct`

## Security constraints

- Route is 404 while disabled.
- Route is POST-only.
- Route requires a separate PoC bearer token.
- Request bodies are limited to 16 KiB.
- Message count and message length are bounded.
- Model names are allowlisted.
- Upstream calls time out after 15 seconds.
- AI Gateway caching is disabled for the PoC.
- Logs contain only timestamp, result, model, duration and upstream status.
- Prompts, responses, tokens, customer data and lead data are never logged.
- No browser CORS support is added.

## Alternatives considered

### Direct browser to GitHub Models

Rejected. It would expose credentials and bypass server-side policy enforcement.

### Pages Function directly to GitHub Models

Rejected for the target architecture. It would bypass Cloudflare AI Gateway observability and central controls.

### Workers AI only

Not selected for this PoC because the requested experiment is specifically GitHub Models. It remains a possible later alternative for low-cost classification.

### Production chatbot or CRM integration

Rejected and out of scope. These require a separate product, privacy and legal decision.

## Operational setup

No Cloudflare setting is changed by this repository branch. Before a live PoC call, an authorized operator must manually:

1. Create or select AI Gateway `hsb-boden-ai`.
2. Create custom provider `github-models` with base URL `https://models.github.ai`.
3. Store the GitHub fine-grained token in the provider credential configuration; permission `models:read` only.
4. Create a scoped AI Gateway auth token.
5. Add the five Pages environment values as encrypted secrets/variables in a non-production environment first.
6. Keep `AI_POC_ENABLED=false` until an explicit test window is approved.

## Rollback

Rollback is immediate and does not affect the website or lead endpoint:

1. Set or leave `AI_POC_ENABLED=false`.
2. Remove the PoC Pages secrets/variables.
3. Delete or disable the `github-models` custom provider.
4. Revoke the GitHub token and Cloudflare AI Gateway token.
5. Close the PR and delete the branch if the experiment is abandoned.

## Consequences

Positive:

- Provider credential remains centralized.
- No frontend dependency or UI is introduced.
- Model access is constrained and observable.
- Removal is isolated and low risk.

Negative:

- Manual Cloudflare dashboard setup is still required.
- The PoC adds an internal API surface that must never be enabled without token configuration.
- GitHub Models free-tier limits remain unsuitable for unbounded production traffic.
