# GitHub-Actions-Wert- und Risiko-Matrix — hsb-boden

Stand: 2026-07-12, grep-/API-Audit (alle Actions SHA-gepinnt, 0 ungepinnte `uses:`).

| Workflow | Trigger | Permissions | Wert | Risiko | Bewertung |
|---|---|---|---|---|---|
| quality.yml | push/PR main | contents: read | check+build+test-Gate | gering | KEEP |
| security.yml | push/PR/cron | contents: read (job-level, CodeQL braucht security-events) | CodeQL, Dependency Review, Secret-Suche | gering | KEEP |
| lighthouse.yml | PR | contents: read | Performance-Budgets (.lighthouserc.json) | gering | KEEP |
| ci.yml | push/PR | contents: read | Basis-CI | gering | KEEP (Überlappung mit quality.yml prüfen → Konsolidierungskandidat) |
| deploy-preview.yml | PR | contents: read | Pages-Preview je PR-Branch | mittel: nutzt CLOUDFLARE_API_TOKEN; Fork-PRs dürfen ohne Secrets nicht deployen (verifizieren) | KEEP + Audit bei jeder Änderung (R3) |
| deploy-production.yml | workflow_dispatch only | contents: read | manuelles Production-Deploy | mittel, durch Dispatch-Gate kontrolliert | KEEP |
| dependabot-auto-merge.yml | pull_request | contents: write, pull-requests: write | weniger Handarbeit bei Patch-Updates | HOCH: auto-merged auch semver-MINOR ohne menschliche Prüfung | OWNER_DECISION → siehe AUTO_MERGE_POLICY.md |

Nicht vorhanden (verifiziert): jules-auto-merge.yml, GitHub-Models-Workflows, AI-Review-Workflows (offene PRs #12/#13 würden welche einführen → R3-Owner-Review).

Pflicht bei jeder Workflow-Änderung: actionlint + zizmor + Permission-Audit + SHA-Pin-Kontrolle + pull_request_target-/Injection-Prüfung (Quorum R3).
