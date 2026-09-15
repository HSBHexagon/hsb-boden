# UTM_QR_DOWNLOAD_MATRIX — HSB-Boden / HEXAFLOOR

Status: `utm-structure-verified-live-2026-08-11`
Stand: 2026-06-26, Host-Korrektur 2026-08-11 | Ursprünglich als "awaiting-dns"
(voller NS-Cutover) markiert — das ist überholt. Die Website läuft seit dem
Pages-Cutover live über `www.hsb-boden.de` (Cloudflare Pages), der Apex
`hsb-boden.de` leitet per 301 unter Erhalt aller Query-Parameter auf `www` um
(live per `curl -I` verifiziert, 2026-08-11). Die Basis-URLs unten sind daher
von `hsb-boden.de` auf `https://www.hsb-boden.de` korrigiert — kein separater
NS-Cutover mehr nötig.

**Live-Status 2026-08-11:** `https://www.hsb-boden.de/kontakt/` → HTTP 200.
Beide Flyer-PDFs → HTTP 200, `content-type: application/pdf`. UTM-Parameter
bleiben über den Apex→www-Redirect erhalten (verifiziert mit echtem
`utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer`-Test).
Workers.dev URLs sind weiterhin nur für internes Testing — nie für Outreach.

Canonical asset readiness: `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`

---

## UTM Parameter Convention

| Parameter | Values | Purpose |
|-----------|--------|---------|
| `utm_source` | `email`, `qr`, `linkedin`, `xing`, `print` | Where the click originated |
| `utm_medium` | `outreach`, `flyer`, `social`, `direct` | Channel type |
| `utm_campaign` | `kaltakquise-2026-q3`, `messe-2026`, `followup-batch-01` | Campaign name (date-stamped) |
| `utm_content` | `joel-flyer`, `jordi-flyer`, `gf-flyer`, `homepage-link` | Which specific asset/link |
| `utm_term` | (optional) `lebensmittel`, `chemie`, `logistik` | Industry segment |

All parameter values must be lowercase with hyphens. No spaces. No special characters.

---

## Production URLs (Live seit Pages-Cutover, verifiziert 2026-08-11)

Base: `https://www.hsb-boden.de`

### PDF Flyer Direct URLs

```
https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf
https://www.hsb-boden.de/HSB-Flyer-Jordi-Post.pdf
https://www.hsb-boden.de/HSB-Flyer-Geschaeftsfuehrer.pdf
```

### Homepage with UTM

```
https://www.hsb-boden.de/?utm_source=qr&utm_medium=flyer&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer
```

### PDF Download with UTM (Linked in Email)

```
https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer

https://www.hsb-boden.de/HSB-Flyer-Jordi-Post.pdf?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=jordi-flyer
```

> **Note:** UTM parameters on direct PDF links are captured by GA4 as referral context
> only if the user navigates from the PDF to the website. For tracking PDF downloads,
> use the `pdf_download` GA4 event on the click, not UTM on the file URL itself.
> UTM on PDF links is useful for QR codes pointing to the PDF where GA4 cannot fire.

---

## UTM Matrix by Channel

### Email Outreach

| Asset | UTM URL |
|-------|---------|
| Joel flyer link in email | `?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer` |
| JORDI flyer link in email | `?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=jordi-flyer` |
| Homepage link in email | `?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=homepage-link` |

### Printed Flyer QR Code

| Asset | Target URL | QR Points To |
|-------|-----------|--------------|
| Joel Cherino flyer | `https://www.hsb-boden.de/?utm_source=qr&utm_medium=flyer&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer` | Homepage with UTM |
| JORDI Post flyer | `https://www.hsb-boden.de/?utm_source=qr&utm_medium=flyer&utm_campaign=kaltakquise-2026-q3&utm_content=jordi-flyer` | Homepage with UTM |
| Geschäftsführer flyer | `https://www.hsb-boden.de/?utm_source=qr&utm_medium=flyer&utm_campaign=kaltakquise-2026-q3&utm_content=gf-flyer` | Homepage with UTM |

QR codes on printed flyers should point to the **homepage with UTM**, not directly to the PDF.
This ensures GA4 fires on the landing page and the session is attributed correctly.

### Trade Show / Event

| Asset | UTM URL |
|-------|---------|
| Messe stand QR | `?utm_source=qr&utm_medium=flyer&utm_campaign=messe-2026&utm_content=messe-stand` |
| Direct link | `?utm_source=direct&utm_medium=referral&utm_campaign=messe-2026` |

### LinkedIn / Xing (Future)

| Asset | UTM URL |
|-------|---------|
| LinkedIn post link | `?utm_source=linkedin&utm_medium=social&utm_campaign=kaltakquise-2026-q3` |
| Xing post link | `?utm_source=xing&utm_medium=social&utm_campaign=kaltakquise-2026-q3` |

---

## QR Code Generation Strategy

### When to Generate QR Codes

Production ist live (verifiziert 2026-08-11) — QR-Codes können mit den
Production-URLs oben generiert werden. Weiterhin nie mit workers.dev-URLs.

### Recommended QR Generation Tools

| Tool | Type | Notes |
|------|------|-------|
| `qrencode` (CLI) | Local, open-source | `qrencode -o flyer-joel.png "https://www.hsb-boden.de/?utm_source=qr..."` |
| qr-code-generator.com | Web | Free, no account needed |
| Canva QR widget | Design integrated | If flyers are edited in Canva |

### QR Code Specifications

| Parameter | Value |
|-----------|-------|
| Format | PNG, minimum 1000×1000 px for print |
| Error correction | Level M (15% data recovery) |
| Quiet zone | Minimum 4 modules |
| Color | Black on white — no color QR for print reliability |

### QR Test Before Print

After generating a QR code:
1. Scan with iPhone camera — verify it opens the correct UTM URL
2. Verify the page loads in production (`hsb-boden.de`)
3. Check GA4 DebugView — confirm `qr_landing` event fires
4. Only then approve for print

---

## Campaign Naming Convention

Pattern: `[scope]-[year]-[quarter|event]`

Examples:
- `kaltakquise-2026-q3` — cold outreach campaign Q3 2026
- `messe-2026` — trade show general
- `followup-batch-01` — follow-up wave 1

New campaign names must be documented in CRM-Light `Kampagne` field and logged here
if they represent a new wave.

---

## UTM Tracking Verification

After DNS switch and first campaign:

```bash
# Check GA4 Realtime or DebugView for campaign sessions
# Open: https://analytics.google.com → GA4 Property G-VC4BJBEFTV → Reports → Realtime
# Filter by: Session campaign = kaltakquise-2026-q3
```

GA4 Acquisition report (after 24h data):
- **Reports → Acquisition → Traffic acquisition**
- Group by: Session source / medium
- Expected row: `email / outreach` or `qr / flyer`

---

## Forbidden

- No workers.dev URLs in any outreach material, printed flyer, or QR code
- No UTM parameters capturing PII
- No campaign names created without documenting in this file or CRM field
