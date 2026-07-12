# AI_GATEWAY_FUTURE_ARCHITECTURE — HSB-Boden / HEXAFLOOR

Status: `ai-gateway-future-only-not-planned-for-current-launch`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No AI Gateway created. No AI feature built. No Cloudflare AI products activated.**
This document is a forward-looking architecture note only.
It does not represent any planned or approved near-term work.

Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`

---

## Current AI Usage in HSB-Boden

None. The current production system is:
- Cloudflare Worker serving an Astro 6 static site
- Lead intake form → `/api/lead` → Apps Script → Google Sheets CRM-Light
- No AI inference, no LLM calls, no AI-generated content at runtime

---

## What AI Gateway Would Enable (Future Only)

Cloudflare AI Gateway is a proxy/observability layer for AI API calls. It provides:
- Request/response logging for LLM calls
- Rate limiting and cost control per model
- Caching of identical prompts (reduces cost)
- Fallback routing between AI providers
- No model training or fine-tuning

**AI Gateway is only relevant if HSB-Boden adds an AI feature (e.g., smart lead scoring,
AI-assisted response generation, or an internal assistant).** There is no such feature
planned or approved for the current launch.

---

## Potential Future Use Cases (No Commitment)

| Use Case | Trigger | Priority |
|----------|---------|---------|
| Internal lead scoring assistant | >200 leads in CRM, manual scoring slow | Low |
| AI-generated follow-up draft templates | JORDI or Joel requests it | Low |
| AI search over product docs | Internal knowledge base decision | Low |
| Customer-facing chatbot | Explicit product decision + legal review | Very low |

None of these use cases are approved, planned, or funded.

---

## If AI Gateway Is Activated in the Future

### Setup Steps

1. Cloudflare Dashboard → **AI → AI Gateway → Create Gateway**
2. Name: `hsb-boden-ai`
3. Enable logging (costs apply at scale; verify current plan pricing)
4. Replace direct AI API calls in Worker with AI Gateway endpoint URL:
   ```
   https://gateway.ai.cloudflare.com/v1/{account_id}/hsb-boden-ai/{provider}/{model}
   ```
5. Keep AI API keys as Worker secrets — never hardcoded

### Supported Providers (As of Mid-2026)

- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet, Claude Haiku 4.5)
- Google (Gemini Pro)
- Workers AI (Cloudflare's own hosted models — Llama, Mistral, etc.)

### Workers AI (Lowest Cost Option)

Cloudflare Workers AI runs inference directly on Cloudflare's edge network.
No external API key required. Billed per neuron token.
Suitable for: simple classification, embedding generation, basic summarization.
Not suitable for: complex reasoning, long document analysis, customer-facing chat (quality risk).

---

## Cloudflare AI Search (Future Only)

Cloudflare AI Search (formerly Vectorize + Workers AI embeddings) enables semantic search
over an embedded document corpus. Use cases:
- Internal product knowledge base search
- Semantic lead matching (very advanced, not required)

**Not planned. Not built. Not approved.** Document here for architectural awareness only.

---

## Boundary with Current Work

| Item | Status |
|------|--------|
| AI Gateway created | No |
| AI feature in Worker code | No |
| LLM API calls in any Worker | No |
| Workers AI binding in `wrangler.toml` | No |
| AI-generated content in production | No |

If any AI feature is added, a separate ADR (Architecture Decision Record) must be written,
reviewed by Joel, and approved before implementation.

---

## Stop Condition

If this document is referenced during a launch session, stop.
AI Gateway has no relevance to the current DNS-triggered go-live.
Focus on `docs/PHASE_C_CUTOVER_RUNBOOK.md` and `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`.
