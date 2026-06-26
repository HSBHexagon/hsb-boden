# EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `email-dns-records-verified-dkim-pending-migration-plan-ready`
Stand: 2026-06-26 | Canonical since this sweep.

No live mail send, no mailbox mutation, no bulk workflow activation performed here.
This document is readiness truth only.

---

## Canonical Sender and Mailboxes

| Address | Role | Status |
|---------|------|--------|
| `j-cherino@hsb-boden.de` | B2B outreach, flyer dispatch, all canonical acquisition contact | Active — no send until DKIM + approval |
| `info@hsb-boden.de` | General inquiries, legal, web form reply-to | Active — inbound/legal |
| `cherinodiaz@outlook.com` | Historical personal fallback only | Not a canonical outreach channel |

Outlook (`cherinodiaz@outlook.com`) is documented as historical fallback only.
All production outreach uses `j-cherino@hsb-boden.de` via Microsoft 365.

---

## Current DNS Mail Records (Verified via `dig`, 2026-06-26)

### MX

```
10 hsbboden-de0i.mail.protection.outlook.com.
```

Microsoft 365 / Exchange Online is the mail provider.

### SPF (TXT on apex)

```
v=spf1 include:spf.protection.outlook.com -all
```

Hard `-all`. Only M365 servers authorized to send for `hsb-boden.de`. Status: **PRESENT**.

### DMARC (`_dmarc.hsb-boden.de`)

```
v=DMARC1; p=none;
```

Monitoring mode. No enforcement action. No `rua`/`ruf` reporting configured. Status: **PRESENT**.

### DKIM Selectors

```
selector1._domainkey.hsb-boden.de → (no CNAME present)
selector2._domainkey.hsb-boden.de → (no CNAME present)
```

M365 requires `selector1._domainkey` and `selector2._domainkey` CNAME records.
Both are **missing** (verified via `dig CNAME`, 2026-06-26).
DKIM signing is not active. This must be resolved before production outreach.

### Autodiscover (CNAME)

```
autodiscover.hsb-boden.de → autodiscover.outlook.com.
```

Live and verified via `dig`, 2026-06-26. Must be preserved through NS switch.

### Current Nameservers

```
ns5.kasserver.com.
ns6.kasserver.com.
```

### Current A Record (WordPress origin)

```
85.13.130.17  (Kasserver WordPress hosting)
```

---

## SPF / DKIM / DMARC Readiness

### SPF — READY

`v=spf1 include:spf.protection.outlook.com -all` is live and correct.
Copy 1:1 to Cloudflare DNS (DNS-only, no proxy) during NS switch.

### DKIM — MISSING — Action Required Before Outreach

M365 DKIM must be activated in Microsoft 365 Admin Center:

1. M365 Admin Center → Settings → Domains → `hsb-boden.de`
   or Exchange Admin Center → Policies → DKIM
2. Enable DKIM for `hsb-boden.de` — M365 generates two CNAME values
3. Add those CNAMEs to DNS (Kasserver dashboard, before NS switch)
   or directly in Cloudflare (after NS switch, DNS-only):
   - `selector1._domainkey.hsb-boden.de` → `selector1-hsbbodende._domainkey.cherinojoel.onmicrosoft.com.`
   - `selector2._domainkey.hsb-boden.de` → `selector2-hsbbodende._domainkey.cherinojoel.onmicrosoft.com.`
   (Retrieve exact values from M365 Admin Center — above are schema examples)
4. After NS switch: ensure same CNAMEs are in Cloudflare as DNS-only records

Without DKIM: outbound mail from `j-cherino@hsb-boden.de` scores lower for spam filters.
DKIM is mandatory for B2B outreach deliverability.

### DMARC — PRESENT (`p=none`) — Harden After Stabilization

Current `p=none` is correct for initial phase (monitoring only).

After 2–4 weeks of stable mail operation with DKIM active:
- Upgrade to `p=quarantine` or `p=reject`
- Add reporting: `rua=mailto:dmarc@hsb-boden.de` (or external aggregator)

Future schema:
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@hsb-boden.de; pct=100;
```

---

## NS Switch Mail Record Migration List

The following records must exist in Cloudflare DNS before or immediately after NS switch.
All mail records must be **DNS-only (grey cloud)** — Cloudflare does not proxy mail.

| Type | Name | Value | Priority | Proxy |
|------|------|-------|----------|-------|
| MX | `hsb-boden.de` | `hsbboden-de0i.mail.protection.outlook.com.` | 10 | DNS-only |
| TXT | `hsb-boden.de` | `v=spf1 include:spf.protection.outlook.com -all` | — | DNS-only |
| TXT | `hsb-boden.de` | `MS=ms97748082` | — | DNS-only |
| TXT | `_dmarc.hsb-boden.de` | `v=DMARC1; p=none;` | — | DNS-only |
| CNAME | `autodiscover.hsb-boden.de` | `autodiscover.outlook.com.` | — | DNS-only |
| CNAME | `selector1._domainkey.hsb-boden.de` | (from M365 Admin Center) | — | DNS-only |
| CNAME | `selector2._domainkey.hsb-boden.de` | (from M365 Admin Center) | — | DNS-only |

Mail records must be entered before Cloudflare routes for `hsb-boden.de/*` are activated,
to prevent mail disruption during DNS propagation.

---

## Inbound Reply Handling

- `info@hsb-boden.de` receives general and legal inbound mail
- `j-cherino@hsb-boden.de` receives outreach replies; Joel monitors and logs to CRM
- No automated inbound routing or auto-reply is configured or required

---

## Cloudflare Email Routing — Strategy Note

Cloudflare Email Routing can forward `@hsb-boden.de` addresses to external mailboxes.
Only activatable after NS switch. Not required if M365 mailboxes are fully configured.

**Recommended path (Option B — M365 primary):**
- MX stays on `hsbboden-de0i.mail.protection.outlook.com.`
- No Cloudflare Email Routing for outbound-sending addresses
- Cloudflare Email Routing is only for inbound forwarding; it does not handle outbound
- If `j-cherino@hsb-boden.de` is a full M365 mailbox, no Cloudflare Email Routing needed

---

## Pre-Outreach Readiness Checklist

Completed:
- [x] MX, SPF, DMARC verified via `dig` and documented
- [x] Autodiscover CNAME verified live
- [x] Mail provider confirmed as M365
- [x] Canonical outreach address: `j-cherino@hsb-boden.de`
- [x] General address: `info@hsb-boden.de`
- [x] Outlook fallback correctly classified as historical only
- [x] NS switch migration list complete

Blocked (must complete before any production outreach):
- [ ] M365 Admin Center: enable DKIM for `hsb-boden.de`, obtain CNAME values
- [ ] Add DKIM CNAME records to current DNS (Kasserver) or Cloudflare after switch

Blocked (after NS switch):
- [ ] All mail records in Cloudflare Dashboard — DNS-only
- [ ] Test mail from `j-cherino@hsb-boden.de`, verify headers (DKIM pass, SPF pass, DMARC pass)
- [ ] DMARC hardening after 2–4 weeks stable operation

---

## Stop Condition

No live mail send, no batch, no dispatch is permitted until:
- DKIM is activated and verified
- Recipient basis documented per recipient
- Opt-out wording approved
- Batch approved per `docs/launch/PHASE_7_COMPLIANCE_GATE.md`

If DNS/NS is not active and no lead data exists, stop.

---

## Reference

- Templates and opt-out handling: `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md`
- CRM dispatch workflow: `docs/crm/CRM_LIGHT_OPERATOR_READINESS.md`
- Master go-live checklist: `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md`
