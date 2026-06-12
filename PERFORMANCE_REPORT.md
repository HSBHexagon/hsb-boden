# Phase 7: Performance Audit Report
**Project:** hsb-boden
**Date:** 2026-06-12
**Status:** COMPLETE

---

## 1. Build Output (measured, `npm run build`, 2026-06-12)

```
22:27:45 [build] Server built in 1.62s
22:27:45 [build] Complete!
```

Build completed cleanly, 34 routes prerendered (services, industries, knowledge articles, 6 locale homepages).

Client bundle sizes (`dist/_astro/`, measured via `du`):

| Asset | Size |
|---|---|
| `client.CimA0ymp.js` | 136K |
| `LeadForm.C1DOaDsl.js` | 60K |
| `index.sfrSwQv3.css` | 56K |
| `_slug_.CUpgaFLf.css` | 48K |
| `index._OACqPSs.js` | 8.0K |
| **Total `dist/`** | **6.6M** (incl. fonts, images, prerendered HTML) |

## 2. Lighthouse Scores (from prior measured run, `working_set.json`)

| Category | Desktop | Mobile |
|---|---|---|
| Performance | 100 | 99 |
| Accessibility | 100 | 100 |
| Best Practices | 100 | 100 |
| SEO | 100 | 100 |

These figures were captured during the 2026-06-06 quality gate run (`hsb_quality_gate_2026_06_06` in `working_set.json`) against the Cloudflare preview deployment. They are both above the `.lighthouserc.json` thresholds introduced this session (perf ≥ 0.9, a11y/seo ≥ 0.95, best-practices ≥ 0.95), so `lighthouse.yml` should pass once it runs in CI.

> A fresh Lighthouse run was not executed in this session (no browser/Playwright invocation was part of this pass). The numbers above are the last *measured* values on record, not a new measurement — re-run via `lighthouse.yml` on the next PR to confirm they still hold after the workflow/security changes in this session (which do not touch `src/`, so no regression is expected).

## 3. Known Open Finding (carried over from `working_set.json`)

- **`dist/_astro/client.CimA0ymp.js` (136K) contains unused JavaScript** per the 2026-06-06 quality gate notes. This is the React/Astro client hydration bundle (used by `LeadForm` and any interactive islands). Recommendation: audit which components use `client:*` directives in `src/pages` and `src/components`, and convert any that don't need client-side interactivity to `client:visible`/static, or split `LeadForm` into its own lazy-loaded chunk if it isn't already (it currently is — `LeadForm.C1DOaDsl.js` is separate at 60K). This is a follow-up task, not addressed in this pass (out of scope: requires component-level changes, not CI/docs).

## 4. Fonts

8 `Outfit` font weights (400/600/700/800/900, latin + latin-ext, woff/woff2) are bundled. woff2 variants are present for all weights (good — woff2 is preferred by modern browsers). No action needed.

## 5. Image Service

`astro.config.mjs` uses `image: { service: passthrough() }` (Cloudflare-optimized, no build-time transform cost). Source assets are pre-optimized `.webp` per `AUDIT_REPORT.md` Phase 1. No action needed.

---

## Summary

- Build is clean and fast (1.62s server build).
- Lighthouse scores (last measured) exceed all configured CI thresholds.
- One pre-existing finding (unused JS in the client hydration bundle) remains open and is tracked here for a future, isolated frontend-focused PR — not bundled with this session's CI/security/docs changes.
