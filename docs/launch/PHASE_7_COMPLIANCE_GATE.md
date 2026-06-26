# Phase 7 Compliance Gate

## Purpose

Phase 7 is a controlled manual B2B outreach gate only.

- No mass mail.
- No automation.
- No n8n sending.
- No Gmail or API sending.
- No Apps Script live dispatch.
- No hidden tracking pixels unless separately approved and documented.
- No invented claims, logos, certificates, Argelith/Zahna claims, or unverified references.
- No campaign execution until every gate below is satisfied.
- The future 5,000 acquisition contacts are not required for this documentation task.
- This task prepares the empty import-ready CRM and compliance structure only.

Compliance is a required human/legal approval gate.

## Required approvals before any send

- Final lead list approved.
- Recipient basis documented per recipient.
- Source of each contact documented.
- Opt-out wording approved.
- Sender confirmed as `j-cherino@hsb-boden.de`.
- Reply handling confirmed.
- CRM logging process confirmed.
- Human owner approval documented for the specific test batch.
- Legal/compliance check documented.

## Required lead-list fields for Phase-7 approval

- `Lead-ID`
- `Firma`
- `Ansprechpartner`
- `Rolle`
- `E-Mail`
- `Quelle`
- `Beziehung / Kontaktgrund`
- `Opt-in / existing-customer / other documented basis`
- `Opt-out status`
- `Versandfreigabe yes/no`
- `Verantwortlicher`
- `Notizen`

## Manual test-send limit

- First batch max. `10-20` A-leads.
- Manual only.
- CRM row required before contact.
- CRM row required after contact.
- No follow-up automation.

## Exit criteria

Phase 7 is only ready to move from gate to controlled manual test-send once:

- Real lead data has been inserted or imported.
- All recipient rows are approved.
- Opt-out text is approved.
- The manual send checklist is complete.
- CRM logging is defined.
- The owner explicitly approves the exact batch.
- Legal/compliance approval is documented.

Until then, Phase 7 remains `gate-prepared-awaiting-lead-data`.
