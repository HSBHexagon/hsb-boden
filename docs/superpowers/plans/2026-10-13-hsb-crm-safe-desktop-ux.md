# HSB CRM – Safe Desktop UX plan (2026-10-13)
**Goal:** Non-destructive presentation of the existing Google Sheets Sales OS; no second CRM, mobile feature, or customer send.
**Canonical Sheet:** 1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg
**Execution:** superpowers:executing-plans; source modules and generated bundle kept byte-equivalent.
- [x] Replace destructive setup macro and reject missing operative tabs.
- [x] Preserve 11 operator views; hide only known technical/archive tabs.
- [x] Add test and quality gate; verify CI before merging.
- [ ] Authorized Mac offline: check actual Apps Script revision, deployment and triggers before any publish.
- [ ] Verify that combined and modular Apps Script sources are not simultaneously loaded in one project (duplicate function definitions).
- [ ] Restrict Drive 'anyone with link' permission using authorized permission management; current connector lacks deletion.
- [ ] Separate Oct-12 COM draft evidence from stale Oct-08 DE sync; investigate 167 review cases.
- [ ] Keep PR #459's opt-out fixes independent. No CRM writes, merges, production deployments, or email sends without verified approvals.
