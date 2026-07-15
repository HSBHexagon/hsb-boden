# JOEL_JORDI_OPERATOR_RUNBOOK — HSB-Boden / HEXAFLOOR

Status: `www-live-awaiting-review-compliance-and-owner-gates`
Stand: 2026-07-15 | Canonical operator layer above the truth docs.

**Partner name quality rule:** The only correct spelling is `Jordi` (JORDI in headings).
Never use `Jordy`, `Jordie`, or `Jodie` for the person in project text. Technical exceptions are the historical filename of this runbook and the exact existing Chrome profile label `Jordie (HEXAGON)`.

---

## Stop Condition (Read First)

Stand 2026-07-15 sind die früheren externen Trigger eingetreten:

1. `www.hsb-boden.de` läuft produktiv über Cloudflare Pages; der Apex leitet per 301 auf www. Die Zone `hsb-boden.de` im Info-Account ist weiterhin `pending`: Ein voller NS-Cutover ist **nicht** erfolgt und bleibt Owner-Gate.
2. 6.424 Leads liegen im MASTER-Sheet (Tier A 1.612 / B 4.812), aber die Versandfreigabe steht bei 0/6.424.

**Verbleibender Stop:** Kein Versand ohne erfüllten `docs/launch/PHASE_7_COMPLIANCE_GATE.md` und aktives M365-DKIM. Keine Production-Soft-404-Korrektur ohne unabhängiges Review/Freigabe, Merge und manuellen Deploy von PR #85. Keine Google-/CRM-Arbeit ohne explizite Re-Authentifizierung und Auswahl von `cherinojoel@gmail.com`. NS-Cutover, Cloudflare-Altaccount-Bereinigung und Token-/Service-Account-Key-Rotation bleiben separate Owner-Gates. Der GitHub-Models-PoC aus PR #74 bleibt deaktiviert, bis reale Cloudflare-AI-Gateway-Inferenz belegt ist.

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

> **Status 2026-07-15:** `www.hsb-boden.de` läuft produktiv über **Cloudflare Pages**; der Apex `hsb-boden.de` leitet per 301 (Query-erhaltend) auf www um. Im Cloudflare-Info-Account sind Pages-Projekt und www-Domain aktiv, es gibt dort keine Workers, und die Zone bleibt `pending`. Der alte Preview-Worker und die doppelte Zone im Alt-Account sind davon getrennte Cleanup-Gates. Ein voller NS-Cutover wurde nicht durchgeführt.

Falls später ein NS-Cutover freigegeben wird (Zone `hsb-boden.de` Status `active`):

1. Read `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` — go/no-go checklist
2. Read `docs/PHASE_C_CUTOVER_RUNBOOK.md` — **Achtung: dieses Dokument ist STALE aus der Workers-Ära.** Vor Ausführung erst prüfen/aktualisieren, ob die Schritte noch zur aktuellen Pages-only-Architektur passen; keine Worker-Route-Befehle blind ausführen.
3. Verify Pages deployment truth: `npm run deploy:dry-run` (Projekt `hsb-boden`, Account 01dc37803d1c687b4f9d6249ec89f700)
4. Verify env var `LEAD_WEBHOOK_URL` on the Pages project (Dashboard → Settings → Environment variables)
5. Run pre-cutover checks: `npm run build && npm run check && npm run test:run`
6. Only then: switch DNS per runbook
7. Verify live domain response: `curl -I https://hsb-boden.de` (must 301 → www) and `curl -I https://www.hsb-boden.de`
8. Verify contact form writes to CRM: **nur mit Owner-Freigabe**, nach erfolgreicher Google-Re-Authentifizierung, mit einer synthetischen Nicht-PII-Testprobe an `/api/lead` und verifiziertem Cleanup der Testzeile im Anschluss — ohne diese Voraussetzungen stattdessen einen Mock/Dry-Run verwenden
9. Verify GA4/GSC per `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`
10. Do not touch mail DNS records unless separately approved
11. Log completion in `SESSION_LOG.md`

**Do not skip the go/no-go checklist.**

---

## Trigger B — Lead Dataset Present; Outreach Still Blocked

Der reale Datensatz ist vorhanden (MASTER 6.424), bleibt aber vollständig für Versand gesperrt. Vor jedem Outreach:

1. Read `docs/crm/CRM_LIGHT_MAX_READINESS.md` — field order, defaults, duplicate rules
2. Read `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` — pre-paste and post-paste checklists
3. Read `docs/launch/PHASE_7_COMPLIANCE_GATE.md` — approval gates before any send
4. Verify DKIM is active for `j-cherino@hsb-boden.de` (see `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`)
5. Normalize phone fields as text, deduplicate on all defined keys
6. Set all defaults: `Status = neu`, `Versandfreigabe = no`, `Opt-out-Status = unknown`
7. Bestehenden Import in Google Sheets „HSB CRM Light" nicht ohne Owner-Freigabe überschreiben; für maschinellen Zugriff zuerst Profil `cherinojoel` explizit auf `cherinojoel@gmail.com` re-authentifizieren
8. Bei einem freigegebenen Neuimport 20 Zeilen stichprobenartig prüfen
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
- No Cloudflare zone/NS change, old-account cleanup, or token rotation without separate owner approval
- No production deploy via GitHub Actions without going through runbook
- No merge or production deploy of PR #85 without independent review and approval
- No activation of PR #74 while successful Cloudflare AI Gateway inference remains unproven
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

If clean and the remaining review/compliance/account/owner gates are not explicitly cleared: stop. Do not invent work or mutate external systems.
