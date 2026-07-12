# JOEL_JORDI_OPERATOR_RUNBOOK — HSB-Boden / HEXAFLOOR

Status: `sales-operations-max-ready-awaiting-dns-and-leads`
Stand: 2026-06-26 | Canonical operator layer above the truth docs.

**Partner name quality rule:** The only correct spelling is `JORDI`.
Never use `Jordy`, `Jordi`, or `Jodie` in any project document.

---

## Stop Condition (Read First)

If neither of the following external inputs exists, stop. Do not invent work.

1. DNS/NS transfer for `hsb-boden.de` is active
2. Real 5,000-lead dataset has been delivered

Everything else in this repo is ready. The only remaining work is triggered by external inputs.

---

## Exact Resume Order

Open this repo and read in this exact order:

1. `docs/FINAL_OPERATOR_HANDOFF.md` — overall project status
2. `PROJECT_TRUTH.md` — canonical truth snapshot
3. `CHECKPOINT_STATE.json` — machine-readable state
4. `docs/FINAL_ADVERSARIAL_AUDIT.md` — verified final verdict
5. `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md` — historical Cloudflare audit
6. `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` — canonical Cloudflare readiness
7. `docs/PHASE_C_CUTOVER_RUNBOOK.md` — DNS trigger execution path
8. `docs/crm/CRM_LIGHT_MAX_READINESS.md` — CRM and lead data readiness
9. This file — operator role split and next actions

---

## Role Split: Joel vs JORDI

| Responsibility | Joel | JORDI |
|---------------|------|--------|
| Repo access, code decisions | ✅ Primary | — |
| DNS/NS switch coordination | ✅ Primary (with registrar) | Informed |
| Cloudflare route activation | ✅ Primary (after approval) | — |
| Outreach email composition | ✅ Primary (`j-cherino@hsb-boden.de`) | — |
| JORDI's flyer variant | — | ✅ Owner (`HSB-Flyer-Jordi-Post.pdf`) |
| Legal/compliance sign-off | ✅ Required from Joel | Co-review where agreed |
| Lead list approval | ✅ Both must agree | ✅ Co-approval |
| CRM updates after outreach | ✅ Joel logs first | JORDI logs own contacts |
| Business decisions / offers | Jointly | Jointly |

---

## Trigger A — DNS/NS Becomes Active

When Cloudflare zone `hsb-boden.de` shows status `active`:

1. Read `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` — go/no-go checklist
2. Read `docs/PHASE_C_CUTOVER_RUNBOOK.md` — step-by-step execution
3. Verify production worker is still route-less: `npx wrangler deployments list --name hsb-boden`
4. Verify secret: `npx wrangler secret list --name hsb-boden` — `LEAD_WEBHOOK_URL` must appear
5. Run pre-cutover checks: `npm run build && npm run check && npm run test:run`
6. Only then: activate routes per runbook
7. Verify live domain response: `curl -I https://hsb-boden.de`
8. Verify contact form writes to CRM: test POST to `/api/lead`
9. Activate GA4/GSC per `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`
10. Do not touch mail DNS records unless separately approved
11. Log completion in `SESSION_LOG.md`

**Do not skip the go/no-go checklist. Do not create routes before zone is `active`.**

---

## Trigger B — 5,000-Lead Dataset Arrives

When the real lead dataset is delivered:

1. Read `docs/crm/CRM_LIGHT_MAX_READINESS.md` — field order, defaults, duplicate rules
2. Read `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` — pre-paste and post-paste checklists
3. Read `docs/launch/PHASE_7_COMPLIANCE_GATE.md` — approval gates before any send
4. Verify DKIM is active for `j-cherino@hsb-boden.de` (see `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`)
5. Normalize phone fields as text, deduplicate on all defined keys
6. Set all defaults: `Status = neu`, `Versandfreigabe = no`, `Opt-out-Status = unknown`
7. Import or paste to Google Sheets "HSB CRM Light"
8. Sample-check 20 rows after import
9. **Do not send email. Do not start Phase 8 or 9.**
10. Complete Phase 7 compliance gate before any batch send

---

## Manual CRM and Outreach Logging Rules

Before any outreach contact:
- CRM row must exist for the lead
- `Versandfreigabe = yes` must be set and approved
- `Status` must reflect true current state

After any outreach contact:
- Log contact date, method, sender in `Notizen`
- Update `Status` (e.g., `kontaktiert`, `follow-up-1`)
- Set `Nächste Aktion` and `Follow-up-Datum`

After any opt-out:
- Immediately set `Opt-out-Status = ja` and `Versandfreigabe = no`
- Log opt-out date and signal in `Notizen`
- No further contact

---

## Follow-Up Windows

| Stage | Window |
|-------|--------|
| First follow-up | 4–7 days after first contact, no response |
| Second follow-up | 10–14 days after first contact, no response |
| Archive | No response after second follow-up → `Status = verloren` |

See: `docs/crm/CRM_LIGHT_MAX_READINESS.md` for the full workflow.

---

## What Remains Forbidden

At all times until explicit separate approval:

- No email sending to leads (DKIM + Phase 7 gate required first)
- No mass mailing
- No automation activation (n8n, Apps Script send, any auto-dispatch)
- No Cloudflare route creation before DNS/NS active
- No production deploy via GitHub Actions without going through runbook
- No Phase 8/9 start (requires Phase 7 review outcome)
- No use of customer logos, names, or references without per-use approval
- No unapproved claims, certifications, or project references
- No push/commit without explicit approval
- No PII, real lead data, or fake-person lead list in git

---

## Flyer Use Rules

| Flyer | Sender |
|-------|--------|
| `HSB-Flyer-Joel-Cherino.pdf` | Joel Cherino Diaz — use when Joel is the contact |
| `HSB-Flyer-Jordi-Post.pdf` | JORDI Post — use when JORDI is the contact |
| `HSB-Flyer-Geschaeftsfuehrer.pdf` | Generic variant — use when role matters more than name |

Do not send before DKIM is active and Phase 7 gate is completed.

---

## Key Document Map

| Need | Document |
|------|----------|
| Cloudflare readiness (canonical) | `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` |
| DNS cutover execution | `docs/PHASE_C_CUTOVER_RUNBOOK.md` |
| Email/deliverability readiness | `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md` |
| Analytics readiness | `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` |
| Asset/PDF readiness | `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md` |
| CRM schema + send workflow | `docs/crm/CRM_LIGHT_MAX_READINESS.md` |
| Automation blueprints (optional) | `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md` |
| Phase 7 compliance gate | `docs/launch/PHASE_7_COMPLIANCE_GATE.md` |
| Lead import checklist | `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` |
| Overall project truth | `PROJECT_TRUTH.md` |
| Final operator handoff | `docs/FINAL_OPERATOR_HANDOFF.md` |

---

## Safe First Commands After Reopening the Repo

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git status --short --branch
git log --oneline --decorate -5
gh run list --branch main --limit 5
```

If clean and no external trigger exists: stop. Do not invent work.
