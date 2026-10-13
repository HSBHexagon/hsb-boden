# HSB CRM – Safe Desktop UX and live operations (2026-10-13)

> Execute with Superpowers: systematic-debugging, test-driven-development and verification-before-completion. Existing infrastructure only. No Opera, Desktop Commander or local Mac requirement for Google Sheets, GitHub, permission management, Apps Script UI inspection.

**Goal:** Improve the existing HSB CRM safely while preserving its unique canonical data source.
**Canonical Sheet:** `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`.
**Scope:** Desktop UX, formula integrity, access safety, existing Apps Script, .de/.com synchronization evidence. No mobile, new CRM, new mailing job, new agent dependency, or production deploy without gates.

## Completed changes (verified)

- [x] PR #460: replace destructive `setupPremiumSheetUX` setup with a formatting-only, fail-closed action.
- [x] PR #460: preserve all eleven existing operator tabs; hide only known technical/archival tabs.
- [x] PR #460: generate `HSB_SALES_OS.gs` from the four canonical source modules; Node regression test included in Quality Assurance and green in the initial run.
- [x] Read `README!A4` / `DASHBOARD!E13:E14` via Google Sheets API, replace falsely reassuring "Echtzeit" / "alle 15 Minuten" captions with truthful "Tabellenstand" / last **logged** .de sync captions; independent API read-back confirmed formulas untouched.
- [x] Remove public `anyone:reader` permission from the original CRM using authenticated owner via Google web browser; independent direct Google Drive API checks through both connected accounts confirm public=false and owner plus five named editors unchanged.
- [x] Access live bound Apps Script via existing authorized **TinyFish Google profile**. Live project found; files include `HSB_GraphAdapter.gs`, `HSB_SALES_OS.gs`, `HSB_FlowConnect.gs`, `HSB_DraftAdapter.gs.gs`, `HSB_AdapterSelbsttest.gs`, two HTML files and manifest. No separate `Config.gs`, `Engine.gs`, `Code.gs`: combined+modular duplicate in one project not observed.

## Root cause found for stale .de sync

- [x] Inspect live Apps Script Executions and triggers. Two time-driven `hsbAutoReconcile` triggers visible, both owned by **another user**; recent error rates approximately 73%.
- [x] Multiple failures on October 12–13 report exact runtime dispatch error `Scriptfunctie niet gevonden: hsbAutoReconcile` ("Script function not found"). No successful recent reconcile observed; `onOpen` succeeds. This is not evidence of an IMAP/.com or Gmail failure.
- [x] Confirm **live** `HSB_GraphAdapter.gs` does not expose declaration `function hsbAutoReconcile()` (editor search "No results"), while the **GitHub** module `apps/sales-os/apps_script/HSB_GraphAdapter.gs` DOES define it (about line 841). Source drift proven.
- [ ] Reconcile the full live `HSB_GraphAdapter.gs` and other actual Apps Script source with GitHub. Do **not** replace the whole file blindly: live-only changes, account-bound tokens, extra adapters and invocation paths must be identified.
- [ ] Safely restore the missing handler only after tests cover APIHub/Graph token handling, ScriptLock, and `SYNC_STATUS` data writes. No live patch without complete source review and rollback.
- [ ] Clean up each stale time trigger **under its actual creator account** (current signed-in owner sees "Other user"). Do not create additional triggers or claim they can be deleted by a different account.
- [ ] Verify first controlled read-only mailbox reconciliation, check its persisted `SYNC_STATUS` timestamp and error log; never trigger external sending.
- [ ] Recheck live script deployment versions, including "HSB v6", before app publishing; a GitHub commit is not a deployment.

## Operational truth and release gates

- [ ] Triage 167 unresolved `INBOUND_EVENTS` without guessing lead or owner; do not mass-apply status changes.
- [ ] Keep documented Oct-12 COM drafts separate from last logged Oct-08 DE reconciliations; no invented "live" state.
- [ ] PR #460 must pass checks and review before merge; no automatic merging. PR #459 opt-out repairs are independent and not covered by this plan.
- [ ] Human desktop UX check of existing `README`, `DASHBOARD`, `HEUTE JOEL`, `HEUTE JORDI` with actual data before deploying the PR's source changes.

## Tool-selection rule

1. Use native Google Drive/Sheets/GitHub/Cloudflare tools for reads and supported writes; use a connected browser profile only for missing browser-only Apps Script/Google permissions operations.
2. An unconnected Opera browser and an offline Desktop Commander are **not** prerequisites and must not block independent progress.
3. If the exact user/account authorization is absent, record the precise blocker; do not create duplicate systems or speculate.
4. Stop at destructive actions, new mail sends, or untested live Apps Script repairs. Verify every implemented step against the existing source of truth.
