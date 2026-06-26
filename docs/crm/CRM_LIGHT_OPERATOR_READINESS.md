# CRM_LIGHT_OPERATOR_READINESS — HSB-Boden / HEXAFLOOR

Status: `crm-template-ready-operator-workflow-documented-awaiting-lead-data`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No real PII. No actual lead dataset. No generated fake-person list.**
Only schema, workflow, and safe defaults are documented here.
Canonical CRM schema truth: `docs/crm/CRM_LIGHT_MAX_READINESS.md`
Compliance gate: `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
Lead import process: `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`

---

## CRM-Light System Overview

| Item | Value |
|------|-------|
| System | Google Sheets — "HSB CRM Light" |
| Owner | Joel Cherino Diaz (`cherinojoel@gmail.com`) |
| Active intake channel | Website form → `/api/lead` → Apps Script Web App → Google Sheets |
| Intake verification | End-to-end tested and verified — 2026-06-24 |
| Lead data present | No — awaiting real dataset |
| Status | `template-ready-awaiting-lead-data` |

---

## Canonical Safe Defaults (All New Rows)

Every row — whether from web form intake or manual import — must start with these defaults:

| Field | Default Value | Notes |
|-------|--------------|-------|
| Status | `neu` | Never pre-set to `kontaktiert` or `versendet` |
| Nächste Aktion | `prüfen` | Operator sets real action after review |
| Versandfreigabe | `no` | Never `yes` until explicitly approved per recipient |
| Opt-in-Status | `unknown` | Never assume opt-in |
| Opt-out-Status | `unknown` | Treat as blocking equivalent until verified |

No batch or individual outreach email may be sent until:
- `Versandfreigabe = yes` is set per recipient
- `Opt-out-Status ≠ opted_out`
- Recipient basis is documented in `Beziehung / Kontaktgrund`
- Batch is approved per `docs/launch/PHASE_7_COMPLIANCE_GATE.md`

---

## Operator Daily Workflow

### Morning Check (Joel — Primary Operator)

```
1. Open "HSB CRM Light" in Google Sheets
2. Filter: Status = neu (new website form leads since last check)
3. For each new row:
   a. Review company, contact, message
   b. Assess tier (A = high priority / B = medium / C = low)
   c. Set Nächste Aktion (call / email / research)
   d. Set Follow-up-Datum (YYYY-MM-DD)
   e. Add Notizen: key context, interest signal
4. Escalate A-tier leads immediately
```

### After Contact Attempt

```
1. Find lead row by Lead-ID or Firma
2. Update Status:
   - kontaktiert (if email or call attempted)
   - geantwortet (if reply received)
   - qualifiziert (if interest confirmed)
   - verloren (if declined or no response after 3 attempts)
3. Update Nächste Aktion to next concrete step
4. Update Follow-up-Datum
5. Add Notizen entry: [YYYY-MM-DD] Kontakt per E-Mail — [key outcome]
```

### After Opt-Out Reply

```
1. Find lead row
2. Set Opt-out-Status = opted_out
3. Set Versandfreigabe = no
4. Add Notizen: [YYYY-MM-DD] Abmeldung per E-Mail — nie wieder kontaktieren
5. Do not delete the row — keep as audit record
```

---

## Role Split: Joel vs JORDIE

| CRM Task | Joel | JORDIE |
|----------|------|--------|
| CRM sheet ownership | ✅ Primary | — |
| Review new web form leads | ✅ Daily | — |
| Log own outreach contacts | ✅ Always | — |
| Log JORDIE's contacts | — | ✅ Logs own column (Verantwortlicher = JORDIE) |
| Set Versandfreigabe | ✅ Joint approval | ✅ Joint approval |
| Lead list import approval | ✅ Both required | ✅ Both required |
| Tier A escalation decision | ✅ Joint | ✅ Joint |

---

## Web Form Lead Intake (Active)

New website form submissions arrive automatically in CRM-Light:

```
User submits form at hsb-boden.de/
  → POST /api/lead (Worker)
  → Fetch to LEAD_WEBHOOK_URL (Worker secret)
  → Google Apps Script Web App
  → New row in "HSB CRM Light"
```

Default fields set by Apps Script intake:
- Lead-ID: auto-generated (`HSB-XXXX`)
- Quelle: `website-form`
- Status: `neu`
- Nächste Aktion: `prüfen`
- Versandfreigabe: `no`
- Opt-in-Status: `unknown`
- Opt-out-Status: `unknown`

Joel reviews within 1 business day. No automated reply is sent.

---

## Lead Tier Scoring Guide

| Tier | Criteria |
|------|---------|
| A | Food/Chemical/Logistics company, GF/Werkleiter contact, >500 m² estimated area, mentioned timeline |
| B | General industrial, Facility Manager contact, <500 m² or unclear area, no timeline |
| C | Unknown industry fit, student/researcher, competitor, or unclear basis |

Score 0–100 (optional): A = 70–100, B = 40–69, C = 0–39.

---

## CRM Column Quick Reference

Full schema in `docs/crm/CRM_LIGHT_MAX_READINESS.md`. Key fields for daily use:

| Field | Purpose |
|-------|---------|
| Lead-ID | Unique identifier — always log in email subject line |
| Firma | Company name |
| Status | Current stage (`neu / kontaktiert / geantwortet / qualifiziert / verloren`) |
| Nächste Aktion | What to do next |
| Follow-up-Datum | When to follow up (YYYY-MM-DD) |
| Versandfreigabe | `no` until explicitly approved — never override without approval |
| Notizen | Free text log — always prepend `[YYYY-MM-DD]` |

---

## Manual Paste / Import Protocol (Future — When Lead Data Available)

See `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` for full import checklist.

Quick summary:
1. Import ONLY after Joel reviews and approves the lead list
2. Paste max 50 rows per batch — verify before next batch
3. All rows start with safe defaults (Status=neu, Versandfreigabe=no, Opt-in=unknown)
4. Never paste real lead data into any git-tracked file

---

## Verification Commands (CRM Infrastructure)

```bash
# Verify Apps Script web app URL is set as Worker secret
npx wrangler secret list --name hsb-boden
# Expected: LEAD_WEBHOOK_URL listed

# Verify end-to-end pipeline is live
# Test by submitting the form on: https://hsb-boden.cherinojoel.workers.dev/
# Then check Google Sheets for new row
```

---

## Stop Conditions

- If no real lead data exists, do not import placeholder data
- If no web form submissions exist yet, do not fabricate test rows in the production sheet
- If DKIM is not active, do not set `Versandfreigabe = yes` for any recipient
- If `docs/launch/PHASE_7_COMPLIANCE_GATE.md` is not completed, stop all outreach
