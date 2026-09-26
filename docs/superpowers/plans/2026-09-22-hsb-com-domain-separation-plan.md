# HSB Sales OS — Domain-Separation & .com Outbound-Pipeline

> **Für KI-Arbeiter:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Ziel:** Die E-Mail-Akquise von `hsb-boden.de` auf `hsb-boden.com` verlagern, um die primäre .de-Domain dauerhaft vor Reputationsschäden zu schützen. Senden über .com via SMTP (ALL-INKL Kasserver), Antworten per Reply-To an .de-Postfächer.

**Architektur-Entscheidung (radikal ehrlich):**

| Option | Bewertung | Begründung |
|--------|-----------|------------|
| **A) ALL-INKL SMTP direkt** | ✅ **EMPFOHLEN für Start** | Bereits bezahlt, Zugänge vorhanden, kein neues Abo nötig. Python smtplib direkt. Limit: ~1.000 Mails/Tag (KAS-Tarif-abhängig). |
| B) Google Workspace | ⚡ Beste Zustellbarkeit | ~7€/User/Monat. Googles Sender-Reputation ist höher als Kasserver. Aber: Neues Abo, neuer OAuth-Flow, höhere Kosten. |
| C) Cloudflare Email Service | ❌ Nicht geeignet | Nur transaktionale E-Mails. Kein Postfach, kein IMAP. Kein B2B-Akquise-Tool. |
| D) Resend/SendGrid SMTP Relay | ❌ Nicht empfohlen | Cold Outreach in AGB verboten. Shared IPs. Reputation-Risiko. |

**Empfehlung:** Starte mit **Option A** (ALL-INKL SMTP). Wenn Volumen > 200 Mails/Tag nötig wird → Migration zu Google Workspace.

## Global Constraints

- Hermetic Safety Law: `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` bis zum expliziten Go-Live.
- Managing Director: Verbatim `Jordie Post` (mit `-ie`).
- Reply-To: Alle Antworten gehen an `.de`-Postfächer.
- Domain-Warmup: 14-21 Tage graduelles Warmup Pflicht.
- DNS: SPF + DKIM + DMARC `p=quarantine` auf `.com` vor erstem Versand.

---

## Task 1: DNS-Hardening für hsb-boden.com

**Ziel:** SPF, DKIM, DMARC korrekt setzen, bevor eine einzige Mail versendet wird.

**Sub-Steps:**

- [ ] 1.1 — DNS-Provider der .com-Domain ermitteln (ALL-INKL KAS-Panel oder Cloudflare)
- [ ] 1.2 — SPF-Record setzen: `v=spf1 mx a include:kasserver.com -all`
- [ ] 1.3 — DKIM im KAS-Panel aktivieren (unter E-Mail → DKIM) und TXT-Record `mail._domainkey.hsb-boden.com` prüfen
- [ ] 1.4 — DMARC setzen: `v=DMARC1; p=quarantine; rua=mailto:postmaster@hsb-boden.com; adkim=s; aspf=r`
- [ ] 1.5 — MX-Records auf Kasserver setzen (falls nicht automatisch)
- [ ] 1.6 — DNS-Verifizierung: `dig TXT hsb-boden.com`, `dig MX hsb-boden.com`, `dig TXT mail._domainkey.hsb-boden.com`
- [ ] 1.7 — Deliverability-Test senden: manuell eine Test-Mail von j-cherino@hsb-boden.com an j-cherino@hsb-boden.de

**Acceptance:** Alle DNS-Records propagiert, Test-Mail kommt im .de-Postfach an.

---

## Task 2: SMTP-Sender-Modul für ALL-INKL

**Ziel:** Python-Modul `engine/smtp_com_sender.py` das über ALL-INKL SMTP (.com) E-Mails versendet.

**Sub-Steps:**

- [ ] 2.1 — RED: Tests schreiben für `smtp_com_sender.py`:
  - `test_send_draft_via_smtp_mocked` — SMTP-Verbindung gemockt, prüft `Reply-To: .de`
  - `test_fail_closed_on_missing_smtp_credentials` — ValueError bei fehlenden Credentials
  - `test_reply_to_header_points_to_de` — `Reply-To` Header verifizieren
  - `test_from_header_uses_com_domain` — `From` Header verifizieren
  - `test_attachment_flyer_attached` — MIME multipart mit Flyer
- [ ] 2.2 — GREEN: `smtp_com_sender.py` implementieren:
  ```python
  SMTP_CONFIG = {
      "JOEL": {
          "host": "w0221a9f.kasserver.com",
          "port": 465,
          "user": "m0821e5d",
          "from": "j-cherino@hsb-boden.com",
          "reply_to": "j-cherino@hsb-boden.de",
      },
      "JORDI": {
          "host": "w0221a9f.kasserver.com",
          "port": 465,
          "user": "m0821e5b",
          "from": "j-post@hsb-boden.com",
          "reply_to": "j-post@hsb-boden.de",
      },
  }
  ```
  - `smtplib.SMTP_SSL` mit Port 465
  - MIME multipart: HTML body + Flyer PDF attachment
  - `Reply-To` Header auf `.de`
  - `From` Header auf `.com`
  - Passwörter aus Environment-Variables: `HSB_SMTP_JOEL_PW`, `HSB_SMTP_JORDI_PW`
- [ ] 2.3 — Tests grün
- [ ] 2.4 — Commit: `feat(sales-os): add SMTP .com sender with reply-to .de routing`

**SICHERHEIT:** Passwörter NIEMALS im Code. Nur über `os.environ`. `.env`-Datei in `.gitignore`.

**Acceptance:** 5 Tests grün, SMTP-Modul sendet über .com mit Reply-To .de.

---

## Task 3: Canonical Template Factory — .com Erweiterung

**Ziel:** `canonical_template_factory.py` erweitern um `.com`-Absender-Konfiguration.

**Sub-Steps:**

- [ ] 3.1 — RED: Tests für .com-Modus:
  - `test_render_canonical_email_com_domain` — `sender_email` endet auf `.com`
  - `test_render_canonical_email_reply_to_de` — Reply-To auf `.de`
  - `test_render_canonical_email_de_fallback` — Default bleibt `.de` (Abwärtskompatibilität)
- [ ] 3.2 — GREEN: `render_canonical_email()` um Parameter `domain="de"` erweitern:
  - `domain="com"` → From: `.com`, Reply-To: `.de`, Logo-URL bleibt `.de`
  - `domain="de"` → Bisheriges Verhalten (Default, keine Regression)
  - Signatur-Block: Absender-E-Mail anpassen, Website bleibt `hsb-boden.de`
  - Abmelde-Link bleibt `hsb-boden.de/abmelden` (UGC-Domain unverändert)
- [ ] 3.3 — Bestehende 5 Tests weiterhin grün (keine Regression)
- [ ] 3.4 — Commit: `feat(sales-os): extend canonical template factory with .com domain mode`

**Acceptance:** 8 Tests grün (5 bestehende + 3 neue), Abwärtskompatibilität gewahrt.

---

## Task 4: Draft-vs-Send Governance Layer

**Ziel:** Zentraler Schalter der zwischen Draft-Erstellung (Graph API) und echtem SMTP-Versand (.com) unterscheidet.

**Sub-Steps:**

- [ ] 4.1 — RED: Tests für `send_governance.py` Erweiterung:
  - `test_send_mode_draft_creates_graph_draft` — Mode "draft" erzeugt Graph-API-Request
  - `test_send_mode_smtp_calls_smtp_sender` — Mode "smtp" ruft `smtp_com_sender` auf
  - `test_send_mode_default_is_draft` — Default bleibt Draft (Safety)
  - `test_real_send_count_guardrail_smtp` — Counter wird hochgezählt
- [ ] 4.2 — GREEN: `engine/send_dispatch.py` implementieren:
  ```python
  SEND_MODE = os.environ.get("HSB_SEND_MODE", "draft")  # "draft" | "smtp"
  
  def dispatch_email(lead, owner, mode=None):
      effective_mode = mode or SEND_MODE
      email = render_canonical_email(lead, owner, domain="com" if effective_mode == "smtp" else "de")
      if effective_mode == "draft":
          return create_graph_draft(email)  # bisheriges Verhalten
      elif effective_mode == "smtp":
          return send_via_smtp(email)  # neuer .com SMTP-Pfad
  ```
- [ ] 4.3 — Tests grün, `REAL_EXTERNAL_PROSPECT_SEND_COUNT` bleibt 0 bis expliziter Freigabe
- [ ] 4.4 — Commit: `feat(sales-os): add send dispatch layer (draft vs smtp) with fail-safe default`

**Acceptance:** 4+ Tests grün, Default ist immer Draft, SMTP nur mit explizitem Opt-in.

---

## Task 5: Domain-Warmup-Plan & Monitoring

**Ziel:** Strukturierter Warmup-Plan für hsb-boden.com.

**Sub-Steps:**

- [ ] 5.1 — `docs/warmup-plan-hsb-boden-com.md` erstellen:
  ```
  Woche 1 (Tag 1-7):   5 Mails/Tag/Postfach → 10 Mails am Tag 5
  Woche 2 (Tag 8-14):  15 Mails/Tag/Postfach → 25 Mails am Tag 12
  Woche 3 (Tag 15-21): 30 Mails/Tag/Postfach → 50 Mails am Tag 21
  Woche 4+:            50-100 Mails/Tag/Postfach (stabil)
  ```
- [ ] 5.2 — Warmup-Limiter in `send_dispatch.py`:
  ```python
  WARMUP_DAILY_LIMIT = int(os.environ.get("HSB_WARMUP_DAILY_LIMIT", "5"))
  ```
  - Automatischer Abbruch wenn Tageslimit erreicht
  - Log: "Warmup limit reached: {count}/{limit} for {date}"
- [ ] 5.3 — Monitoring: DNS-Audit Script erweitern um .com-Domain
- [ ] 5.4 — Commit: `feat(sales-os): add domain warmup plan and daily limiter`

**Acceptance:** Warmup-Plan dokumentiert, Limiter getestet, DNS-Audit deckt .com ab.

---

## Task 6: Integration Test — End-to-End Dry-Run

**Ziel:** Voller Durchlauf mit 1 Test-Lead über den neuen .com-SMTP-Pfad.

**Sub-Steps:**

- [ ] 6.1 — Test-Lead erstellen (eigene E-Mail-Adresse als Empfänger)
- [ ] 6.2 — `send_dispatch.py --mode smtp --owner JOEL --lead TEST_LEAD` ausführen
- [ ] 6.3 — Prüfen:
  - Mail kommt an ✓
  - From: `j-cherino@hsb-boden.com` ✓
  - Reply-To: `j-cherino@hsb-boden.de` ✓
  - DKIM-Signatur valide ✓
  - SPF pass ✓
  - Flyer-Anhang vorhanden ✓
  - Antwort landet im .de-Postfach ✓
- [ ] 6.4 — Commit: `test(sales-os): verify .com SMTP end-to-end with reply-to .de`

**Acceptance:** E-Mail zugestellt, alle Header korrekt, Antwort kommt bei .de an.

---

## Architektur-Diagramm

```
                    ┌────────────────────┐
                    │   ALL_LEADS Sheet   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ canonical_template  │
                    │ factory (domain=?)  │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   send_dispatch    │
                    │  mode=draft|smtp   │
                    └───┬───────────┬────┘
                        │           │
           ┌────────────▼───┐  ┌────▼───────────┐
           │  Graph API     │  │  ALL-INKL SMTP │
           │  (Draft .de)   │  │  (.com → senden)│
           │  bisheriger    │  │  Reply-To: .de  │
           │  Pfad          │  │  Port 465 SSL   │
           └────────────────┘  └────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  Empfänger-     │
                              │  Postfach       │
                              └────────┬────────┘
                                       │ Antwort
                              ┌────────▼────────┐
                              │  .de-Postfach   │
                              │  (via Reply-To) │
                              └─────────────────┘
```

## Risiken & Mitigationen

| Risiko | Schwere | Mitigation |
|--------|---------|------------|
| ALL-INKL sperrt bei zu viel Volumen | Hoch | Warmup-Limiter, max 50/Tag/Postfach initial |
| .com hat keine Reputation → Spam | Hoch | 14-21 Tage Warmup, DKIM+DMARC Pflicht |
| Passwörter im Code | Kritisch | Nur env vars, .env in .gitignore |
| Regression .de-Pfad | Mittel | Alle bestehenden Tests müssen weiterhin grün sein |
| Kasserver TLS-Zertifikat auf kasserver.com, nicht Custom-Domain | Niedrig | smtplib verifiziert Kasserver-Hostname |
