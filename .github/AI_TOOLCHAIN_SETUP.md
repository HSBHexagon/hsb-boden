# AI Toolchain Setup — HSB Boden

This repository uses a guarded AI review and agent workflow setup. The configuration is optimized for security, reproducibility, low noise, and predictable cost rather than maximizing model calls.

## Installed workflows

### `.github/workflows/ai-pr-review.yml`

- Direct OpenAI review through the Responses API
- Direct Gemini review through the Interactions API
- No third-party AI review action and no checkout or execution of pull request code
- Exact `/ai-review` command for pull requests
- `/ai-review` is accepted only from `OWNER`, `MEMBER`, or `COLLABORATOR`
- Pull request content is treated as untrusted data to reduce prompt-injection risk
- Sticky review comments are updated instead of posting duplicates
- AI review is advisory; deterministic CI, QA, and security checks remain authoritative
- No GitHub Models dependency because GitHub Models is retired on July 30, 2026
- No per-PR model evaluation matrix

### `.github/workflows/copilot-setup-steps.yml`

- Required setup workflow for GitHub Copilot coding agent
- Validated automatically only when the setup workflow itself changes
- Uses least-privilege `contents: read`

### `.github/workflows/jules-auto-merge.yml`

- Uses GitHub native auto-merge and squash merge
- Never auto-merges merely because a pull request was authored by a bot
- `jules-approved` authorizes auto-merge only for `google-labs-jules[bot]`
- `auto-merge` authorizes auto-merge for another explicitly reviewed pull request
- Only an actor with `write`, `maintain`, or `admin` permission can authorize auto-merge
- Draft, closed, and non-`main` pull requests are rejected
- The expected head SHA is verified before auto-merge is enabled
- Every new commit disables auto-merge and removes approval labels, so fresh approval is required
- Pull request code is never checked out or executed in the privileged `pull_request_target` workflow

## Repository secrets

At least one provider secret is required for AI review. If neither secret exists, the workflow remains green and reports that no provider is configured.

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

## Repository variables

### Provider selection

- `AI_REVIEW_PROVIDER`
  - `auto` — default; use OpenAI when configured, otherwise Gemini
  - `openai` — use only OpenAI
  - `gemini` — use only Gemini
  - `both` — run both providers and incur both providers' usage
  - `none` — disable AI review without deleting the workflow

### Model selection

- `OPENAI_REVIEW_MODEL` — default: `gpt-5.6-luna`
- `OPENAI_REASONING_EFFORT` — default: `medium`
- `GEMINI_REVIEW_MODEL` — default: `gemini-3.5-flash`

The OpenAI default is the cost-sensitive GPT-5.6 option because pull-request review is a potentially high-volume workload. Override it with `gpt-5.6-terra` when more review depth is worth the additional cost.

## Auto-merge prerequisite

GitHub native auto-merge waits only for requirements configured in branch protection or repository rulesets. Configure required CI, QA, security, and review checks for `main`. Without required checks, an approved pull request can merge immediately.

## Guardrails

- No production deployment changes
- No DNS changes
- No secret values in the repository, issues, pull requests, comments, or documentation
- No unreviewed bot auto-merge
- No stale approval after a pull request changes
- No checkout or execution of pull request code in privileged workflows
