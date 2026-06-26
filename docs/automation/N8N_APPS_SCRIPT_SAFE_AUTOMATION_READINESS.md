# N8N_APPS_SCRIPT_SAFE_AUTOMATION_READINESS — HSB-Boden / HEXAFLOOR

Status: `automation-blueprints-documented-disabled-by-default-no-live-role`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No live automation activated. No outbound sending enabled. No auto-follow-up enabled.**
Canonical blueprint reference: `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md`

---

## Active Intake Chain (Unchanged — Must Not Be Replaced)

```
Website /api/lead
  → Worker (Cloudflare)
  → LEAD_WEBHOOK_URL (Worker secret)
  → Google Apps Script Web App
  → Google Sheets "HSB CRM Light"
```

This is the **only active automation**. It is intake-only. It does not send emails.
Apps Script in this chain is a passive webhook receiver and sheet writer.
n8n has **no active role today**.

---

## Apps Script — Current Role and Boundaries

### Current Active Role

| Function | Status |
|----------|--------|
| Receive POST from Cloudflare Worker via LEAD_WEBHOOK_URL | ✅ Active |
| Write lead data to Google Sheets CRM-Light | ✅ Active |
| Send automated outbound email to leads | ❌ Not permitted |
| Send automated follow-up to leads | ❌ Not permitted |
| Generate recipient lists | ❌ Not permitted |
| Change `Versandfreigabe` automatically | ❌ Not permitted |

### Apps Script Secrets Boundary

The Apps Script Web App URL (`LEAD_WEBHOOK_URL`) is stored exclusively as a Cloudflare
Worker secret. It must not be committed to git, documented in any tracked file with its
value, or shared with n8n.

### Optional Blueprint — Apps Script Internal Notification

If Joel wants an internal notification when a new web form lead arrives:

```javascript
// In the Apps Script webhook handler — optional addition
// Sends a notification to Joel's internal email only (not to the lead)
function notifyOperator(leadData) {
  MailApp.sendEmail({
    to: 'cherinojoel@gmail.com', // Internal operator only
    subject: `[HSB CRM] Neuer Lead: ${leadData.firma || 'Unbekannt'}`,
    body: `Neuer Lead eingegangen.\nFirma: ${leadData.firma}\nStatus: neu\nBitte prüfen.`
  });
}
```

**This is optional.** Activation requires:
1. Joel approval
2. Test run verified (single email received, correct content)
3. No lead PII in email body beyond company name

---

## n8n — Current Role and Boundaries

### Current Role

n8n has **no live role**. `ops/n8n/` content is historical documentation.

### Allowed Future Optional Roles (Blueprints Only)

n8n may be activated ONLY for internal operational notifications:

| Blueprint | Purpose | Permitted |
|-----------|---------|-----------|
| Daily CRM summary | Count rows by status, send to Joel's internal channel | ✅ Optional |
| Follow-up reminder | Alert when `Follow-up-Datum` is today and `Status = kontaktiert` | ✅ Optional |
| Weekly report | Aggregate stats (calls, replies, qualified) to internal doc | ✅ Optional |

### Forbidden n8n Actions (Permanent)

| Action | Status |
|--------|--------|
| Outbound email to leads | ❌ Never |
| Auto-follow-up sending | ❌ Never |
| Setting `Versandfreigabe = yes` automatically | ❌ Never |
| Generating new recipient lists | ❌ Never |
| Accessing `LEAD_WEBHOOK_URL` or any sending credential | ❌ Never |
| Bypassing `docs/launch/PHASE_7_COMPLIANCE_GATE.md` | ❌ Never |

### n8n Activation Gate (If Optional Blueprints Are Wanted)

- [ ] Joel explicitly approves specific workflow
- [ ] Workflow scope is limited to internal notifications only
- [ ] No sending credentials configured in n8n
- [ ] n8n reads CRM data only in read-only mode
- [ ] Workflow tested in n8n staging/sandbox before production
- [ ] Joel verifies output before activation

---

## Optional Blueprint Detail — Daily CRM Summary (n8n)

### Trigger
- Schedule: every weekday at 08:00 Europe/Berlin

### Steps
1. Read Google Sheets "HSB CRM Light" (read-only)
2. Count rows by Status:
   - `neu` — new, unreviewed
   - `kontaktiert` — contacted, awaiting reply
   - `geantwortet` — replied
   - `qualifiziert` — qualified opportunity
   - `verloren` — lost
3. Send summary to Joel's internal notification channel (Telegram, Slack, or Gmail — Joel's choice)

### Output (Example — Internal Only)

```
HSB CRM Tagesbericht — 2026-07-01
Neu: 3 | Kontaktiert: 12 | Geantwortet: 4 | Qualifiziert: 1 | Verloren: 2
Heutige Follow-ups fällig: 2
```

No lead names, no email addresses, no PII in notification.

---

## Optional Blueprint Detail — Follow-Up Reminder (n8n)

### Trigger
- Schedule: every weekday at 09:00 Europe/Berlin

### Steps
1. Read Google Sheets CRM-Light
2. Filter: `Status = kontaktiert` AND `Follow-up-Datum = today`
3. For each matching row: send internal alert to Joel only
4. Alert content: Lead-ID, Firma, Nächste Aktion (no email/phone from CRM)

---

## GitHub Branch Protection and Deploy Gate

All code changes — including any automation additions — must go through:

1. Feature branch (never commit directly to `main`)
2. Pull request with code review
3. CI passes (GitHub Actions: `ci.yml`)
4. Joel approval / merge
5. Deploy via: `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
   (Never `npm run deploy:production` or `--env production` — documented broken path)

See `docs/PHASE_C_CUTOVER_RUNBOOK.md` for deploy gate detail.

---

## Stop Conditions

- No n8n live activation without explicit Joel approval per workflow
- No Apps Script outbound email without explicit per-batch approval
- No automation that bypasses `Versandfreigabe = yes` check
- No automation that sends to leads without `docs/launch/PHASE_7_COMPLIANCE_GATE.md` complete
