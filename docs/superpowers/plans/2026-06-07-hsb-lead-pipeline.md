# HSB-Boden Lead-Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das HSB-Boden Website-Formular stellt echte Projektanfragen zu — über eine selbst-gehostete (kostenfreie) n8n-Community-Instanz, öffentlich erreichbar via Cloudflare Tunnel.

**Architecture:** Astro-Frontend (`LeadForm.tsx`) POSTet JSON an `PUBLIC_LEAD_ENDPOINT` → n8n-Webhook (`/webhook/hsb-boden-lead-intake`) → validieren → IF gültig → E-Mail an Betreiber + lokales Archiv → Response. Lokales n8n wird über Cloudflare Tunnel öffentlich gemacht; `WEBHOOK_URL` zeigt n8n die externe Adresse.

**Tech Stack:** n8n Community 2.8.4 (Node.js **20.x** Pflicht — 26 inkompatibel), Cloudflare Tunnel (`cloudflared`), Astro + Cloudflare Pages.

---

## Verifizierte Ausgangslage (2026-06-07)
- ✅ Repo `main` synchron mit origin, Gate grün (check 0/0/0 · test 8/8 · build ok).
- ✅ n8n nativ `/opt/homebrew/bin/n8n` v2.8.4. **Läuft nur mit node@20** (`/opt/homebrew/opt/node@20/bin`); System-node 26 wird abgelehnt.
- ✅ Workflow importiert (ID `IgpypQLWY2Xdi1li`), `active=1`, ABER **nicht published** → production-Webhook nicht registriert. Publish ist eine **UI-Aktion** (CLI `publish:workflow` schreibt keinen published-version-Eintrag — verifiziert in DB).
- ✅ `cloudflared` v2026.5.2 installiert.
- ⚠️ `emailSend`-Node: `credentials:{}`, `fromEmail`/`toEmail` = `*.invalid` Platzhalter → SMTP fehlt.
- ✅ Archiv-Node schreibt lokal nach `_AI_Memory/leads/hsb-boden/` (keine Credentials).

## Offene Entscheidungen / Risiken (vor Go-Live klären)
- **R1 — Dauerbetrieb:** Lokaler Mac + Tunnel ist NICHT 24/7-zuverlässig (Sleep, Neustart). Für echten Produktivbetrieb später VPS erwägen. Bis dahin: „staging/best-effort".
- **R2 — SMTP-Quelle:** Welcher Postausgang? (z. B. bestehendes Postfach `info@…` via SMTP, oder Transaktions-Provider). User liefert Zugangsdaten — NICHT erfinden.
- **R3 — Empfänger:** Echte Ziel-E-Mail für Leads (ersetzt `LEAD_RECIPIENT_EMAIL_TO_SET_IN_N8N@example.invalid`).
- **R4 — Spam/Abuse:** Öffentlicher Webhook ohne Auth. `PUBLIC_LEAD_ACCESS_KEY` ist KEIN echtes Secret (Browser-sichtbar). Honeypot/Rate-Limit als Folge-Task.

---

## Phase 1 — Lokal grün (Community n8n)

### Task 1: Node-Runtime für n8n fest verdrahten
**Files:**
- Create: `ops/n8n/run-n8n.sh`

- [ ] **Step 1: Wrapper-Skript schreiben** (pinnt node@20, deaktiviert Telemetrie)

```bash
#!/usr/bin/env bash
# n8n Community lokal starten — pinnt die kompatible Node-Version (20.x).
set -euo pipefail
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
export N8N_DIAGNOSTICS_ENABLED=false
export N8N_PERSONALIZATION_ENABLED=false
# WEBHOOK_URL wird in Phase 2 (Tunnel) gesetzt; lokal optional leer lassen.
exec n8n start
```

- [ ] **Step 2: Ausführbar machen + Node-Version verifizieren**

Run: `chmod +x ops/n8n/run-n8n.sh && /opt/homebrew/opt/node@20/bin/node -v`
Expected: `v20.20.2` (im Range `>=20.19 <=24.x`)

- [ ] **Step 3: Commit**

```bash
git add ops/n8n/run-n8n.sh
git commit -m "ops(n8n): node@20-gepinntes Start-Skript für Community-Instanz"
```

### Task 2: Workflow im UI publishen (production-Webhook registrieren)
**Files:** keine (UI-Aktion + Verifikation)

- [ ] **Step 1: n8n starten** (falls nicht laufend)

Run: `./ops/n8n/run-n8n.sh` (in eigenem Terminal lassen) — warten bis `Editor is now accessible via: http://localhost:5678`

- [ ] **Step 2: UI öffnen + ggf. Owner-Account anlegen**

Browser: `http://localhost:5678`. Beim Erststart fragt n8n 2.x einen lokalen Owner-Account ab (nur lokal, kein öffentliches Konto). Anlegen.

- [ ] **Step 3: Workflow publishen**

Workflow „hsb-boden-lead-intake" öffnen → Button **Publish** (oben rechts) klicken.

- [ ] **Step 4: Registrierung verifizieren**

Run: `grep -E "published workflows" /tmp/hsb-n8n.log` nach n8n-Neustart
Expected: `Processed 0 draft workflows, 1 published workflows` (NICHT mehr „0 published")

Alternativ DB-Check:
Run: `sqlite3 ~/.n8n/database.sqlite "SELECT count(*) FROM workflow_published_version;"`
Expected: `1`

### Task 3: Lokaler Webhook-Test (Fake-Daten, ohne SMTP)
**Files:** keine

- [ ] **Step 1: Invalider Payload → 400**

Run:
```bash
curl -s -X POST http://localhost:5678/webhook/hsb-boden-lead-intake \
  -H "Content-Type: application/json" -d '{"foo":"bar"}' -w "\n[%{http_code}]\n"
```
Expected: `[400]` mit `invalid_payload` (Webhook registriert + Validierung greift)

- [ ] **Step 2: Gültiger FAKE-Lead → erreicht emailSend**

Run:
```bash
curl -s -X POST http://localhost:5678/webhook/hsb-boden-lead-intake \
  -H "Content-Type: application/json" \
  -d '{"source":"website","legalBasis":"inquiry","firstName":"TEST","lastName":"FAKE","company":"Muster Industrie GmbH (TEST)","email":"test-fake@example.invalid","phone":"+49 000 0000000","industry":"Lebensmittel","projectType":"Neubau","areaSize":"500","liveOperation":"ja","loads":["chemisch"],"message":"AUTOMATISIERTER TEST – kein echter Lead","privacyConsent":true}' \
  -w "\n[%{http_code}]\n"
```
Expected: emailSend schlägt fehl (kein SMTP) → Execution mit Fehler am Mail-Node. **Das ist der erwartete Beweis**, dass Validierung + IF-true-Zweig laufen. Verifizieren in UI → Executions.

### Task 4: SMTP-Credential + echten Empfänger setzen (UI)
**Files:** keine (n8n-Credential, NICHT im Repo)

> ⚠️ BLOCKER R2+R3: Braucht echte SMTP-Daten + Ziel-E-Mail vom User. Keine Secrets ins Repo/Memory.

- [ ] **Step 1:** In n8n → Credentials → „SMTP" anlegen (Host, Port, User, Passwort vom User).
- [ ] **Step 2:** Node „Lead per E-Mail senden" → Credential zuweisen, `fromEmail` + `toEmail` auf echte Adressen setzen.
- [ ] **Step 3: Re-Publish** (Änderung ist neue Version → erneut Publish).
- [ ] **Step 4: Fake-Lead erneut senden** (Task 3 Step 2)
Expected: `[200]` `received` + E-Mail kommt an + Archiv-Datei unter `_AI_Memory/leads/hsb-boden/` erzeugt.

---

## Phase 2 — Öffentlich erreichbar (kostenfrei)

### Task 5: Cloudflare Tunnel auf localhost:5678
**Files:** keine (Tunnel-Config liegt in `~/.cloudflared`)

- [ ] **Step 1: Quick-Tunnel testen** (kostenfrei, ephemere URL)

Run: `cloudflared tunnel --url http://localhost:5678 --protocol http2`
Expected: Ausgabe einer öffentlichen `https://<random>.trycloudflare.com`-URL.
> ✅ Verifiziert 2026-06-07: `--protocol http2` ist nötig (QUIC/UDP instabil → HTTP 000; http2/TCP → HTTP 200). Editor + Webhook-Routing extern erreichbar bestätigt (Webhook gibt erwartungsgemäß 404 bis UI-Publish).

- [ ] **Step 2:** Öffentliche URL gegen Webhook testen

Run (URL aus Step 1 einsetzen):
```bash
curl -s -X POST https://<random>.trycloudflare.com/webhook/hsb-boden-lead-intake \
  -H "Content-Type: application/json" -d '{"foo":"bar"}' -w "\n[%{http_code}]\n"
```
Expected: `[400]` `invalid_payload` (extern erreichbar)

- [ ] **Step 3: `WEBHOOK_URL` setzen** im Wrapper (damit n8n korrekte externe URLs erzeugt)

In `ops/n8n/run-n8n.sh` vor `exec` ergänzen:
```bash
export WEBHOOK_URL="https://<stabile-tunnel-url>/"
```
> Hinweis: Quick-Tunnel-URLs wechseln bei Neustart. Für stabile URL: benannter Tunnel (`cloudflared tunnel create hsb-n8n`) + DNS-Route auf eine Subdomain (z. B. `n8n.cherinojoel.workers.dev`-Äquivalent / eigene Domain). Als Folge-Task, sobald Domain feststeht.

- [ ] **Step 4: Commit** (ohne echte URL falls geheim gehalten; sonst Subdomain)

```bash
git add ops/n8n/run-n8n.sh
git commit -m "ops(n8n): WEBHOOK_URL für Cloudflare-Tunnel-Erreichbarkeit"
```

### Task 6: Persistenz (best-effort Dauerbetrieb)
**Files:**
- Create: `ops/n8n/README-runbook.md`

- [ ] **Step 1: Runbook dokumentieren** (Start n8n + Tunnel, R1-Risiko Mac-Sleep)

Inhalt: Reihenfolge `run-n8n.sh` → `cloudflared tunnel`, wie URL prüfen, dass Mac nicht schlafen darf (`caffeinate -s`), Limitation für echten 24/7-Betrieb (VPS-Empfehlung).

- [ ] **Step 2: Commit**

```bash
git add ops/n8n/README-runbook.md
git commit -m "docs(n8n): Runbook für lokalen Betrieb + Tunnel"
```

---

## Phase 3 — Website anbinden

### Task 7: `PUBLIC_LEAD_ENDPOINT` setzen (lokaler Preview-Test)
**Files:**
- Create: `.env` (gitignored — NICHT committen)

- [ ] **Step 1: `.env` anlegen** mit Tunnel-URL (Wert aus Task 5)

```
PUBLIC_LEAD_ENDPOINT=https://<tunnel-url>/webhook/hsb-boden-lead-intake
PUBLIC_LEAD_ACCESS_KEY=
```

- [ ] **Step 2: Verifizieren, dass `.env` gitignored ist**

Run: `git check-ignore .env`
Expected: `.env` (ist ignoriert)

### Task 8: Build + lokale Preview
**Files:** keine

- [ ] **Step 1: Gate (ADR-003)**

Run: `npm run check && npm run test:run && npm run build`
Expected: check 0 errors · tests grün · build ok

- [ ] **Step 2: Wrangler-Preview starten**

Run: `npm run preview` (bzw. projektspezifischer Preview-Befehl) → lokale Prod-Build-URL

### Task 9: End-to-End über echte Website (Playwright, Fake-Lead)
**Files:** keine

- [ ] **Step 1:** Playwright → Preview-URL → `/kontakt`-Formular mit FAKE-Daten ausfüllen + absenden.
- [ ] **Step 2: Erfolg verifizieren**

Expected: Redirect auf `/danke-projektanfrage/`, 0 Console-Errors, in n8n → Executions erscheint die Anfrage, Archiv-Datei + (falls Task 4) E-Mail.

---

## Phase 4 — Production-Deploy (nur nach Freigabe)

### Task 10: Cloudflare Pages Env + Re-Deploy
**Files:** keine

> ⚠️ Kein Prod-Deploy ohne explizite User-Freigabe. Keine DNS-Änderung.

- [ ] **Step 1:** `PUBLIC_LEAD_ENDPOINT` in Cloudflare Pages (Projekt-Env, Production+Preview) setzen.
- [ ] **Step 2:** Preview-Deploy → E2E-Fake-Lead über die Preview-Domain.
- [ ] **Step 3:** Erst nach Grün + Freigabe: Production.

### Task 11: Gate + Memory/Handoff
- [ ] **Step 1:** ADR-003-Gate final grün dokumentieren (Zahlen notieren).
- [ ] **Step 2:** `CANONICAL_STATE.md` + `working_set.json` aktualisieren: Lead-Pipeline-Status, Tunnel-URL-Strategie, offene R1/R4.
- [ ] **Step 3:** `ai-state checkpoint --status completed` sobald E2E grün.

---

## Self-Review
- **Spec-Coverage:** n8n-Quelle (Phase 1), Betriebsart kostenfrei (Phase 1+2), lokaler Test (Task 3), Public-Webhook (Task 5), `PUBLIC_LEAD_ENDPOINT` (Task 7/10), Re-Deploy (Task 8/10), E2E (Task 9) — abgedeckt.
- **Blocker explizit:** R2 (SMTP) + R3 (Empfänger) in Task 4; R1 (Dauerbetrieb) + R4 (Abuse) als Risiken markiert.
- **Keine erfundenen Werte:** alle Secrets/URLs als Platzhalter, vom User zu liefern.
