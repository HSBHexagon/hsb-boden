# Phase 8: Marketing Readiness / Conversion Report
**Project:** hsb-boden
**Date:** 2026-06-12
**Status:** BLOCKED (lead pipeline not live — matches AGENTS.md Deploy Gate)

---

## 1. Lead Capture Form

- `src/components/forms/LeadForm.tsx` + `LeadFormSection.astro` implement the lead capture UI.
- Endpoint config: `src/data/site.ts` reads `PUBLIC_LEAD_ENDPOINT` and `PUBLIC_LEAD_ACCESS_KEY` from environment variables, both default to `""` if unset.
- Per `AGENTS.md` Accessibility note and `ACCESSIBILITY_REPORT.md`, form labels/ARIA need verification before go-live (open item carried from accessibility audit).

## 2. Lead Pipeline Status (per `working_set.json`, `hsb_n8n_2026-06-07`)

- n8n workflow exists at `ops/n8n/hsb-boden-lead-intake.json` (`POST /hsb-boden-lead-intake`), imported and active in a **local** n8n instance (`localhost:5678`).
- **No production webhook exists.** A `localhost` endpoint cannot receive submissions from the live Cloudflare-deployed site — `PUBLIC_LEAD_ENDPOINT` would need to point at a publicly reachable URL.
- `cloudflared` (Cloudflare Tunnel, v2026.5.2) is installed and was the user-approved free option to expose the local n8n instance, but the tunnel has not been set up/published yet.
- This matches the `AGENTS.md` Deploy Gate condition: "Production deploys remain blocked until the lead pipeline is live and the WordPress site is intentionally cut over." **That condition is still not met.**

## 3. SEO / Structured Data Readiness (cross-reference `SEO_REPORT.md`)

- Meta titles/descriptions, canonical tags, OG/Twitter cards, JSON-LD (Organization, LocalBusiness, Service, FAQPage, BreadcrumbList), sitemap/robots, and hreflang for 6 locales are all implemented and rated "EXCELLENT" in the Phase 5 audit.
- Marketing/SEO technical foundation is ready independent of the lead-pipeline blocker.

## 4. Trust Signals / Claims

- Per Non-Negotiables in `AGENTS.md`: no Argelith/Zahna certification/partnership claims unless documented; Südzucker reference is confirmed real and approved (per `working_set.json` `hsb_suedzucker`); 5 further references remain anonymous (Level B, accepted as unbelegt-aber-anonymisiert).
- No new trust claims were added or changed in this session.

## 5. Outreach / Email

- Per `working_set.json` `hsb_outreach_2026-06-07`: an outreach system plan, email master template, and CRM/lead-control-table specs exist as planning docs, but `name@hsb-boden.de` mailbox + SMTP are not yet set up, and no real campaign has been sent (consistent with the "no unapproved email campaigns" Non-Negotiable).

---

## Summary / Go-Live Checklist (Marketing)

| Item | Status |
|---|---|
| SEO technical foundation | ✅ Done (Phase 5) |
| Accessibility | ✅ Done, 2 minor follow-ups (Phase 6) |
| Lead form UI | ✅ Implemented |
| Lead pipeline (n8n) — production webhook | ❌ **Blocker** — local-only, no public endpoint |
| `PUBLIC_LEAD_ENDPOINT` configured for prod | ❌ Blocked by above |
| Email/SMTP for outreach | ❌ Not set up |
| WordPress → Cloudflare cutover (DNS) | ❌ Not done (intentional, per Deploy Gate) |

No marketing-readiness item in this report required or received a code change in this session — this is a status consolidation only, per the "Plan-/Audit-Aufträge: nur Plan/Audit, keine Mutation" guardrail for items outside the approved CI/docs scope.
