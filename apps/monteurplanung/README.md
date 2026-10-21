# HEXAFLOOR Monteurplanung

Existing planner, extended from the user's HEXAFLOOR_Einsatzplaner_KOSTENLOS.html (Library revision 2, 2026-10-20) and the previously hosted HSB Boden planner (source e8f48ab9f9fdf463159b67c56445c51fd0a0630a).

## Canonical source and operations

Canonical repository: https://github.com/HSBHexagon/hsb-boden, path `apps/monteurplanung/`.
Hosting remains the **existing** Sites application on Cloudflare Workers, project `appgprj_6ad6cecb911c8191bcea167554724ca5`. The Sites Git repository is a deployment mirror, not a second source of planning data. Keep `.openai/hosting.json` and use Sites publishing helpers. Never deploy to the website's Pages project.

The only operational data source is the existing Cloudflare D1 `DB` binding, `planning_*` tables. Google Sheet `1ifyWKXZbNaB48rPfnDeoQgGgqC2YOUJ0zUETnke2CjE` was independently read on 2026-10-21: all three domain tabs contained headers only; `_META.rev=0`. No Google Sheets sync or browser record cache exists. Legacy D1 `plans` was read and contained no rows before the change. It remains untouched and unused.

Production records use environment `production`. `/planner.html?environment=test` and `/api/test-plan` use an independently keyed `test` namespace in the same D1 database, with compound keys and environment predicates on every query. This is logical isolation, not a separate database or infrastructure account. Synthetic fixtures exist only in automated tests or this test environment. Never load them through `/api/plan`.

## Access boundary

The Site was changed from public to custom, owner-only access on 2026-10-21, access-policy revision 3, and independently read back. Sites dispatch enforces this on all pages, static assets and APIs. It consumes platform service credentials before forwarding; those calls do not include visitor identity. API requests with another authenticated visitor ID are rejected too. **Never make this Site public**. Do not copy the shared service-call behavior to a public Worker.

The current allowed user is the existing Site owner. Additional staff access requires deliberate grant in Sites and updating API authorization; no invitations were sent. No app passwords or tokens belong in source.

## Application behavior

Projects and workers have durable internal IDs distinct from project numbers. Workers have skills and crew names. Assignments are full days Monday–Saturday; server validation and a database unique key prevent double bookings. Absences remove only affected daily assignments. Free candidates respect skills and crews. Reassignment suggestions use excess staff and require explicit confirmation. Archiving with assignments requires confirmation before removing those assignments; revision backups preserve the previous state. Reopening retains the project ID.

Weekly table, selected-day shortages, archive/edit forms, project extension, per-day requirements, Saturday activation, absence management, CSV, printable full-week plan and copyable WhatsApp text reuse the existing interface. No automatic WhatsApp or email sending. External plan text omits absence records and internal notes.

Each successful save uses an atomic D1 batch with compare-and-swap revision and random write token. Stale writers receive HTTP 409. Failed statements roll back the entire write. Parent rows are updated in place so future project documents can reference them. Every save also appends an immutable full revision snapshot and server-derived change description. JSON export/import supports manual backup and restore; imports use the current revision and normal validation. Quota errors leave the last stored state intact.

## Verification

`node --test tests/*.test.mjs` exercises real SQLite transaction SQL and shared production planning logic; `node_modules/.bin/tsc --noEmit` checks types; the Sites build helper builds the Worker. Tests use an in-memory SQLite adapter, not a claim of live D1 or browser verification.

Browser QA is blocked in this execution environment by the cloud-browser URL policy. Do not report the ten user acceptance cases as passed in a browser. Live deployment/API and source/CI evidence are recorded separately in the final acceptance report.

No new paid plan, external database, analytics product or subscription is required or activated. Actual underlying Sites billing/quota details are controlled by the existing platform and must not be inferred from a direct Cloudflare Free tier. Direct Cloudflare connector calls failed with MCP -32603 Internal error in this session.

## Future project-file integration (not implemented)

Reviewed Drive HTML `1FtcXbHpNa_tx-xumpNSsDg9YdJDMAptu` and PDF `11WYZYkGSbdkwcAPHY2if1ZkGXZwO1POq` on 2026-10-21. Existing forms cover report number/date, construction project, supervisor, weather, work times, staff categories/hours, performance, obstructions, changes, incidents, signatures and photo pages with descriptions. HTML uses local browser form text storage and embedded photo data, plus print-to-PDF; it is not a central project document backend.

Later reports must reference `planning_projects(environment,id)` with a foreign key and keep document/report IDs separate. Reuse form layout, print behavior and photo-description UX; migrate browser-only storage when that module is commissioned. Reports/photos, time tracking, materials/orders, quotations/contracts/variations, correspondence chronology and cost analyses are intentionally not implemented here.
