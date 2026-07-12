# R2_ASSET_UPLOAD_STRATEGY — HSB-Boden / HEXAFLOOR

Status: `strategy-documented-r2-not-activated-assets-on-worker-static`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No R2 bucket created, no R2 upload performed, no public bucket exposure made here.**
This document defines the future asset strategy for R2 if/when static asset offloading
becomes necessary. Current canonical asset delivery is via Cloudflare Workers Static Assets.

Canonical asset readiness: `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`
Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`

---

## Current Asset Delivery (Active — No R2 Required Today)

All PDF flyers and static files are in `public/` and served via the Cloudflare Worker
`[assets]` binding defined in `wrangler.toml`.

| File | Served From | Status |
|------|-------------|--------|
| `public/HSB-Flyer-Joel-Cherino.pdf` | Worker Static Assets | Deployed |
| `public/HSB-Flyer-Jordi-Post.pdf` | Worker Static Assets | Deployed |
| `public/HSB-Flyer-Geschaeftsfuehrer.pdf` | Worker Static Assets | Deployed |
| `public/_redirects` | Worker Static Assets | Active redirect rules |
| `public/brand/` | Worker Static Assets | Deployed |
| `public/logos/` | Worker Static Assets | Deployed |
| `public/media/` | Worker Static Assets | Deployed |

**R2 is not required for the current asset set.** Worker Static Assets handles all PDFs,
images, and media files up to Cloudflare's static asset limits without additional cost.

---

## When R2 Becomes Relevant

R2 should be considered only if:

1. **Asset size exceeds Worker Static Assets limits** — single files >25 MB or total
   asset bundle approaches size limits
2. **Video files** — MP4 product demos, installation guides, or testimonial videos that
   are too large for static asset deployment
3. **High-volume downloads** — if PDF flyer downloads generate measurable egress cost
   and R2 free tier (10 GB/month) would reduce cost
4. **Private/internal documents** — documents intended for authenticated operators only,
   combined with Cloudflare Access

---

## R2 Bucket Strategy (Future — Not Activated)

### Bucket Naming Convention (When Created)

| Bucket | Purpose | Access |
|--------|---------|--------|
| `hsb-boden-public` | Public PDFs, marketing materials | Public read (after approval) |
| `hsb-boden-private` | Internal operator docs, lead imports | Private — Cloudflare Access required |
| `hsb-boden-video` | Product demo videos (future) | Public read or signed URLs |

### Public Read Configuration (If Activated)

```toml
# wrangler.toml addition (do not add until approved)
[[r2_buckets]]
binding = "PUBLIC_ASSETS"
bucket_name = "hsb-boden-public"
preview_bucket_name = "hsb-boden-public-preview"
```

Public bucket activation requires:
1. Explicit approval from Joel
2. No customer PII, no lead data, no internal documents in the public bucket
3. CORS policy configured to allow only `hsb-boden.de` and `www.hsb-boden.de`

### Private Document Handling

Private operator documents (lead import templates, compliance docs, internal guides)
must never be in a public R2 bucket. If R2 is used for private docs:
- Cloudflare Access policy must gate the `/internal/*` or `/private/*` path
- No signed URL generation without explicit approval per batch

---

## Cloudflare Access — Private Document Strategy (Future)

If internal/private documents are stored in R2 or served via a Worker path:

```
Path: https://hsb-boden.de/internal/*
Gate: Cloudflare Access — one-time PIN to joel@... or JORDI's email
```

Cloudflare Access is not activated today. This is a future optional feature.
Activation requires: Access policy creation → email approval → test gate → approval.

---

## Asset Upload Process (When Approved)

### For Public PDFs (If Moving to R2)

```bash
# Only after approval and R2 bucket creation
npx wrangler r2 object put hsb-boden-public/HSB-Flyer-Joel-Cherino.pdf \
  --file public/HSB-Flyer-Joel-Cherino.pdf \
  --content-type application/pdf

npx wrangler r2 object put hsb-boden-public/HSB-Flyer-Jordi-Post.pdf \
  --file public/HSB-Flyer-Jordi-Post.pdf \
  --content-type application/pdf

npx wrangler r2 object put hsb-boden-public/HSB-Flyer-Geschaeftsfuehrer.pdf \
  --file public/HSB-Flyer-Geschaeftsfuehrer.pdf \
  --content-type application/pdf
```

### For Videos (Future)

```bash
# Only after video assets exist and approval is granted
npx wrangler r2 object put hsb-boden-video/demo-boden-sanierung.mp4 \
  --file media/demo-boden-sanierung.mp4 \
  --content-type video/mp4
```

---

## UTM and Tracking for R2-Served Assets

If assets move to R2, UTM tracking via URL parameters will no longer be embedded
in the file URL itself. Use a Worker redirect layer to:

1. Accept `GET /download/flyer-joel?utm_source=...`
2. Log the event to CRM (optional)
3. Redirect to R2 public URL or serve via `fetch()` from R2 binding

This pattern is documented in `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`.

---

## Forbidden Actions

- No R2 bucket creation without explicit approval
- No public bucket exposure without approval and CORS review
- No customer PII, lead data, or internal compliance documents in any public bucket
- No signed URL generation without per-batch approval
- No video upload without explicit media approval

---

## Decision Summary

| Today | Future (If Needed) |
|-------|--------------------|
| Worker Static Assets serves all PDFs | R2 for videos >25 MB or cost optimization |
| No R2 required | R2 `hsb-boden-public` for large/video assets |
| No Cloudflare Access required | Cloudflare Access for private internal docs |
| No additional wrangler config needed | `[[r2_buckets]]` binding addition required |

**Current recommendation: keep all assets in `public/` via Worker Static Assets.
R2 is not required and adds operational complexity without benefit at current scale.**
