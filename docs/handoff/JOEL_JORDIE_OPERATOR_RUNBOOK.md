# JOEL_JORDI_OPERATOR_RUNBOOK — HSB-Boden / HEXAFLOOR

Status: `www-live-core-fixed-security-and-owner-gates-open`
Stand: 2026-07-15, 12:06 CEST | Canonical operator layer above the truth docs.

**Partner name quality rule:** The only correct spelling is `Jordi` (JORDI in headings).
Never use `Jordy`, `Jordie`, or `Jodie` for the person in project text. Technical exceptions are the historical filename of this runbook and the exact existing Chrome profile label `Jordie (HEXAGON)`.

---

## Stop Condition (Read First)

Stand 2026-07-15 sind die früheren externen Trigger eingetreten:

1. `www.hsb-boden.de` läuft produktiv über Cloudflare Pages; der Apex leitet per 301 auf www. Die Zone `hsb-boden.de` im Info-Account ist weiterhin `pending`: Ein voller NS-Cutover ist **nicht** erfolgt und bleibt Owner-Gate.
2. 6.424 Leads liegen im MASTER-Sheet (Tier A 1.612 / B 4.812), aber die Versandfreigabe steht bei 0/6.424.

**Verbleibender Stop:** Kein Versand ohne erfüllten
`docs/launch/PHASE_7_COMPLIANCE_GATE.md` und aktives M365-DKIM. Zwei im
oeffentlichen Repo sichtbar gewordene Apps-Script-Endpunkte muessen durch einen
neuen authentifizierten Pfad ersetzt werden: Preview-Test, atomare Production-
Umstellung, E2E-Verifikation, alte Deployments zuletzt invalidieren. Keine
Google-/CRM-Arbeit ohne explizite
Re-Authentifizierung und Auswahl von `cherinojoel@gmail.com`. PR #86 nicht
unveraendert mergen. NS-Cutover, Cloudflare-Altaccount-Bereinigung und
Token-/Service-Account-Key-Rotation bleiben separate Owner-Gates. PR #74 bleibt
deaktiviert, bis reale Cloudflare-AI-Gateway-Inferenz belegt ist.

---

## Exact Resume Order

Read and verify in this exact order before any action:

1. `~/KI-System/ObsidianVault/brain/01_core/STORAGE_ROLES.md`
2. `~/KI-System/ObsidianVault/brain/START_HIER.md`
3. `~/KI-System/ObsidianVault/brain/CANONICAL_STATE.md`
4. `~/KI-System/08_System/config/canonical-projects.json`
5. `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`
6. Resolve and assert the canonical checkout, then inspect Git:

   ```bash
   cd "$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)"
   ~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden
   git status --short --branch
   ```

7. `AGENTS.md` and `CLAUDE.md` — project rules and execution preflight
8. `PROJECT_TRUTH.md` — current canonical project truth
9. `CHECKPOINT_STATE.json` — machine-readable current state
10. `docs/ai_state/TRUTH_MATRIX_2026-07-15.md` — timestamped evidence
11. `docs/MASTER_EXECUTION_PLAN.md` — canonical phase roadmap
12. This file — operator role split and next actions
13. `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md` — supporting Cloudflare evidence
14. `docs/crm/CRM_LIGHT_MAX_READINESS.md` — supporting CRM evidence
15. `docs/FINAL_OPERATOR_HANDOFF.md` and `docs/PHASE_C_CUTOVER_RUNBOOK.md` —
    historical/superseded evidence only; never execute their old commands

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
2. `docs/PHASE_C_CUTOVER_RUNBOOK.md` nur als historische Evidenz lesen. Fuer
   einen spaeter freigegebenen NS-Cutover zuerst ein neues Pages-/Mail-DNS-
   Runbook erstellen; keine Worker-Befehle daraus ausfuehren.
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
- Keine Wiederverwendung der im Git-Verlauf exponierten Apps-Script-Endpunkte;
  neuen Auth-Pfad zuerst bauen/testen, alte Deployments erst nach erfolgreicher
  Umstellung invalidieren
- PR #86 nicht unveraendert mergen; nur einzeln belegte Schutzlogik in einem
  frischen PR auf aktuellem `main` portieren
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
| Optionaler spaeterer NS-Cutover | Neues Pages-/Mail-DNS-Runbook erforderlich; `docs/PHASE_C_CUTOVER_RUNBOOK.md` nur historische Evidenz |
| Email/deliverability readiness | `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md` |
| Analytics readiness | `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` |
| Asset/PDF readiness | `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md` |
| CRM schema + send workflow | `docs/crm/CRM_LIGHT_MAX_READINESS.md` |
| Automation blueprints (optional) | `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md` |
| Phase 7 compliance gate | `docs/launch/PHASE_7_COMPLIANCE_GATE.md` |
| Lead import checklist | `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` |
| Overall project truth | `PROJECT_TRUTH.md` |
| Historischer Operator-Snapshot | `docs/FINAL_OPERATOR_HANDOFF.md` — superseded, nicht als Resume-Start verwenden |

---

## Safe First Commands After Reopening the Repo

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git status --short --branch
git log --oneline --decorate -5
gh run list --branch main --limit 5
```

If clean and the remaining review/compliance/account/owner gates are not explicitly cleared: stop. Do not invent work or mutate external systems.
