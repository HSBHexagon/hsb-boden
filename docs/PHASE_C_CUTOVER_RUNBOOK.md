# Phase C — Production-Cutover Runbook (HSB / HEXAFLOOR)

> ## ⚠️ STALE — 2026-07-12: Deploy-Architektur hat sich geändert
> Dieses Runbook stammt aus der **Cloudflare-Workers-SSR-Ära** (Juni 2026). Seitdem wurde
> die Site auf **statisches Astro + Cloudflare Pages** migriert (Projekt `hsb-boden`,
> `www.hsb-boden.de` läuft bereits live über Pages). Die `wrangler deploy`-Befehle unten
> deployen einen **Worker** und sind nicht mehr der Production-Weg; der Worker
> `hsb-boden` unter `cherinojoel.workers.dev` ist ein verwaistes Artefakt im alten Account.
> Aktueller Production-Deploy-Weg: `.github/workflows/deploy-production.yml`
> (`workflow_dispatch`-only, `wrangler pages deploy dist --project-name hsb-boden --branch=main`).
> Offen bleibt ausschließlich der freigabepflichtige **Apex-/NS-Cutover bei All-Inkl**.
> Die Schritte unten nur noch als historische Referenz lesen, nicht ausführen.

> Erstellt 2026-06-24 (Claude Code, Opus 4.8). Alle Befehle/Pfade sind **empirisch per Dry-Run + Quellcode-Lesen verifiziert**, nicht nur aus dem Handoff übernommen.
> **Cutover bleibt freigabepflichtig.** Dieses Dokument macht den Vorgang mechanisch — es ersetzt keine Freigabe.

> ## STATUS 2026-06-24 ~03:00 CEST — Schritte 1–4 ERLEDIGT + VERIFIZIERT
> Mit Nutzer-Freigabe wurde der Production-Worker bereits **route-los vorab deployed + end-to-end verifiziert**:
> - **Worker `hsb-boden`** live (route-los): `https://hsb-boden.cherinojoel.workers.dev`, Version `27f7a6a0-4460-44c5-aff4-3cec86a8ee4b`, `ENVIRONMENT=production`, SESSION-KV auto-provisioniert (`hsb-boden-session`), ASSETS gebunden.
> - **Secret `LEAD_WEBHOOK_URL`** auf `hsb-boden` gesetzt (= live Apps-Script-URL).
> - **End-to-End verifiziert:** server-seitiger POST → `{"ok":true}` → echte Zeile im Sheet „HSB CRM Light" (Lead-ID `WEB-20260624-023525`, 27-Spalten-Mapping korrekt, Telefon als Text mit führender Null, Status `neu`), Testzeile danach geleert.
> - **KEINE Routes, KEIN DNS** → Seite ist NICHT live (Traffic läuft weiter zum alten WordPress, da NS-Switch noch aussteht).
>
> **MORGEN verbleibt nur:** NS-/DNS-Switch (Domain-Admin) → dann **Schritt 5 (Routes)** + **Schritt 6 (Live-Verify auf hsb-boden.de)**. Schritte 1–3 nur noch idempotent re-prüfen. Das ist der „DNS als Finale"-Stand.

## Zweck

Den fertigen Astro-/Cloudflare-Worker als **Production-Worker `hsb-boden`** live auf `hsb-boden.de` schalten, sobald der **NS-/DNS-Switch** durch den Domain-Admin erfolgt ist. Bis dahin bleibt die Domain auf dem alten Live-Pfad; der route-lose Production-Worker ist bereits separat vorbereitet und verifiziert.

## Fakten (verifiziert)

| Sache | Wert | Quelle |
|---|---|---|
| Cloudflare-Account | `cherinojoel@gmail.com` → `043ec899a435f150995d89f402ed7b12` | Zone-API 2026-06-23 |
| Zone `hsb-boden.de` | `2aefa04f69a2339b2f9f3f2876d7e35c`, Status `pending` (→ `active` nach NS-Switch) | Zone-API |
| Preview-Worker | `hsb-boden-preview` (existiert, Lead-Pipeline live) | wrangler |
| Production-Worker | `hsb-boden` — **deployed route-los 2026-06-24**, Version `27f7a6a0…`, URL `https://hsb-boden.cherinojoel.workers.dev` (noch ohne Routes) | wrangler deploy 2026-06-24 |
| SESSION-KV (Prod) | `hsb-boden-session` (`dc91654846b546e39c273d85f559a5a2`), auto-provisioniert beim Deploy | wrangler |
| Lead-Webhook (Apps Script) | `https://script.google.com/macros/s/AKfycbyVR_Mib5YEI4qZ1MUhUKKZWGJl6VDVmTIC_h_fiFt8INII5_epMUcjh5LhqqdH3lUv/exec` | Handoff 2026-06-22, GET = `{"ok":true,"service":"hsb-lead-intake"}` |
| CRM-Sheet | „HSB CRM Light" (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`), Account cherinojoel@gmail.com | Handoff |
| Secret-Name | `LEAD_WEBHOOK_URL` (Endpoint liest `env.LEAD_WEBHOOK_URL`, `src/pages/api/lead.ts:136`) | Quellcode |
| Origin-Allowlist | hart kodiert `https://hsb-boden.de`, `https://www.hsb-boden.de` (`src/pages/api/lead.ts:7-9`) | Quellcode |

## ⚠️ Kritischer Bug — `--env production` ist KAPUTT

`npm run deploy:production` (= `wrangler deploy --env production`) **deployt still auf `hsb-boden-preview`**, NICHT auf Production.

**Ursache (verifiziert):** Der Astro-6-Cloudflare-Adapter legt beim Build `.wrangler/deploy/config.json` als Redirect auf `dist/server/wrangler.json` an. Diese generierte Datei ist aus dem **Top-Level (= preview)** der `wrangler.toml` geflattet (`name: hsb-boden-preview`, `vars: {ENVIRONMENT: preview}`, `env: {}`). `--env production` findet dort keine `production`-Sektion und wird **stumm ignoriert**.

**Beleg (Dry-Run 2026-06-24):**
- `wrangler deploy --env production --dry-run` → `env.ENVIRONMENT ("preview")` ❌
- `wrangler deploy --name hsb-boden --var ENVIRONMENT:production --dry-run` → `env.ENVIRONMENT ("(hidden)")` ✅ (CLI-Override greift)

→ **NIEMALS `npm run deploy:production` für den Cutover verwenden.** Stattdessen den `--name`-Workaround unten.

## Cutover-Schritte (morgen, nach NS-Switch + Freigabe)

### 0. Vorbedingungen prüfen
```bash
cd "$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)"
~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden
git status --short            # sauber
git log --oneline -1          # auf main, Stand bekannt
```
- DNS/NS-Switch bestätigt? Zone `hsb-boden.de` Status = `active`?
- Apps-Script-Webhook lebt? `curl -s "<LEAD_WEBHOOK_URL>"` → `{"ok":true,"service":"hsb-lead-intake"}`

### 1. Build
```bash
npm run build
```

### 2. Production-Worker deployen (Workaround, NICHT --env production)
```bash
wrangler deploy --name hsb-boden --var ENVIRONMENT:production
```
- Erzeugt/aktualisiert Worker `hsb-boden`. Bindings (ASSETS, SESSION-KV) werden vom Top-Level geerbt; `ENVIRONMENT=production` per CLI-Override; **keine Routes** (kommen in Schritt 4).

### 3. Production-Secret setzen
```bash
printf '%s' 'https://script.google.com/macros/s/AKfycbyVR_Mib5YEI4qZ1MUhUKKZWGJl6VDVmTIC_h_fiFt8INII5_epMUcjh5LhqqdH3lUv/exec' \
  | wrangler secret put LEAD_WEBHOOK_URL --name hsb-boden
```
- `printf '%s'` (kein `echo`) → kein Trailing-Newline in der URL.

### 4. Worker VOR Live-Schaltung verifizieren (noch ohne Routes!)
```bash
# Server-seitiger POST (kein Origin-Header → passiert Origin-Check) gegen die workers.dev-URL des neuen Workers:
curl -s "https://hsb-boden.<subdomain>.workers.dev/api/lead" \
  -H "Content-Type: application/json" \
  --data '{"name":"HSB-TEST-PROD","email":"test@example.com","phone":"0170000000","message":"cutover-test","privacy":true}'
# Erwartung: {"ok":true}
```
- **WICHTIG:** kein `-X POST` verwenden — zwingt curl, dem Apps-Script-302 mit POST zu folgen → 405. Ohne `-X POST` downgradet curl den Redirect korrekt auf GET.
- Danach im Sheet „HSB CRM Light" prüfen: neue Zeile, 27-Spalten-Mapping korrekt, Telefon als Text (führende Null erhalten), Status `neu`. **Testzeile danach leeren.**
- Der Worker inspiziert die Apps-Script-Antwort nicht → Sheet direkt prüfen, nicht nur auf `ok:true` verlassen.

### 5. Routes setzen (= GO-LIVE; macht die Seite live)
Der `--name`-Workaround umgeht die `[env.production]`-Routes in `wrangler.toml`. Routes daher **separat** setzen, z.B. via API:
```bash
# Pattern 1
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/2aefa04f69a2339b2f9f3f2876d7e35c/workers/routes" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  --data '{"pattern":"hsb-boden.de/*","script":"hsb-boden"}'
# Pattern 2
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/2aefa04f69a2339b2f9f3f2876d7e35c/workers/routes" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  --data '{"pattern":"www.hsb-boden.de/*","script":"hsb-boden"}'
```
(Alternativ im Dashboard: Worker `hsb-boden` → Settings → Domains & Routes → Route hinzufügen.)
- **Achtung Reihenfolge:** Die Zone hat `A @/www/* → 85.13.130.17` **proxied** vorkonfiguriert. Ohne Worker-Route ginge der Traffic nach NS-Switch weiter zum **alten WordPress**. Erst Route = neue Seite live. Ein kaputter Worker + aktive Route = Seite down (kein Fallback) → deshalb Schritt 4 zwingend vor Schritt 5.

### 6. Live-Verifikation auf der echten Domain
```bash
curl -sI "https://hsb-boden.de/"                 # 200, vom Worker (nicht WordPress)
curl -sI "https://www.hsb-boden.de/"             # 200
```
- Im Browser auf `https://hsb-boden.de/kontakt/` das **echte Formular** absenden (Origin = hsb-boden.de → passt Origin-Allowlist) → neue Zeile im Sheet. Damit ist die Pipeline erstmals **mit echtem Browser-Origin** bewiesen (bisher nur server-/no-origin-seitig auf Preview).
- Mail (Outlook MX/SPF/DMARC/autodiscover) **nicht anfassen**.

## Rollback
- Routes wieder entfernen (`DELETE .../workers/routes/{id}`) → Traffic fällt auf die vorkonfigurierte A-Record-Route (altes WordPress) zurück.
- Worker `hsb-boden` kann gelöscht werden (`wrangler delete --name hsb-boden`), falls nötig.

## Offene Punkte (nicht Teil des Cutovers)
- Saubere Lösung statt `--name`-Workaround: Env-Handling des Adapters reparieren oder dedizierte Production-wrangler-Config — eigener Task nach Go-Live.
- `package.json` `deploy:production`-Script auf den funktionierenden Pfad umstellen (aktuell irreführend, deployt auf preview).
- Manuelle Sheet-UI (Dropdowns/Filter/Header-Fixierung), 3 leere Rest-Apps-Script-Projekte aufräumbar.
