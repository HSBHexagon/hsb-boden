# CRM_LIGHT_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `template-ready-awaiting-lead-data`
Stand: 2026-06-26 | Canonical since this sweep.
Sources consolidated: `CRM_LIGHT_SCHEMA.md`, `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`,
`docs/launch/PHASE_7_COMPLIANCE_GATE.md`.

No real PII, no actual lead dataset, no generated fake-person list in git.
Only schemas, templates, placeholders, and process docs belong here.
This document is operational readiness truth only.

---

## Canonical Field Order

Use this exact column order for all paste/import operations into "HSB CRM Light":

| # | Field | Type | Notes |
|---|-------|------|-------|
| 1 | Lead-ID | string | `HSB-0001` format |
| 2 | Firma | string | Required |
| 3 | Standort | string | City/location |
| 4 | Region | string | NRW / BW / etc. |
| 5 | Branche | string | Food, Chemical, Logistics… |
| 6 | Tier | enum | A / B / C / Unknown |
| 7 | Ansprechpartner | string | Optional at import |
| 8 | Rolle | string | GF, Werkleiter, Facility… Optional |
| 9 | E-Mail | string | Required for dispatch eligibility |
| 10 | Telefon | string (text!) | Preserve leading zeros |
| 11 | Website | url | Optional |
| 12 | Quelle | string | Required — document origin |
| 13 | Beziehung / Kontaktgrund | string | Required — document basis |
| 14 | Kampagne | string | e.g. `Outreach-2026-Q2` |
| 15 | Score | number | 0–100 |
| 16 | Status | enum | **Default: `neu`** |
| 17 | Nächste Aktion | string | **Default: `prüfen`** |
| 18 | Follow-up-Datum | date | YYYY-MM-DD |
| 19 | Interesse | string | hoch / mittel / niedrig |
| 20 | Projektart | string | Neubau / Sanierung |
| 21 | Fläche geschätzt | number (m²) | Optional |
| 22 | Belastungsart | string | mechanisch / chemisch / thermisch |
| 23 | Sanierungsfenster | string | Quarter / period |
| 24 | Opt-in-Status | enum | **Default: `unknown`** |
| 25 | Opt-out-Status | enum | **Default: `unknown`** |
| 26 | Versandfreigabe | enum | **Default: `no`** |
| 27 | Verantwortlicher | string | Joel / JORDIE |
| 28 | Notizen | text | Free text |

**Telephone fields must always be stored as text** — never as numbers. This preserves
leading zeros (e.g. `0170000000`).

---

## Required Safe Defaults

These defaults must be applied on every import row unless explicitly overridden:

| Field | Default | Meaning |
|-------|---------|---------|
| `Status` | `neu` | Not yet contacted |
| `Nächste Aktion` | `prüfen` | Needs manual review |
| `Versandfreigabe` | `no` | No send allowed until explicit approval |
| `Opt-out-Status` | `unknown` | Treat as blocking until confirmed |
| `Opt-in / recipient basis` | `unknown` | Treat as blocking until verified |

**No send is permitted unless `Versandfreigabe = yes` and all Phase 7 approval gates are met.**

---

## Send-Status Workflow

| Status | Meaning | Allowed next actions |
|--------|---------|---------------------|
| `neu` | Not yet contacted | Review, qualify, log in CRM before any contact |
| `kontaktiert` | First contact sent | Log date, response, schedule follow-up |
| `follow-up-1` | First follow-up sent | Log, schedule second if no response |
| `follow-up-2` | Second follow-up sent | Log, archive or close if no response |
| `interessiert` | Responded with interest | Move to offer phase |
| `angebot` | Offer / proposal sent | Track response |
| `gewonnen` | Deal closed | Document outcome |
| `verloren` | Not interested / lost | Document reason |
| `opt-out` | Opted out — immediate suppression | **No further contact allowed** |

Status transitions are manual only. No automated status change is permitted.

---

## Duplicate Detection Keys

Check against all of the following before import:

- `E-Mail` (exact match)
- `Website` (domain-level match)
- `Firma` + `Standort` (combined match)
- `Firma` + `Ansprechpartner` (combined match)
- `Telefon` (if present — normalized, leading zeros preserved)

---

## Dispatch-Blocking Fields

A row is blocked from dispatch until ALL of the following are present and resolved:

- `E-Mail` — must be present
- `Quelle` — must be documented
- `Beziehung / Kontaktgrund` — must be documented
- `Opt-in-Status` — must not be `unknown`
- `Opt-out-Status` — must not be `unknown` or `ja`
- `Versandfreigabe` — must be `yes`
- `Verantwortlicher` — must be assigned

Any missing or unresolved field blocks dispatch for that row.

---

## Manual Import Batch Rules

- Split large imports (>500 rows) into smaller batches to prevent Google Sheets performance issues
- 5,000 rows total is acceptable for CRM-Light at current schema size
- Verify row count matches expected import count after paste
- Do not paste over headers or protected column rows
- Do not paste formulas into data fields

---

## Row Verification Steps

After each import batch:

1. Row count matches expected import count
2. Required columns populated (`Firma`, `E-Mail`, `Quelle`, `Beziehung / Kontaktgrund`)
3. No formula or header corruption
4. Filter and sort still functional
5. Manual sample: check 20 random rows for data quality
6. Duplicate spot check on `E-Mail` and `Firma + Standort`
7. All `Versandfreigabe` default to `no` — confirm no row was incorrectly set to `yes`
8. No send action, no automation triggered during import

---

## Manual Follow-Up Workflow

### First Contact Logging Rule

Log the following in CRM before sending any first contact:
- Lead-ID
- Date
- Method (email / phone)
- Sender: `j-cherino@hsb-boden.de`
- Short note on contact reason

Update `Status` to `kontaktiert` after send.

### Follow-Up Windows

| Stage | Window | Action |
|-------|--------|--------|
| First follow-up | 4–7 days after first contact with no response | Send follow-up, update Status to `follow-up-1` |
| Second follow-up | 10–14 days after first contact with no response | Send second follow-up, update Status to `follow-up-2` |
| Archive / close | No response after second follow-up | Set Status to `verloren`, add close note |

### Opt-Out Immediate Suppression Rule

If a recipient replies with any opt-out signal (unsubscribe, stop, remove, please don't contact):
1. Immediately set `Opt-out-Status = ja` and `Versandfreigabe = no`
2. Log opt-out date and method in `Notizen`
3. No further contact from any channel
4. Do not restore `Versandfreigabe = yes` without documented review

### Archive / Close Rule

After second follow-up with no response:
- Set `Status = verloren`
- Note reason in `Notizen`
- Do not delete rows — keep for future reference
- Operator reviews monthly for any re-engagement potential

---

## Tiering Rule

| Tier | Criteria |
|------|---------|
| A | Strong-fit industrial, food, pharma, chemical, or production lead — visible flooring/hygiene/renovation relevance |
| B | Plausible industrial lead — weaker urgency or incomplete contact basis |
| C | Low-fit, incomplete, or needs manual qualification |
| Unknown | Not ready for dispatch — requires manual review |

---

## Compliance Prerequisite (Phase 7 Gate)

Before any batch send:

- [ ] Final lead list approved by Joel
- [ ] Recipient basis documented per recipient
- [ ] Source of each contact documented
- [ ] Opt-out wording approved
- [ ] Sender confirmed as `j-cherino@hsb-boden.de`
- [ ] Reply handling confirmed (CRM log required)
- [ ] Human owner approval documented for specific test batch
- [ ] Legal/compliance check documented
- [ ] Max first batch: 10–20 Tier A leads, manual only

See full gate: `docs/launch/PHASE_7_COMPLIANCE_GATE.md`

---

## Active Lead Intake Path

```
Website /api/lead
  → Google Apps Script Web App (LEAD_WEBHOOK_URL secret)
  → Google Sheets "HSB CRM Light"
```

`ops/n8n/` is historical/deprecated. n8n is not the active lead intake solution.
Apps Script is the active intake bridge, not a sending engine.

---

## Stop Condition

If the real 5,000-lead dataset does not exist yet: do not import, do not send.
If DNS/NS is not active: do not activate live automation.
This CRM remains `template-ready-awaiting-lead-data` until real data arrives.

---

## References

- Schema source: `CRM_LIGHT_SCHEMA.md`
- Import checklist: `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`
- Compliance gate: `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
- Operator handoff: `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`
