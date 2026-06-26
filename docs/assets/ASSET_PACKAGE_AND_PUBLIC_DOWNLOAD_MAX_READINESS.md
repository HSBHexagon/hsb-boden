# ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `assets-ready-deployed-awaiting-custom-domain`
Stand: 2026-06-26 | Canonical since this sweep.

No asset mutation, no R2 upload, no unapproved customer logos or references added here.
This document is readiness truth only.

---

## Canonical PDF Flyer Inventory

All three flyers exist in `public/` and are deployed on the production worker.
Validation evidence: `marketing/flyer/validation.md` — all 20 acceptance criteria passed.

| File | Size | Purpose |
|------|------|---------|
| `public/HSB-Flyer-Joel-Cherino.pdf` | 254 KB | Joel Cherino Diaz — canonical outreach variant |
| `public/HSB-Flyer-Jordie-Post.pdf` | 253 KB | JORDIE Post — alternative representative variant |
| `public/HSB-Flyer-Geschaeftsfuehrer.pdf` | 253 KB | Managing director variant (general) |

### Public URLs After DNS Switch

```
https://hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf
https://hsb-boden.de/HSB-Flyer-Jordie-Post.pdf
https://hsb-boden.de/HSB-Flyer-Geschaeftsfuehrer.pdf
```

Currently accessible on workers.dev (not linked, not for outreach use):
```
https://hsb-boden.cherinojoel.workers.dev/HSB-Flyer-Joel-Cherino.pdf
```

---

## Other Static Assets (`public/`)

| Path | Contents |
|------|----------|
| `public/brand/` | Brand assets |
| `public/logos/` | Logo variants |
| `public/media/` | Media files |
| `public/_redirects` | Cloudflare Workers Static Assets redirect rules |

### `_redirects` Rules (Active)

`public/_redirects` is natively evaluated by the Cloudflare Workers `[assets]` binding.
Two active rules (verified 2026-06-26):

```
/ueber-uns   /  301
/ueber-uns/  /  301
```

No separate Cloudflare Rule needed. Verify after custom domain go-live:
`https://hsb-boden.de/ueber-uns` → 301 to `/`.

---

## Flyer Source Assets (`marketing/flyer/assets/`)

Source files for the HTML/CSS flyer renderer (`flyer.html`, `flyer.css`, `render-flyer.mjs`).
Not for direct public download.

| File | Type | Note |
|------|------|------|
| `biovegan.svg` | Reference logo | **Approval required before external use** |
| `meggle.svg` | Reference logo | **Approval required before external use** |
| `suedzucker.svg` | Reference logo | **Approval required before external use** |
| `detail.jpg` | Product image | HSB internal |
| `hero.jpg` | Header image | HSB internal |
| `logo-dark.jpg` | HSB logo dark | HSB internal |
| `logo-light.jpg` | HSB logo light | HSB internal |
| `qr.svg` | QR code | Points to canonical domain |

**Reference logos (biovegan, meggle, suedzucker):** These are existing customer/partner
references. Do not use on new materials, campaigns, or public pages without explicit
documented approval. Operator must verify current customer relationship before each use.

---

## `marketing/flyer/final/` vs `public/` — Clarification

`marketing/flyer/final/` contains 2 PDFs (Joel-Cherino, Jordie-Post).
`HSB-Flyer-Geschaeftsfuehrer.pdf` is only in `public/`.

This is not a defect. `public/` is the deployment source; `marketing/flyer/final/` is the
render output directory. `public/` copies are canonical. No copy action required.

---

## Public Asset Readiness Matrix

| Asset | In Repo | In Build | Workers-Dev | Custom Domain (after switch) |
|-------|---------|----------|-------------|------------------------------|
| HSB-Flyer-Joel-Cherino.pdf | ✅ | ✅ | ✅ | ⬜ after switch |
| HSB-Flyer-Jordie-Post.pdf | ✅ | ✅ | ✅ | ⬜ after switch |
| HSB-Flyer-Geschaeftsfuehrer.pdf | ✅ | ✅ | ✅ | ⬜ after switch |
| Brand assets (`brand/`, `logos/`) | ✅ | ✅ | ✅ | ⬜ after switch |

---

## Public Download Strategy

### Canonical Public Asset Paths

Base: `https://hsb-boden.de/<filename>`
No subdirectory required for flyers — they serve directly from `public/`.

### Naming Convention

`HSB-Flyer-<PersonOrRole>.pdf` — PascalCase, hyphen-separated.
Do not change filenames without updating all links and QR codes pointing to them.

### Versioning Rule

If a flyer is updated, replace the file in `public/` and `marketing/flyer/final/`.
Keep old versions in `marketing/flyer/archive/` if needed for reference.
Do not add version numbers to filenames unless explicitly required (breaks QR/UTM links).

### QR / Landing Page / UTM Consistency

QR codes in the current flyers point to the canonical domain `hsb-boden.de`.
If UTM parameters are used in future flyer revisions:
- Keep UTM source/medium/campaign consistent across QR and email links
- Document in `marketing/flyer/validation.md`
- Verify QR decode before printing

### No R2 Requirement

All public assets are served via the Cloudflare Workers Static Assets binding
(`[assets]` in `wrangler.toml`, `binding = "ASSETS"`) from `dist/`.
No R2 bucket is required unless a real large-file or media streaming need arises.

---

## Approval Boundaries

| Item | Status |
|------|--------|
| Flyer PDF content | Validated — all 20 QA criteria passed |
| Customer logos (biovegan, meggle, suedzucker) | **Approval required per use** |
| Customer names as text references | **Approval required per use** |
| Unapproved locations or project data | **Forbidden** |
| Fake customer names or generated PII | **Forbidden** |
| Real lead list or PII in git | **Forbidden** |

---

## Post-DNS Asset Verification Checklist

After NS switch and route activation:

- [ ] `https://hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf` → 200, Content-Type: application/pdf
- [ ] `https://hsb-boden.de/HSB-Flyer-Jordie-Post.pdf` → 200, Content-Type: application/pdf
- [ ] `https://hsb-boden.de/HSB-Flyer-Geschaeftsfuehrer.pdf` → 200, Content-Type: application/pdf
- [ ] `https://hsb-boden.de/ueber-uns` → 301 redirect to `/`
- [ ] QR codes in flyers resolve correctly to live domain
- [ ] Lighthouse re-audit after custom domain activation

---

## Flyer Dispatch — Send-Readiness

Flyers are validated. Dispatch remains blocked until:
1. DKIM activated for `j-cherino@hsb-boden.de`
2. Recipient list approved with documented basis
3. Opt-out wording approved
4. Exact batch approved per `docs/launch/PHASE_7_COMPLIANCE_GATE.md`

See: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`

---

## Reference

- UTM and QR link strategy: `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`
- R2 asset offloading (future): `docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`
- Email templates and flyer links: `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md`
- Master go-live checklist: `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md`
