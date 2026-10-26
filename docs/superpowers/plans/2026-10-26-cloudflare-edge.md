# Cloudflare-Edge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Cloudflare-Kette (Pages, Functions, Header, WAF, Turnstile) ist dokumentiert wie sie ist, schützt das Lead-Formular doppelt und kommt ohne `unsafe-inline` aus, soweit der Build das erlaubt.

**Architecture:** Erst die Dokumentation an die Wirklichkeit angleichen (Pages + Functions), dann Bot-Schutz serverseitig (Turnstile, `functions/api/lead.ts`), dann Edge-Regeln im Dashboard (Owner), dann CSP-Härtung über Astro, zuletzt eine Entscheidung zu Pages vs. Workers ohne Migration.

**Tech Stack:** Cloudflare Pages + Pages Functions, Wrangler 4, Turnstile, WAF Rate Limiting, Astro `security.csp`, Vitest.

**Spec:** Keine Spezifikation vorhanden. Grundlage ist der Abschnitt „Ist-Zustand“ (Stand 2026-10-26).

## Global Constraints

- Keine Website-Code-Änderung ohne Freigabe: `src/`, `public/`, `components/`, `layouts/`, `styles/`, `astro.config.*`, `wrangler.toml`, `package.json`, Lockfiles. Zusätzlich gelten `functions/` und `public/_headers` als Website-Code. Jeder Task, der sie ändert, beginnt mit dem Schritt „Freigabe einholen“.
- Kein Production-Deploy, keine Dashboard-Änderung aus dieser Session; `PROJECT_TRUTH.md`: „Keine produktive Website-Veröffentlichung durch diesen Auftrag.“ Live-WordPress bleibt unberührt.
- Keine Secrets in Repo, Chat oder Doku; `TURNSTILE_SECRET` nur im Pages-Projekt.
- Kein `git add .`; kein Push ohne Freigabe; vor Commit `python3 scripts/verify_ssot.py` mit Exit 0; vor Abschluss `npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run` in `apps/website`.
- `wrangler.toml` bleibt ohne `pages_build_output_dir` (Begründung im Kopfkommentar der Datei).
- Dashboard-Aktionen (Turnstile-Widget, WAF-Regeln, Secrets) führt der Konto-Inhaber aus. Der Plan nennt sie **Owner-Aktion**.

## Ist-Zustand (Belege)

| Befund | Beleg |
|---|---|
| Die Seite ist ein statischer Astro-Build auf **Cloudflare Pages** (Projekt `hsb-boden`), API als Pages Functions; Workers sind laut Checkpoint seit 2026-07-12 gelöscht. | `apps/website/wrangler.toml:1-30`, `CHECKPOINT_STATE.json` |
| Die kanonische Doku beschreibt noch Workers, Account `043ec899…`, Zone „pending“ und `src/pages/api/lead.ts`. Der aktuelle Account laut Checkpoint ist `01dc3780…`; der Endpunkt liegt in `functions/api/lead.ts`, `src/pages/api` existiert nicht. | `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md:20,44,63,77`; `TURNSTILE_FORM_PROTECTION_READINESS.md:17,60` |
| Turnstile ist nicht aktiv; `lead.ts` hat kein `siteverify`. Rate-Limit über KV `RATE_LIMIT_KV` per Lesen-dann-Schreiben (nicht atomar), je IP und je E-Mail. | `apps/website/functions/api/lead.ts:10,31-44,268-277` |
| `_headers`: 8 Regelblöcke, längste Zeile 953 Zeichen (Grenzen: 100 Regeln, 2.000 Zeichen je Zeile [C4]). CSP enthält `script-src 'unsafe-inline'`, kein `frame-src`, und Google-Ads-Domains, obwohl „Marketing“ laut `consent.ts` deaktiviert ist. | `apps/website/public/_headers:1-10`, `src/data/consent.ts` |
| Inline-Skripte: `SEOHead.astro:55` (`is:inline`), `abmelden/index.astro:34`, JSON-LD (`SEOHead.astro:69`); Astro-gebündelte Skripte in `BaseLayout.astro`. | `rg "is:inline" apps/website/src` |
| `tests/headers-security-perf.test.ts` prüft weder `unsafe-inline` noch Zeilenlänge. | `grep` im Test |

## Quellen (abgerufen 2026-10-26)

- [C1] Workers Best Practices: https://developers.cloudflare.com/workers/best-practices/workers-best-practices/. Für neue statische Projekte wird Workers Static Assets empfohlen; Pages „continues to work“, neue Funktionen gehen an Workers.
- [C2] Migrate from Pages (aktualisiert 2026-10-12): https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/. Workers unterstützt keine Domain, deren Nameserver nicht bei Cloudflare liegen; Preview-URLs funktionieren anders.
- [C3] Early Hints (Pages): https://developers.cloudflare.com/pages/configuration/early-hints/. Auf Pages immer aktiv und nicht abschaltbar; Workers folgt der Zonen-Einstellung.
- [C4] Headers (Pages): https://developers.cloudflare.com/pages/configuration/headers/. 100 Regeln, 2.000 Zeichen je Zeile.
- [C5] Turnstile validieren (aktualisiert 2026-10-22): https://developers.cloudflare.com/turnstile/get-started/server-side-validation/. Siteverify ist Pflicht, Token 300 s gültig und einmalig (`timeout-or-duplicate`), Parameter `secret`, `response`, optional `remoteip`, `idempotency_key`; Antwort enthält `hostname` und `action`.
- [C6] Formulare schützen: https://developers.cloudflare.com/use-cases/solutions/protect-sensitive-forms-fraud-abuse/. Rate-Limit-Regel für Formular-Endpunkte; Free-Plan: Zähler nach IP, Periode 10 s, Aktion Block 10 s.
- [C7] Turnstile Client-Rendering: https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/. `api.js` nur von der genannten URL laden, nicht proxien oder cachen; Fehlercode 200500 beschreibt einen blockierten Iframe von `challenges.cloudflare.com`. Eine eigene CSP-Seite lieferte die Suche nicht; die nötigen CSP-Einträge (`script-src`, `frame-src`) sind daher abgeleitet und im Test zu bestätigen.
- [A1] Astro `security.csp` (Docs über Context7, `/withastro/docs`, Konfigurationsreferenz): `scriptDirective.hashes`, `styleDirective.hashes`, erzeugt Hashes automatisch. Ob die installierte Version (`astro ^7.3.2`) die Option kennt, ist in Task 4 zu belegen.

## Review Focus

- Siteverify nicht erreichbar oder Timeout: entscheidet über Lead-Verlust vs. Spam (Entscheidung D1 in Task 2).
- Wiederverwendetes Token (Doppelklick, Browser-Zurück): muss als `turnstile_invalid` ohne Absturz enden und im Formular ein neues Token anfordern.
- Vorschau-Hostnamen (`*.pages.dev`): Widget-Hostnamenliste und `hostname`-Prüfung dürfen Previews nicht dauerhaft aussperren.
- CSP-Umstellung bricht still Inline-Skripte (Cookie-Banner, Analytics-Loader): Prüfung im Browser auf CSP-Verstöße gehört zum Abnahmetest.
- WAF-Regel greift auf Free nach IP: Büro-/Mobilfunk-NAT kann legitime Anfragenden sperren; Schwelle und Dauer konservativ wählen.

---

### Task 1: Cloudflare-Doku an die Wirklichkeit angleichen

**Files:**
- Modify: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
- Modify: `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`, `TURNSTILE_FORM_PROTECTION_READINESS.md`, `GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`

**Interfaces:**
- Produces: eine kanonische Doku („Verified State“ mit Datum und Quelle je Zeile); die drei übrigen verweisen darauf.

- [ ] **Step 1: Rot beweisen.** Run: `grep -rn "src/pages/api/lead.ts\|043ec899a435f150995d89f402ed7b12\|wrangler deploy --name" docs/cloudflare`. Expected vorher: mindestens sieben Treffer.
- [ ] **Step 2: Owner-Aktion, Belege liefern.** Ausgabe von `wrangler whoami`, Projekt-/Domain-Status aus dem Pages-Dashboard und Zonenstatus (aktiv oder „pending“). Ohne diese Belege bleibt jede Zeile als „unbelegt“ markiert; nichts wird aus dem Gedächtnis ergänzt.
- [ ] **Step 3: Doku neu schreiben:** Pages statt Workers, Endpunktpfade `functions/api/{lead,collect}.ts`, aktueller Account laut Beleg, Deploy-Wege aus `wrangler.toml`. Veraltetes Material in einen Abschnitt „Historisch“ verschieben statt löschen.
- [ ] **Step 4: Grün beweisen.** Derselbe `grep` aus Step 1. Expected: nur noch Treffer unterhalb der Überschrift „Historisch“.
- [ ] **Step 5: Commit.** `git add docs/cloudflare/`, Nachricht `docs(cloudflare): Readiness an Pages-Ist-Zustand angleichen`.

### Task 2: Turnstile-Validierung für `/api/lead`

**Files:**
- Modify: `apps/website/functions/api/lead.ts`
- Modify: `apps/website/src/components/forms/LeadForm.astro`
- Modify: `apps/website/public/_headers` (nur `https://challenges.cloudflare.com` in `script-src` und `frame-src`)
- Test: `apps/website/tests/lead-endpoint.test.ts`, `apps/website/tests/headers-security-perf.test.ts`

**Interfaces:**
- Produces in `lead.ts`: `Env.TURNSTILE_SECRET?: string`; `verifyTurnstile(token: string | undefined, ip: string, env: Env, fetchImpl?: typeof fetch): Promise<"ok" | "missing" | "invalid" | "unavailable">`. Fehlt `TURNSTILE_SECRET`, liefert die Funktion `"unavailable"` (nicht `"invalid"`) und loggt es. Fehlercodes der Antwort: `turnstile_missing` (400), `turnstile_invalid` (400), bei D1 = fail-closed `turnstile_unavailable` (503).
- Consumes: Siteverify-Antwortfelder `success`, `hostname`, `error-codes` [C5].
- Produces für Task 4: CSP enthält `https://challenges.cloudflare.com` in `script-src` und `frame-src`.

- [ ] **Step 1: Freigabe einholen** für Änderungen in `functions/` und `src/components/forms/` (siehe Global Constraints).
- [ ] **Step 2: Entscheidung D1 vom Owner:** Verhalten bei Siteverify-Ausfall. Empfehlung: nur bei Timeout/5xx fail-open (Lead geht mit dem KV-Limit durch, Ereignis wird geloggt), bei `success: false` immer ablehnen. Begründung: Ein verlorener B2B-Lead kostet mehr als ein seltener Spam-Durchlass; die KV-Limits bleiben aktiv.
- [ ] **Step 3: Failing Tests schreiben** in `lead-endpoint.test.ts` mit gestubbtem `fetch`: `rejects POST without cf-turnstile-response with 400 turnstile_missing`; `rejects when siteverify answers success=false with error-code timeout-or-duplicate (400 turnstile_invalid)`; `rejects when siteverify hostname is not www.hsb-boden.de`; `siteverify timeout follows decision D1`; `valid token reaches the existing lead pipeline unchanged`; `missing TURNSTILE_SECRET is reported as unavailable, not invalid`. In `headers-security-perf.test.ts`: `CSP allows https://challenges.cloudflare.com in script-src and frame-src`.
- [ ] **Step 4: Run.** `cd apps/website && npx vitest run tests/lead-endpoint.test.ts tests/headers-security-perf.test.ts`. Expected: die neuen Tests FAIL, bestehende PASS.
- [ ] **Step 5: `verifyTurnstile` implementieren** (POST an `https://challenges.cloudflare.com/turnstile/v0/siteverify`, `remoteip` aus `CF-Connecting-IP`, Timeout per `AbortController`, Hostname-Prüfung gegen die erlaubten Origins aus `lead.ts`) und vor dem Rate-Limit-Block in den Handler einhängen. Formular: `cf-turnstile`-Container und Skript von der exakten URL laden [C7]; bei serverseitiger Ablehnung ein neues Token anfordern.
Zusätzlich die beiden CSP-Einträge in `_headers` ergänzen; sonst blockiert die bestehende CSP (`default-src 'self'`, kein `frame-src`) das Widget und jeder Lead scheitert.
- [ ] **Step 6: Owner-Aktion, vor dem Merge:** Widget im Dashboard anlegen (Hostnamen `www.hsb-boden.de` plus Preview-Host), Secret `TURNSTILE_SECRET` im Pages-Projekt für Preview und Production setzen. Wert nie in Chat oder Repo. Reihenfolge ist Pflicht: Secret und Widget zuerst, dann Merge. Ohne Secret gilt die D1-Regel für `"unavailable"`: Bei der empfohlenen Variante (fail-open) läuft das Formular mit den KV-Limits weiter und der Fehler steht im Log; bei fail-closed wären ohne Secret alle Leads gesperrt, deshalb ist die Reihenfolge verbindlich.
- [ ] **Step 7: Run.** `npx vitest run tests/lead-endpoint.test.ts tests/headers-security-perf.test.ts && npm run check`. Expected: alle PASS, 0 Fehler. Danach Preview-Test mit den Testschlüsseln aus der Cloudflare-Testseite (nicht in dieser Session).
- [ ] **Step 8: Datenschutz abgleichen.** `src/pages/datenschutz/index.astro` nennt Cloudflare nur als Hosting; Turnstile als Formularschutz ergänzen ist eine inhaltliche Entscheidung des Owners (keine Rechtsberatung durch diesen Plan).
- [ ] **Step 9: Commit.** `git add apps/website/functions/api/lead.ts apps/website/src/components/forms/LeadForm.astro apps/website/public/_headers apps/website/tests/lead-endpoint.test.ts apps/website/tests/headers-security-perf.test.ts`, Nachricht `feat(api): Turnstile-Validierung für Leads`.

### Task 3: WAF-Rate-Limit als zweite Schicht (Owner-Aktion)

**Files:**
- Modify: `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`

**Interfaces:**
- Produces: Regelvorgabe mit Ausdruck `http.request.uri.path eq "/api/lead" and http.request.method eq "POST"`, Zähler IP, Free-Plan-Werte laut [C6].

- [ ] **Step 1: Regelvorgabe in die Doku schreiben,** inklusive Schwelle (konservativ, z. B. 5 Anfragen je 10 s laut Beispiel in [C6]) und der Warnung zu NAT (siehe Review Focus).
- [ ] **Step 2: Owner-Aktion:** Regel im Dashboard unter Security → Security rules anlegen; Zone muss „active“ sein (Task 1, Step 2).
- [ ] **Step 3: Prüfen ohne Produktionsverkehr zu erzeugen:** Wirkung nur im Dashboard unter Security Events ablesen; keine Test-POSTs gegen Production aus dieser Session.
- [ ] **Step 4: Commit.** `git add docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`, Nachricht `docs(cloudflare): WAF-Rate-Limit für /api/lead`.

### Task 4: CSP ohne `unsafe-inline` (Spike, danach Umsetzung)

**Files:**
- Modify: `apps/website/astro.config.mjs`, `apps/website/public/_headers`
- Test: `apps/website/tests/headers-security-perf.test.ts`
- Read: Google-Ursprünge aus `2026-10-26-google-messung-seo.md`, Task 2

**Interfaces:**
- Consumes: Liste der tatsächlich benötigten Google-Origins (Google-Plan, Task 2) und die Turnstile-Einträge aus Task 2 (müssen in der gekürzten CSP erhalten bleiben).
- Produces: CSP ohne `'unsafe-inline'` in `script-src`, falls [A1] in der installierten Astro-Version existiert; `_headers` bleibt unter 100 Regeln und 2.000 Zeichen je Zeile.

- [ ] **Step 1: Freigabe einholen** für `astro.config.mjs` und `_headers`.
- [ ] **Step 2: Spike auf einem Wegwerf-Branch.** Prüfen, ob `security.csp` in der installierten Astro-Version akzeptiert wird: `cd apps/website && npm run build` mit der Option. Expected: Build grün und `<meta http-equiv="content-security-policy">` in `dist/index.html`. Wenn die Option fehlt: Task abbrechen, Ergebnis dokumentieren, Alternative (Hashes manuell in `_headers`) nur mit Owner-Freigabe.
- [ ] **Step 3: Failing Tests** in `headers-security-perf.test.ts`: `script-src has no unsafe-inline`; `every _headers line is at most 2000 characters`; `_headers has at most 100 rules`; `CSP allows https://challenges.cloudflare.com in script-src and frame-src`.
- [ ] **Step 4: Run.** `npx vitest run tests/headers-security-perf.test.ts`. Expected: die neuen Tests FAIL.
- [ ] **Step 5: CSP umstellen** (Hashes über Astro, `frame-src` ergänzen). **Google-Origins werden nur gekürzt, wenn `docs/analytics/GOOGLE_ORIGINS_EVIDENCE_2026-10.md` einen Produktions-HAR für die Szenarien „mit Einwilligung“ und „nach Widerruf“ ausweist.** Fehlt er oder ist die Liste als „unvollständig“ markiert, bleiben alle Google-Origins unverändert; ein lokaler Lauf zeigt keine Google-Hosts (GA4 lädt nur auf der Produktionsdomain) und darf nie als Bedarfsliste dienen, sonst bricht GA4 in Produktion. Hinweis: Eine Meta-CSP und die Header-CSP gelten beide, die strengere gewinnt je Direktive; die Quelle der Wahrheit festlegen und die andere entfernen.
- [ ] **Step 6: Run.** `npm run test:run && npm run check && npm run build`. Expected: alle grün. Danach im Browser (Preview, nicht Production) Konsole auf CSP-Verstöße prüfen: Expected: keine.
- [ ] **Step 7: Commit.** `git add apps/website/astro.config.mjs apps/website/public/_headers apps/website/tests/headers-security-perf.test.ts`, Nachricht `feat(security): CSP ohne unsafe-inline`.

### Task 5: Entscheidungsvorlage Pages vs. Workers Static Assets

**Files:**
- Create: `docs/cloudflare/PAGES_TO_WORKERS_DECISION_2026-10-26.md`

**Interfaces:**
- Produces: Entscheidungsvorlage mit Empfehlung; **keine** Migration, keine Änderung an `wrangler.toml`.

- [ ] **Step 1: Fakten eintragen:** [C1] (Workers empfohlen, Pages läuft weiter), [C2] (Domain braucht Cloudflare-Nameserver; Preview-URLs anders), [C3] (Early Hints auf Pages nicht abschaltbar). Pro/Contra auf die Projektlage beziehen: Pages Functions in `functions/`, KV-Binding im Dashboard, Deploy über `deploy-production.yml`.
- [ ] **Step 2: Offene Belegfrage an den Owner:** Liegen die Nameserver von `hsb-boden.de` bei Cloudflare? Die Doku vom 2026-06-26 sagt „pending“, der Checkpoint ist neuer, aber nicht eindeutig. Ohne Antwort ist ein Wechsel ausgeschlossen [C2].
- [ ] **Step 3: Empfehlung formulieren:** Pages beibehalten, bis (a) die Nameserver-Frage geklärt ist und (b) ein Bedarf entsteht, den nur Workers deckt (Cron, Durable Objects, Observability). Dann Probelauf als separater Worker mit `noindex` und eigenem Namen.
- [ ] **Step 4: Commit.** `git add docs/cloudflare/PAGES_TO_WORKERS_DECISION_2026-10-26.md`, Nachricht `docs(cloudflare): Entscheidungsvorlage Pages vs Workers`.
