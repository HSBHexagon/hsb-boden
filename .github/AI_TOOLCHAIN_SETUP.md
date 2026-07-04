# AI Toolchain Setup — HSB Boden

This repository includes a maximum practical AI toolchain setup that still respects existing guardrails.

## Installed workflows

- `.github/workflows/ai-pr-review.yml`
  - GitHub Models review via `GITHUB_TOKEN` and `models: read`
  - Gemini CLI review via `GEMINI_API_KEY`
  - ChatGPT CodeReview via `OPENAI_API_KEY`
  - Evaluation matrix for GitHub Models
  - `/ai-review` issue comment trigger for PRs

- `.github/workflows/copilot-setup-steps.yml`
  - Required setup workflow for GitHub Copilot coding agent

## Manual secrets still required

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

## No-go reminders

- No production deploy changes
- No DNS changes
- No auto-merge
- No secret values in repo, issues, PRs, or docs
