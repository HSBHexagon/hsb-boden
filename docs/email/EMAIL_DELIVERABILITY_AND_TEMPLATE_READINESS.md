# EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS — HSB-Boden / HEXAFLOOR

Status: `deliverability-documented-dkim-pending-templates-ready-no-send-approved`
Stand: 2026-06-26 | New doc — final pre-go-live documentation wave.

**No live mail sent. No mailbox mutated. No bulk workflow activated.**
This document consolidates deliverability readiness and outreach template structure.
Canonical email/deliverability truth: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`

---

## Canonical Outreach Channel

| Address | Role |
|---------|------|
| `j-cherino@hsb-boden.de` | All B2B outreach, flyer dispatch, canonical acquisition contact |
| `info@hsb-boden.de` | General inquiries, legal, web form reply-to |

All production outreach uses `j-cherino@hsb-boden.de` via Microsoft 365.
`cherinodiaz@outlook.com` is historical fallback only — not a production outreach address.

---

## Deliverability Status Summary

| Record | Status |
|--------|--------|
| MX | ✅ Live — `hsbboden-de0i.mail.protection.outlook.com.` |
| SPF | ✅ Live — `v=spf1 include:spf.protection.outlook.com -all` |
| DMARC | ✅ Live — `v=DMARC1; p=none;` (monitoring mode) |
| Autodiscover CNAME | ✅ Live — `autodiscover.hsb-boden.de → autodiscover.outlook.com.` |
| DKIM selector1 | ❌ Missing — must activate in M365 Admin Center |
| DKIM selector2 | ❌ Missing — must activate in M365 Admin Center |

**DKIM is the only remaining deliverability blocker.** No production outreach until DKIM is active
and a test mail from `j-cherino@hsb-boden.de` shows DKIM pass in headers.

### DKIM Activation Steps (Before Outreach)

1. Open M365 Admin Center → Settings → Domains → `hsb-boden.de`
   or Exchange Admin Center → Policies → DKIM
2. Enable DKIM for `hsb-boden.de`
3. M365 generates two CNAME values:
   - `selector1._domainkey.hsb-boden.de` → `selector1-hsbbodende._domainkey.cherinojoel.onmicrosoft.com.`
   - `selector2._domainkey.hsb-boden.de` → `selector2-hsbbodende._domainkey.cherinojoel.onmicrosoft.com.`
   (Retrieve exact values from M365 — above are schema examples only)
4. Add CNAMEs to current DNS (Kasserver dashboard) OR to Cloudflare DNS after NS switch
5. Test with: `dig CNAME selector1._domainkey.hsb-boden.de`
6. Send test mail from `j-cherino@hsb-boden.de` → verify headers show `dkim=pass`

### Test Mail Header Verification

After DKIM activation, send to a Gmail account and check headers:
```
Authentication-Results: mx.google.com;
  dkim=pass header.i=@hsb-boden.de header.s=selector1 ...;
  spf=pass ...;
  dmarc=pass ...;
```
All three (DKIM, SPF, DMARC) must show `pass` before production outreach.

---

## Outreach Email Templates (Structure Only)

Templates below are structure and placeholder examples.
No template may be sent without: real lead data, DKIM active, recipient basis documented,
opt-out wording approved, and batch approved per `docs/launch/PHASE_7_COMPLIANCE_GATE.md`.

### Template 1 — Initial Cold Outreach (Flyer Dispatch)

**Subject:** Industriebodenbeläge für [Firmenname] – Unser Angebot

**Body (plain text, adapt to recipient context):**

```
Guten Tag [Ansprechpartner],

mein Name ist Joel Cherino Diaz und ich bin Ihr Ansprechpartner bei der
HSB GmbH für industrielle Bodenbeläge und Beschichtungssysteme.

Wir spezialisieren uns auf:
- Mechanisch, chemisch und thermisch belastbare Industrieböden
- Neubau und Sanierung von Gewerbeflächen
- Lösungen für Lebensmittel-, Chemie- und Logistikbetriebe

Im Anhang finden Sie unsere Übersicht. Gerne bespreche ich Ihr Projekt in einem
kurzen Telefonat.

Mit freundlichen Grüßen
Joel Cherino Diaz
HSB GmbH
j-cherino@hsb-boden.de
[Telefonnummer einfügen]

---
Wenn Sie keine weiteren Informationen erhalten möchten, antworten Sie bitte
mit dem Betreff „Abmelden" auf diese E-Mail.
```

**Attachment:** `HSB-Flyer-Joel-Cherino.pdf` (254 KB)

### Template 2 — JORDI Post Variant

**Subject:** Industrieböden für [Firmenname] – Beratung von JORDI Post

**Body:** Same structure, adapted to JORDI's role and flyer variant (`HSB-Flyer-Jordi-Post.pdf`).

### Template 3 — Follow-Up (After No Reply, 14 Days)

**Subject:** Kurze Nachfrage – Bodenbeläge für [Firmenname]

```
Guten Tag [Ansprechpartner],

ich meldete mich vor etwa zwei Wochen wegen unserer Industrieböden.
Darf ich fragen, ob das Thema für [Firmenname] aktuell relevant ist?

Über eine kurze Rückmeldung würde ich mich freuen.

Freundliche Grüße
Joel Cherino Diaz
j-cherino@hsb-boden.de

---
Wenn Sie keine Nachrichten mehr erhalten möchten: kurze Antwort genügt.
```

### Template 4 — Flyer Download Follow-Up (Website Lead)

For leads who submitted the website form (auto-routed to CRM):

```
Guten Tag [Ansprechpartner],

vielen Dank für Ihr Interesse an unseren Industrieböden.
Ich melde mich kurz, um Ihr Projekt besser zu verstehen und
zu prüfen, ob wir helfen können.

Wann passt ein kurzes Telefonat?

Mit freundlichen Grüßen
Joel Cherino Diaz
j-cherino@hsb-boden.de
```

---

## Reply Address and Inbound Handling

All outreach emails from `j-cherino@hsb-boden.de` must use:
- **From:** `j-cherino@hsb-boden.de`
- **Reply-To:** `j-cherino@hsb-boden.de`
- No `noreply@` addresses for outreach
- `info@hsb-boden.de` for web form auto-reply only

### Inbound Reply Workflow

1. Reply arrives in M365 inbox for `j-cherino@hsb-boden.de`
2. Joel reads and categorizes
3. Update CRM row: Status → `geantwortet` or `qualifiziert`, Nächste Aktion → next step
4. Log in Notizen field: date, key message, outcome

---

## Opt-Out Handling

Every outreach email must include a clear unsubscribe instruction in plain text:
> "Wenn Sie keine weiteren Informationen erhalten möchten, antworten Sie bitte mit
> dem Betreff 'Abmelden' auf diese E-Mail."

On receipt of an opt-out reply:
1. Immediately set `Opt-out-Status = opted_out` in CRM row
2. Set `Versandfreigabe = no`
3. Never contact that recipient again without documented re-consent
4. Log date and content of opt-out request in Notizen

---

## Flyer Link Strategy in Emails

PDF flyers may be attached directly (under 300 KB each — within standard attachment limits)
or linked via the production URL after DNS switch:

```
https://hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf
```

With UTM parameters for tracking (see `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`):

```
https://hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer
```

Workers.dev URL must NOT be used in outreach emails — it is for internal testing only.

---

## Pre-Send Gate (All Required Before First Outreach Email)

- [ ] DKIM active — verified via `dig CNAME selector1._domainkey.hsb-boden.de`
- [ ] Test mail headers show dkim=pass, spf=pass, dmarc=pass
- [ ] Recipient basis documented per recipient in CRM (`Beziehung / Kontaktgrund` field)
- [ ] Opt-out wording approved by Joel
- [ ] First batch approved per `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
- [ ] `Versandfreigabe = yes` set per recipient in CRM
- [ ] No auto-send, no n8n outbound, no Apps Script outbound — manual only

---

## Stop Condition

If DKIM is not active or no lead data exists, stop.
Do not send any outreach email, even manually, until all items in the pre-send gate are checked.
