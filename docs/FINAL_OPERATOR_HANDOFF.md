# FINAL_OPERATOR_HANDOFF — HSB-Boden / HEXAFLOOR

## Status
- Overall: `internal-base-ready-awaiting-dns-and-leads`
- Remote main: `bf0f998`
- CI/QA/Deploy Preview/Security/CodeQL: latest observed `success` on `main` for commit `bf0f998`
- Master plan: aligned
- Website: prepared
- CRM-Light: `template-ready-awaiting-lead-data`
- 5,000-lead import: `prepared-awaiting-data`
- Phase 7: `gate-prepared-awaiting-lead-data`
- Phase 12: `blocked-awaiting-dns-ns-switch`

## Remaining external inputs
1. DNS/NS transfer for `hsb-boden.de`
2. Future 5,000 lead dataset

## Final audit entrypoints
1. `docs/FINAL_PHASE_BY_PHASE_AUDIT.md`
2. `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md`
3. `docs/PHASE_C_CUTOVER_RUNBOOK.md`

## Trigger A — DNS/NS becomes active
Only when Cloudflare zone `hsb-boden.de` is active:
1. Read `docs/PHASE_C_CUTOVER_RUNBOOK.md`
2. Read `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md`
3. Verify production Worker route-less state before routes
4. Verify `LEAD_WEBHOOK_URL` secret exists
5. Set only the documented Worker routes
6. Verify live domain response
7. Verify real contact form writes to CRM
8. Do not touch mail DNS records unless separately required and approved

## Trigger B — 5,000 lead dataset becomes available
Only when the real lead dataset exists:
1. Read `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`
2. Read `docs/FINAL_PHASE_BY_PHASE_AUDIT.md`
3. Verify headers and column order
4. Normalize phone fields as text
5. Deduplicate before import
6. Mark `Versandfreigabe = no` by default
7. Import or paste as CRM preparation only
8. Verify row count and sample 20 rows
9. Do not send email
10. Do not start Phase 8 or Phase 9

## Still forbidden
- no email sending
- no mass mailing
- no automation activation
- no n8n execution
- no Gmail API sending
- no Apps Script live dispatch
- no Cloudflare/DNS/deploy action without explicit trigger and approval
- no Phase 8/9 start
- no use of unverified claims, logos, certificates, or references
- do not use `deploy-production.yml` as cutover truth; use `docs/PHASE_C_CUTOVER_RUNBOOK.md`

## Safe next command after reopening the repo
```bash
git status --short --branch
git log --oneline --decorate -5
gh run list --branch main --limit 10
```

## Stop condition

If neither external input exists, stop. Do not invent work.
