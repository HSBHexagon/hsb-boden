# STATUS_UPDATE_AUTOMATION_BLUEPRINT — HSB-Boden / HEXAFLOOR

Status: `blueprints-documented-automation-disabled-by-default`
Stand: 2026-06-26 | Canonical since this sweep.

Automation is **optional and disabled by default**.
No live outbound campaign sending, no auto-follow-up, no automation activation performed here.
This document describes optional future blueprints only.

---

## Active Intake Truth (Unchanged)

The active lead intake chain is:

```
Website /api/lead
  → Google Apps Script Web App (LEAD_WEBHOOK_URL secret)
  → Google Sheets "HSB CRM Light"
```

This chain is live, verified, and must not be replaced or overridden by any blueprint below.
Apps Script is the active intake bridge, not a sending engine.

---

## Optional Blueprint 1 — n8n Status-Update Workflow

### Purpose

Internal status reminder and daily summary notification only.
n8n is optional and currently disabled. `ops/n8n/` content is historical.

### Trigger

Manual operator activation only. No auto-start.
Requires explicit documented approval before activation.

### Allowed Actions

- Read CRM rows where `Status = kontaktiert` and `Follow-up-Datum` is approaching
- Generate a daily summary notification to Joel's internal channel (not to leads)
- Log status reminder to a designated internal doc or sheet

### Forbidden Actions

- No outbound email to leads
- No auto-follow-up sending
- No automated `Versandfreigabe` change
- No recipient generation
- No bypass of Phase 7 compliance gate
- No access to secrets beyond CRM read access

### Secrets Boundary

n8n may only read CRM data for internal notifications.
n8n must not hold or use `LEAD_WEBHOOK_URL` or any sending credential.
SMTP/sending credentials must never be configured in n8n without separate approval.

### Human-Approval Dependency

Before activation:
- [ ] Explicit approval from Joel documented
- [ ] Blueprint scope review — confirmed no outbound send
- [ ] n8n health verified (no failing or pending MCP references)
- [ ] Separate approval if any send capability is added to n8n

---

## Optional Blueprint 2 — Google Apps Script Status-Update Workflow

### Purpose

Apps Script as an optional status-update helper for the Google Sheets CRM-Light.
Currently Apps Script is only the active intake bridge (receiving form data).

### Trigger

Manual operator activation via Apps Script editor only.
No time-based trigger without explicit approval.

### Allowed Actions

- Scan CRM-Light rows for upcoming `Follow-up-Datum` values
- Write a summary row or tab in the same Sheet for operator review
- Send a single internal summary notification to Joel's Gmail (not to leads)

### Forbidden Actions

- No outbound email to leads or prospects
- No auto-follow-up campaigns
- No automated lead generation
- No bypass of opt-out or dispatch gate
- No use of `LEAD_WEBHOOK_URL` for sending

### Secrets Boundary

Apps Script may only operate on the Google Sheet it owns.
Any SMTP or external API credential requires separate approval before addition.

### Human-Approval Dependency

Before activating any time-based trigger or send capability:
- [ ] Explicit approval from Joel documented
- [ ] Scope confirmed as internal summaries only
- [ ] No outbound lead contact added

---

## Forbidden Blueprint Scope (Applies to Both Blueprints)

Neither blueprint may ever:

- Send outbound email to leads or prospects
- Trigger auto-follow-up sequences
- Generate or add new recipient records
- Bypass the Phase 7 compliance gate (`docs/launch/PHASE_7_COMPLIANCE_GATE.md`)
- Access or expose `LEAD_WEBHOOK_URL` or any production secret value
- Replace the manual CRM operation model

---

## Stop Condition

If DNS/NS is not active and no real 5,000-lead dataset exists:
do not activate any automation blueprint.

Automation remains disabled by default until explicit operator approval.

---

## References

- CRM readiness: `docs/crm/CRM_LIGHT_MAX_READINESS.md`
- Compliance gate: `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
- Operator handoff: `docs/handoff/JOEL_JORDI_OPERATOR_RUNBOOK.md`
