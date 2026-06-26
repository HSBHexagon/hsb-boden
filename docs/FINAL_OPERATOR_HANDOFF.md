# FINAL_OPERATOR_HANDOFF — HSB-Boden / HEXAFLOOR

## Status
- Overall: `internal-base-ready-awaiting-dns-and-leads`
- Remote main: `17479a3`
- CI/QA/Deploy Preview/Security/CodeQL: latest observed `success` on `main` for commit `17479a3`
- Master plan: aligned
- Website: prepared
- CRM-Light: `template-ready-awaiting-lead-data`
- 5,000-lead import: `prepared-awaiting-data`
- Phase 7: `gate-prepared-awaiting-lead-data`
- Phase 12: `blocked-awaiting-dns-ns-switch`

## Remaining external inputs
1. DNS/NS transfer for `hsb-boden.de`
2. Future 5,000 lead dataset

## Trigger A — DNS/NS becomes active
Only when Cloudflare zone `hsb-boden.de` is active:
1. Read `docs/PHASE_C_CUTOVER_RUNBOOK.md`
2. Verify production Worker route-less state before routes
3. Verify `LEAD_WEBHOOK_URL` secret exists
4. Set only the documented Worker routes
5. Verify live domain response
6. Verify real contact form writes to CRM
7. Do not touch mail DNS records unless separately required and approved

## Trigger B — 5,000 lead dataset becomes available
Only when the real lead dataset exists:
1. Read `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`
2. Verify headers and column order
3. Normalize phone fields as text
4. Deduplicate before import
5. Mark `Versandfreigabe = no` by default
6. Import or paste as CRM preparation only
7. Verify row count and sample 20 rows
8. Do not send email
9. Do not start Phase 8 or Phase 9

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

## Safe next command after reopening the repo
```bash
git status --short --branch
git log --oneline --decorate -5
gh run list --branch main --limit 10
```

## Stop condition

If neither external input exists, stop. Do not invent work.
