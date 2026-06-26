# TURNSTILE_FORM_PROTECTION_READINESS — HSB-Boden / HEXAFLOOR

Status: `turnstile-planned-not-activated-server-side-validation-required`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No Turnstile site key activation performed. No Cloudflare Dashboard mutation.**
This document defines the readiness state and integration requirements for
Cloudflare Turnstile as optional bot/spam protection for the lead intake form.

Canonical Cloudflare truth: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`

---

## Current Form Protection State

The lead intake form at `src/pages/index.astro` (and the `/api/lead` endpoint at
`src/pages/api/lead.ts`) has no active bot protection beyond the Worker's CORS allowlist.

**Turnstile is not active.** The form works without it. Turnstile is optional hardening.

---

## Why Turnstile (Future Optional)

Cloudflare Turnstile provides:
- Non-intrusive CAPTCHA replacement (no image puzzles)
- Bot and spam form submission filtering
- Privacy-preserving — no cookies, no cross-site tracking
- Free tier covers all expected form volume for HSB

Without Turnstile, the `/api/lead` endpoint accepts any POST that passes CORS.
At current expected lead form volume (small B2B site), spam risk is low but not zero.

---

## Integration Requirements

### Frontend (Client-Side Widget)

Add to the form in `src/pages/index.astro` or the form component:

```html
<!-- Turnstile widget (invisible or managed challenge) -->
<div class="cf-turnstile"
     data-sitekey="TURNSTILE_SITE_KEY_PLACEHOLDER"
     data-callback="onTurnstileSuccess"
     data-theme="auto">
</div>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
```

The widget generates a one-time `cf-turnstile-response` token on successful challenge.
This token must be submitted with the form POST to `/api/lead`.

### Server-Side Validation (MANDATORY)

**Turnstile is only effective if the server validates the token.**
Client-side token generation alone provides no protection — bots can skip it.

In `src/pages/api/lead.ts`, add validation before processing the lead:

```typescript
// Server-side Turnstile validation (must be added before activation)
async function validateTurnstile(token: string, remoteip?: string): Promise<boolean> {
  const body = new URLSearchParams({
    secret: env.TURNSTILE_SECRET_KEY, // Must be set as Worker secret
    response: token,
    ...(remoteip ? { remoteip } : {}),
  });

  const resp = await fetch(
    'https://challenges.cloudflare.com/turnstile/v0/siteverify',
    { method: 'POST', body }
  );
  const data = await resp.json() as { success: boolean };
  return data.success;
}
```

The `TURNSTILE_SECRET_KEY` must be set as a Worker secret (never hardcoded):

```bash
# Only after Turnstile site is created in Cloudflare Dashboard
npx wrangler secret put TURNSTILE_SECRET_KEY --name hsb-boden
```

### Worker Secret Required

| Secret | Worker | Status |
|--------|--------|--------|
| `TURNSTILE_SECRET_KEY` | `hsb-boden` | Not set — not activated |

Do not set this secret until a Turnstile site has been created in Cloudflare Dashboard
and the server-side validation code is merged and deployed.

---

## Activation Gate (All Must Pass Before Activation)

- [ ] Turnstile site created in Cloudflare Dashboard (Turnstile → Sites)
- [ ] Site key type selected: `Managed` (recommended) or `Invisible`
- [ ] Site key `TURNSTILE_SITE_KEY_PLACEHOLDER` replaced with real value in frontend
- [ ] `TURNSTILE_SECRET_KEY` set as Worker secret in `hsb-boden`
- [ ] Server-side validation code added to `src/pages/api/lead.ts`
- [ ] End-to-end test: submit real form → token generated → server validates → lead accepted
- [ ] Failure test: bypass attempt → token missing → server rejects with 400
- [ ] Deployment verified: `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
- [ ] Joel approval granted

---

## Test Mode (Safe Pre-Activation Testing)

Cloudflare Turnstile provides test keys for development/staging:

| Site Key | Behavior |
|----------|----------|
| `1x00000000000000000000AA` | Always passes |
| `2x00000000000000000000AB` | Always blocks |
| `3x00000000000000000000FF` | Forces interactive challenge |

Use test site key in preview environment only. Never in production with real leads.

---

## Cloudflare Dashboard Path

Dashboard: **Turnstile → Add a Site**

Fields to configure:
- Site name: `HSB-Boden Lead Form`
- Domain: `hsb-boden.de` (and optionally `hsb-boden.cherinojoel.workers.dev`)
- Widget type: `Managed` (recommended for B2B — minimal friction)

---

## Forbidden Actions

- No Turnstile activation without server-side validation code deployed
- No site key committed to git (use environment variable or build-time substitution)
- No secret key committed to git — must be a Worker secret
- No activation on production until full end-to-end test passes on preview

---

## Decision Summary

| State | Detail |
|-------|--------|
| Today | No Turnstile — form protected by CORS allowlist only |
| Optional next step | Create Turnstile site → add server-side validation → activate |
| Priority | Low — acceptable to go live without Turnstile, add post-launch |
| Blocker | Server-side validation is mandatory before any activation |
