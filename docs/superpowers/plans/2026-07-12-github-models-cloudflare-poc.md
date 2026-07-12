# GitHub Models via Cloudflare AI Gateway PoC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a disabled-by-default, admin-authenticated Cloudflare Pages Function PoC that routes approved GitHub Models requests through a Cloudflare AI Gateway custom provider.

**Architecture:** The Astro site remains static. A new Pages Function delegates request validation and upstream calling to a focused library module. GitHub credentials stay in the Cloudflare AI Gateway custom-provider credential store; the Pages project receives only gateway identifiers, an AI Gateway auth token, and a separate PoC access token.

**Tech Stack:** Astro 6, Cloudflare Pages Functions, TypeScript 5, Zod 3, Vitest 4, native `fetch`.

## Global Constraints

- Repository: `HSBHexagon/hsb-boden`.
- Branch only: `agent/github-models-cloudflare-poc`; never commit directly to `main`.
- No production deploy, DNS change, route change, or live Cloudflare mutation.
- No frontend integration and no customer, lead, CRM, or form data.
- PoC must return 404 unless `AI_POC_ENABLED=true`.
- PoC must require `Authorization: Bearer <AI_POC_ACCESS_TOKEN>`.
- Allowed models only: `openai/gpt-5`, `deepseek/DeepSeek-V3-0324`, `meta/Llama-4-Scout-17B-16E-Instruct`.
- GitHub Models token is stored in the Cloudflare AI Gateway custom-provider credential, never in Pages environment variables or repository files.
- No new dependencies.
- Logs must never include prompts, responses, bearer tokens, or personal data.

---

### Task 1: Architecture decision and operational boundary

**Files:**
- Create: `docs/adr/ADR-0001-github-models-cloudflare-poc.md`
- Modify: `docs/cloudflare/AI_GATEWAY_FUTURE_ARCHITECTURE.md`

**Interfaces:**
- Consumes: Current Pages deployment architecture and project security gates.
- Produces: Approved PoC boundary, required environment variable names, manual Cloudflare setup and rollback path.

- [ ] Document the decision, alternatives, security model and non-production scope.
- [ ] Record that the prior `future-only` status is superseded only for this isolated PoC branch.
- [ ] Keep production activation explicitly approval-gated.

### Task 2: Write failing behavior tests

**Files:**
- Create: `tests/githubModelsPoc.test.ts`
- Test: `tests/githubModelsPoc.test.ts`

**Interfaces:**
- Consumes: `handleGithubModelsPoc(request, env, fetchImpl)` planned in Task 3.
- Produces: Executable contract for disabled mode, auth, validation, gateway routing and sanitized errors.

- [ ] Add a test proving disabled mode returns 404 without calling upstream.
- [ ] Add a test proving missing or wrong access token returns 401.
- [ ] Add a test proving unsupported models return 400.
- [ ] Add a test proving a valid request uses the configured custom-provider gateway URL and safe headers.
- [ ] Add a test proving upstream failures return a sanitized 502.
- [ ] Push the test-only state and confirm PR CI fails because the implementation module does not exist.

### Task 3: Implement the minimal secure client/handler

**Files:**
- Create: `src/lib/githubModelsPoc.ts`
- Test: `tests/githubModelsPoc.test.ts`

**Interfaces:**
- Produces: `handleGithubModelsPoc(request: Request, env: GithubModelsPocEnv, fetchImpl?: typeof fetch): Promise<Response>`.

- [ ] Add strict Zod validation and the three-model allowlist.
- [ ] Enforce disabled-by-default behavior and constant-work bearer comparison.
- [ ] Validate required Cloudflare identifiers and tokens without logging values.
- [ ] Enforce a 16 KiB request limit and a 15-second upstream timeout.
- [ ] Route through `/custom-github-models/inference/chat/completions` with `cf-aig-authorization` and caching disabled.
- [ ] Return sanitized errors and structured metadata-only logs.
- [ ] Confirm the focused test suite passes in CI.

### Task 4: Add the Cloudflare Pages Function wrapper

**Files:**
- Create: `functions/api/github-models.ts`

**Interfaces:**
- Consumes: `handleGithubModelsPoc` from Task 3.
- Produces: Pages route `/api/github-models` with POST-only behavior.

- [ ] Export `onRequestPost` and delegate to the handler.
- [ ] Return 405 for GET, PUT, DELETE and OPTIONS without enabling browser CORS.
- [ ] Confirm `npm run check` and `npm run build` pass in CI.

### Task 5: Document non-secret configuration

**Files:**
- Modify: `.env.example`
- Modify: `docs/cloudflare/AI_GATEWAY_FUTURE_ARCHITECTURE.md`

**Interfaces:**
- Produces: Exact non-secret variable names and manual dashboard checklist.

- [ ] Add placeholders for `AI_POC_ENABLED`, `AI_POC_ACCESS_TOKEN`, `CF_ACCOUNT_ID`, `CF_AI_GATEWAY_ID`, and `CF_AIG_TOKEN`.
- [ ] Document custom provider slug `github-models` and base URL `https://models.github.ai`.
- [ ] Document that the provider credential requires GitHub `models:read` only.
- [ ] Document rollback: disable flag, remove Pages secrets, delete custom provider, delete branch/close PR.

### Task 6: Final verification and handoff

**Files:**
- No additional production files.

- [ ] Verify PR checks for test, check, build, security and preview deployment.
- [ ] Confirm no secret values are present in the diff.
- [ ] Keep the PR as draft and do not merge or deploy.
