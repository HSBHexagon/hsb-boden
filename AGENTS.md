# Project Rules: hsb-boden

## Purpose

Build a parallel Astro/Cloudflare relaunch for HSB that generates organic B2B leads while preserving the current WordPress live site until final approval.

## Non-Negotiables

- Do not mutate or replace the live WordPress site from this repo.
- Do not claim Argelith/Zahna certification, partnership, or endorsement unless documented and approved.
- Do not publish exact customer locations, logos, or names without explicit approval.
- Do not use competitor customer lists publicly.
- Do not activate or automate email campaigns to purchased contacts without legal review.

## Verification

Run before completion claims:

```bash
npm run test:run
npm run check
npm run build
```

For frontend changes, verify desktop and mobile rendering before launch.

## Content Model

Structured content lives under `src/data`. Add new service, industry, reference, or article entries there and let routes generate pages.

## Design Direction

Technical, industrial, robust, quiet B2B interface. Avoid generic agency visuals, decorative hero gimmicks, or unsupported trust claims.
