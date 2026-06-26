# FINAL_OPERATOR_HANDOFF — HSB-Boden / HEXAFLOOR

## Status
- Overall: `sales-operations-max-ready-awaiting-dns-and-leads`
- Remote main: `d4ea032`
- CI/QA/Deploy Preview/Security/CodeQL: latest observed `success` on `main`
- Master plan: aligned
- Website: prepared
- CRM-Light: `template-ready-awaiting-lead-data`
- 5,000-lead import: `prepared-awaiting-data`
- Phase 7: `gate-prepared-awaiting-lead-data`
- Phase 12: `blocked-awaiting-dns-ns-switch`

## Remaining external inputs
1. DNS/NS transfer for `hsb-boden.de`
2. Future 5,000 lead dataset

## Canonical readiness stack (current)

### Tier 1 — Canonical Readiness Truth
- **Cloudflare Provider**: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
- **Email/Deliverability**: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`
- **Analytics (GA4/GTM/GSC)**: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`
- **Assets/PDFs**: `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`
- **CRM-Light**: `docs/crm/CRM_LIGHT_MAX_READINESS.md`
- **Automation Blueprints**: `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md`
- **Operator Runbook**: `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`

### Tier 2 — Expanded Readiness Detail (2026-06-26 Wave)
- **Cloudflare UI Preflight Inventory**: `docs/cloudflare/GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`
- **WAF/Cache/Rate-Limit**: `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`
- **R2 Asset Strategy**: `docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`
- **Turnstile Form Protection**: `docs/cloudflare/TURNSTILE_FORM_PROTECTION_READINESS.md`
- **AI Gateway (future only)**: `docs/cloudflare/AI_GATEWAY_FUTURE_ARCHITECTURE.md`
- **GA4 Event Tracking Plan**: `docs/analytics/GA4_GSC_EVENT_TRACKING_READINESS.md`
- **Email Templates & Deliverability**: `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md`
- **UTM and QR Matrix**: `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`
- **CRM Operator Workflow**: `docs/crm/CRM_LIGHT_OPERATOR_READINESS.md`
- **n8n / Apps Script Safe Automation**: `docs/automation/N8N_APPS_SCRIPT_SAFE_AUTOMATION_READINESS.md`
- **Multi-PC Operator Sync Protocol**: `docs/ops/MULTI_PC_OPERATOR_SYNC_PROTOCOL.md`
- **Master Go-Live Checklist**: `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md`

## Final audit entrypoints (historical evidence)
1. `docs/FINAL_PHASE_BY_PHASE_AUDIT.md`
2. `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md` (historical wrapper → see cloudflare/ canonical)
3. `docs/PHASE_C_CUTOVER_RUNBOOK.md`

## Trigger A — DNS/NS becomes active
Only when Cloudflare zone `hsb-boden.de` is active:
1. Read `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` — go/no-go checklist
2. Read `docs/PHASE_C_CUTOVER_RUNBOOK.md` — execution steps
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
