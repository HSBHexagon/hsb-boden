# Lead Import 5000 Checklist

## Purpose

Prepare future acquisition contacts for CRM-Light import or paste.

- The 5,000 acquisition contacts are not required for this documentation task.
- This task prepares the empty import-ready CRM structure.
- Lead import or paste is a future manual data-loading step.
- Import or paste is allowed only as CRM data preparation.
- Importing leads is not dispatch approval.
- No email, automation, or follow-up is triggered by this checklist.

### Missing input not a project blocker

The 5,000 lead records are an external input and are not expected to exist yet.

Until the lead data is provided:

- no import can be completed
- no manual test batch can be selected
- no dispatch can be approved
- no Phase 8 or Phase 9 work can start

But the system can still be marked:

- schema-ready
- import-template-ready
- validation-checklist-ready
- dispatch-gate-ready

## Required column order

Use `CRM_LIGHT_SCHEMA.md` as the source of truth and keep this column order for paste/import:

1. `Lead-ID`
2. `Firma`
3. `Standort`
4. `Region`
5. `Branche`
6. `Tier`
7. `Ansprechpartner`
8. `Rolle`
9. `E-Mail`
10. `Telefon`
11. `Website`
12. `Quelle`
13. `Beziehung / Kontaktgrund`
14. `Kampagne`
15. `Score`
16. `Status`
17. `Nächste Aktion`
18. `Follow-up-Datum`
19. `Interesse`
20. `Projektart`
21. `Fläche geschätzt`
22. `Belastungsart`
23. `Sanierungsfenster`
24. `Opt-in-Status`
25. `Opt-out-Status`
26. `Versandfreigabe`
27. `Verantwortlicher`
28. `Notizen`

## Fields allowed blank at import time

These fields may be blank initially and completed later if relevant:

- `Ansprechpartner`
- `Rolle`
- `Telefon`
- `Interesse`
- `Projektart`
- `Fläche geschätzt`
- `Belastungsart`
- `Sanierungsfenster`
- `Notizen`

## Fields that block dispatch if missing

Dispatch remains blocked if any of these are missing, unknown, or unclear:

- `E-Mail`
- `Quelle`
- `Beziehung / Kontaktgrund`
- `Opt-in-Status` or another documented recipient basis
- `Opt-out-Status`
- `Versandfreigabe`
- `Verantwortlicher`

## Required defaults

- `Status` defaults to `neu`
- `Nächste Aktion` defaults to `prüfen`
- `Versandfreigabe` defaults to `no`
- `Opt-out-Status` defaults to `unknown`
- `Opt-in-Status` defaults to `unknown`
- phone fields must be stored and formatted as text

## Lead-ID rule

- Use `HSB-YYYYMMDD-00001`
- IDs must be unique
- Do not reuse deleted IDs
- If imported data already contains IDs, verify uniqueness before paste

## Duplicate detection keys

- E-Mail
- Website
- Firma + Standort
- Firma + Ansprechpartner
- Telefon, if present

## Tiering rule

- Tier A = strong-fit industrial, food, pharma, chemical, or production lead with visible flooring, hygiene, or renovation relevance
- Tier B = plausible industrial or production lead with weaker urgency or incomplete contact basis
- Tier C = low-fit, incomplete, or needs manual qualification
- Unknown = not ready for dispatch

## Pre-paste checklist

- Headers match exactly.
- No duplicate emails.
- No duplicate websites.
- No duplicate company + location pairs.
- Phone columns are formatted as text.
- Opt-out rows are marked and blocked.
- Unknown legal/contact basis is marked as not approved for dispatch.
- Tier A/B/C is assigned.
- Source is documented.
- `Status` defaults to `neu`.
- `Nächste Aktion` defaults to `prüfen`.
- `Versandfreigabe` defaults to `no`.
- No formulas are pasted over headers or protected fields.
- Import is split into smaller batches if browser or Google Sheets performance degrades.

## Post-paste checklist

- Row count matches expected import count.
- Required columns are populated.
- No formula or header corruption exists.
- Filter and sort still work.
- A manual sample of 20 rows is checked.
- Duplicate spot check is completed.
- CRM status model remains intact.
- All dispatch approvals still default to `no` unless explicitly approved.
- No send action was triggered.
- No automation was triggered.

## Scale rule

- 5,000 rows are acceptable for Google Sheets CRM-Light at the current schema size.
- This is operational CRM storage and preparation only.
- It is not mass-email infrastructure.

## No-go list

- no bulk send
- no automation send
- no hidden tracking
- no scraped contact dispatch without documented basis
- no bypassing opt-out
- no use of unverified claims
- no n8n, Gmail, API, or Apps Script send action
