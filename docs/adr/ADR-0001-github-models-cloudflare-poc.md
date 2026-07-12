# ADR-0001: GitHub Models via Cloudflare AI Gateway PoC

- **Status:** Approved for isolated Preview-only PoC; test window closed,
  final route disabled; custom-provider forwarding blocked
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
- Upstream credential: fine-grained GitHub token for GitHub Models (the
  required permission is `models:read`)

Allowed models:

- `openai/gpt-5`
- `deepseek/deepseek-v3-0324`
- `meta/Llama-4-Scout-17B-16E-Instruct`

## Security constraints

- Route is 404 while disabled.
- Route is POST-only.
- Route requires a separate PoC bearer token.
- Request bodies are limited to 16 KiB.
- Message count and message length are bounded.
- Model names are allowlisted.
- Upstream calls time out after 15 seconds.
- AI Gateway caching is disabled for the PoC (`cache_ttl=0` and
  `cf-aig-skip-cache: true`).
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

## Operational state (2026-07-12)

The authorized setup was performed only for the controlled Cloudflare Pages
Preview test window. It does not change production authorization or activate a
customer-facing feature.

- Gateway `hsb-boden-ai` is authenticated with `collect_logs=false` and
  `cache_ttl=0`.
- The enabled custom provider is `github-models` with base URL
  `https://models.github.ai` and an active Secret Store credential scoped to
  `ai_gateway`; its default alias is configured.
- The five PoC Pages values exist only in Preview. Production has no PoC
  variables and retains only `LEAD_WEBHOOK_URL`.
- The final Preview deployment has `AI_POC_ENABLED=false` and the route is
  closed with `404` for every tested method.

The preferred `openai/gpt-5` was catalog-listed but returned
`unavailable_model` in direct synthetic inference. The first existing allowed
fallback, `deepseek/deepseek-v3-0324`, returned `200` directly from GitHub
Models. The exact Cloudflare custom-provider route still returned a
GitHub-shaped `404` in BYOK/default-alias and transient inline-authentication
tests, so successful Gateway inference and performance measurements remain
blocked. The evidence and test boundaries are recorded in
`docs/cloudflare/GITHUB_MODELS_POC_EXECUTION_REPORT.md`.

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

- Cloudflare custom-provider forwarding is not yet proven compatible with
  GitHub Models for this configuration.
- The PoC adds an internal API surface that must never be enabled without token configuration.
- GitHub Models free-tier limits remain unsuitable for unbounded production traffic.
