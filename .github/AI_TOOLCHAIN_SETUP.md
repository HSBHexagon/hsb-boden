# AI Toolchain Setup — HSB Boden

This repository uses a guarded AI review and agent workflow setup. The configuration is intentionally optimized for security, reproducibility, low noise, and predictable cost rather than maximizing the number of model calls.

## Installed workflows

### `.github/workflows/ai-pr-review.yml`

- GitHub Models review via `GITHUB_TOKEN` and `models: read`
- Optional Gemini review via `GEMINI_API_KEY`
- Optional OpenAI review via `OPENAI_API_KEY`
- Exact `/ai-review` command for pull requests
- `/ai-review` is accepted only from `OWNER`, `MEMBER`, or `COLLABORATOR`
- Pull request content is treated as untrusted data to reduce prompt-injection risk
- Sticky review comments are updated instead of posting duplicates
- Optional external reviewers skip cleanly when their secret is missing
- No per-PR model evaluation matrix

### `.github/workflows/copilot-setup-steps.yml`

- Required setup workflow for GitHub Copilot coding agent
- Validated automatically only when the setup workflow itself changes
- Uses least-privilege `contents: read`

### `.github/workflows/jules-auto-merge.yml`

- Uses GitHub native auto-merge and squash merge
- Never auto-merges merely because a PR was authored by a bot
- `jules-approved` authorizes auto-merge only for `google-labs-jules[bot]`
- `auto-merge` authorizes auto-merge for another reviewed PR
- Draft, closed, and non-`main` pull requests are rejected
- The expected head SHA is verified before auto-merge is enabled

## Required repository secrets

External reviewers are optional. Without these secrets, their jobs remain green and report that they were skipped.

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

## Optional repository variables

- `GITHUB_MODELS_REVIEW_MODEL` — default: `openai/gpt-4.1`
- `GEMINI_MODEL` — default: `gemini-2.5-pro`
- `GEMINI_CLI_VERSION` — default: `latest`; pin a tested version for full reproducibility
- `OPENAI_REVIEW_MODEL` — default: `gpt-4.1-mini`

## Auto-merge prerequisite

GitHub native auto-merge waits only for requirements configured in branch protection or repository rulesets. Configure required CI, QA, security, and review checks for `main`. Without required checks, an approved pull request can merge immediately.

## Guardrails

- No production deployment changes
- No DNS changes
- No secret values in the repository, issues, pull requests, comments, or documentation
- No unreviewed bot auto-merge
- No checkout or execution of pull request code in the privileged `pull_request_target` auto-merge workflow
