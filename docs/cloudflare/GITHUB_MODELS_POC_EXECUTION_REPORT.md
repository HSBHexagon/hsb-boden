# GitHub Models × Cloudflare AI Gateway PoC — Execution Report

- **Date:** 2026-07-12
- **Final state:** `preview-poc-configured-tested-disabled`
- **Inference state:** `blocked-custom-provider-forwarding`
- **Scope:** isolated Cloudflare Pages Preview only; no production deployment,
  DNS change, WordPress change, CRM change, or live-site mutation

This report records only verified results from the controlled Preview test
window. It intentionally omits credentials, Secret Store identifiers, caller
tokens, prompts, and raw provider responses.

## Final Preview state

| Item | Verified final value |
|---|---|
| Pages project | `hsb-boden` |
| Branch | `agent/github-models-cloudflare-poc` |
| Final deployment | `https://9fb64336.hsb-boden.pages.dev` |
| Branch alias | `https://agent-github-models-cloudfla-2656.hsb-boden.pages.dev` |
| Home page | `GET /` returned `200` with `x-robots-tag: noindex` |
| PoC gate | Preview `AI_POC_ENABLED=false` |
| Production configuration | No PoC variables; production retained only `LEAD_WEBHOOK_URL` |

The temporary enabled test window was closed before the final deployment. The
final disabled route behavior was verified on the deployment above:

| Method | Final result |
|---|---|
| `GET` | `404`, `not_found` |
| `HEAD` | `404` with an empty response body |
| `PUT` | `404`, `not_found` |
| `PATCH` | `404`, `not_found` |
| `DELETE` | `404`, `not_found` |
| `OPTIONS` | `404`, `not_found` |
| `POST` | `404`, `not_found` |

The disabled feature gate runs before the method check. When the Preview gate
was temporarily enabled, only `POST` was accepted; all other methods returned
`405` and no browser CORS surface was enabled.

## Verified Cloudflare configuration

The Preview-only PoC used the following non-secret configuration shape:

| Component | Verified state |
|---|---|
| AI Gateway | `hsb-boden-ai`; authenticated; `collect_logs=false`; `cache_ttl=0` |
| Custom provider | `github-models`; base URL `https://models.github.ai`; enabled |
| Provider credential | Active Cloudflare Secret Store key scoped to `ai_gateway` |
| Provider config | Default alias configured for the custom provider |
| Pages Preview PoC variables | `AI_POC_ENABLED`, `AI_POC_ACCESS_TOKEN`, `CF_ACCOUNT_ID`, `CF_AI_GATEWAY_ID`, `CF_AIG_TOKEN` |
| Pages Production PoC variables | No PoC variables configured |

The repository never receives the GitHub Models credential. The runtime uses
the Cloudflare provider-specific route:

```text
https://gateway.ai.cloudflare.com/v1/{account_id}/hsb-boden-ai/custom-github-models/inference/chat/completions
```

Caching is disabled both at gateway level and for the request with
`cf-aig-skip-cache: true`.

## Model and inference findings

The initial preferred model `openai/gpt-5` appeared in the GitHub Models
catalog but a direct, credentialed GitHub Models inference call returned the
safe error classification `unavailable_model`. It was therefore not usable for
this test.

The first available model from the existing approved allowlist,
`deepseek/deepseek-v3-0324`, was verified directly against GitHub Models with
a synthetic request and returned `200`. The response content was not recorded.
The allowlist spelling was corrected test-first to match the catalog identifier
exactly; no additional model was introduced.

Despite the direct GitHub success, the documented Cloudflare custom-provider
route returned a GitHub-shaped `404` for that allowed fallback model in both
tested credential modes:

- provider BYOK/default-alias configuration only; and
- a transient, in-memory inline provider-authentication test.

The enabled Pages route consequently returned its intentional sanitized
`502 upstream_unavailable` response for valid requests. This isolates the
remaining blocker to Cloudflare custom-provider forwarding compatibility or a
Cloudflare provider defect, not to the GitHub credential, model catalog, or
Pages request validation.

No successful inference through Cloudflare AI Gateway was observed. Therefore
the warm-up plus three-request performance phase was not completed and no
latency statistics are reported. Failure-response timings are not meaningful
inference performance measurements.

## Enabled-window negative checks

During the temporary Preview enablement, the following boundary checks passed:

| Check | Result |
|---|---|
| Missing internal bearer token | `401 unauthorized` |
| Wrong internal bearer token | `401 unauthorized` |
| Malformed JSON | `400 invalid_json` |
| Model outside allowlist | `400 validation_failed` |
| Request body above 16 KiB | `413 payload_too_large` |
| Valid request with upstream forwarding failure | `502 upstream_unavailable` without upstream body exposure |

Gateway log collection was configured as disabled. Repository logging records
only metadata such as result, model, duration, and upstream status; it does not
record prompts, responses, or credentials.

## Verification performed

The final local verification completed successfully:

| Command | Verified result |
|---|---|
| `npm run test:run` | 73/73 tests passed |
| `npm run check` | 0 errors, 0 warnings, 0 hints |
| `npm run build` | 35 pages built successfully |
| `npm run deploy:dry-run` | Worker compilation succeeded |

## Required next step

Keep the PoC disabled. A future test window may be opened only after the
Cloudflare custom-provider forwarding discrepancy is resolved and the exact
same Preview-only checks are repeated: disabled gate, caller authentication,
input validation, one successful synthetic inference, and a warm-up plus three
sequential measurements. Production remains out of scope and approval-gated.
