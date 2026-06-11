# HSB-Boden — Go-Live Masterplan (Dach-Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development oder superpowers:executing-plans. Steps nutzen Checkbox-Syntax (`- [ ]`).
> **Dach-Plan** über alle Arbeitsstränge. Der Lead-Pipeline-Detailplan ist NICHT hier dupliziert (DRY): siehe `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`.

**Goal:** hsb-boden produktiv schalten als organische B2B-Lead-Engine für Industrieböden — ohne Ranking-Verlust bei der WordPress→Cloudflare-Migration und mit funktionierender Lead-Zustellung.

**Architecture:** Astro 5 (SSG/SSR) auf Cloudflare Workers. Frontend-Formular → n8n-Webhook (self-hosted Community + Cloudflare Tunnel) → E-Mail/Archiv. SEO über statische Seiten + JSON-LD + 301-Redirect-Map. DNS-Cutover von WordPress als letzter Schritt.

**Tech Stack:** Astro, React, TypeScript, Tailwind, Cloudflare Workers/Wrangler, n8n 2.8.4 (node@20), cloudflared.

---

## 🚦 ARBEITSZUSTAND 2026-06-10 (verbindliche Entscheidung)

**Die Website bleibt vorerst auf der Preview-/Entwurfsumgebung** (`https://hsb-boden-preview.cherinojoel.workers.dev/`). hsb-boden.de wird NICHT übernommen, bis alle Voraussetzungen erfüllt und freigegeben sind.

- **PR #2 (Cloudflare-Bot: Worker-Name `hsb-boden-preview` → `hsb-boden`) wird NICHT gemerged.** Begründung: Die Umbenennung ist der erste Schritt der Produktionsübernahme und damit verfrüht. Der PR bleibt offen als Marker für den späteren Go-Live-Schritt (Phase 5).
- **Absolute Sperren bis zur Freigabe:** kein Produktions-Deploy, kein Domain-Switch, keine DNS-Änderung, keine Wrangler-Namensänderung Richtung Produktion.
- **Go-Live-Voraussetzungen (alle offen, blockieren Phase 5):** GA4-ID · SMTP/Formularversand · n8n-Follow-up · juristische Prüfung der Rechtsseiten · finale Sichtprüfung/Freigabe durch den Inhaber.
- **Abgleich mit dem operativen HEXAFLOOR-Abarbeitungsplan:** siehe `docs/superpowers/plans/2026-06-10-hexafloor-abgleich.md` (Akquise-System: Flyer, CRM-Light, n8n-Workflows, Compliance-SOP — größtenteils außerhalb dieses Repos, dort mit Repo-Status abgeglichen).

**Seit 2026-06-07 zusätzlich erledigt (PR #1 + PR #3, beide gemerged):**
- [x] Phase 2 komplett: `public/_redirects` mit 301-Map WordPress→Astro (12 Einträge), gegen Preview verifiziert
- [x] Phase 3.1: Service-JSON-LD auf Leistungsseiten (TDD, Tests grün)
- [x] Phase 3.2: seo-content-reviewer-Durchlauf; unbelegte Superlative + interne Disclaimer-Tonalität entfernt
- [x] Design-/Content-Perfektionierung der Preview (Playwright Desktop 1440 + Mobile 390): Umlaute, Halbgeviertstriche, fehlende Branchen-Optionen im Leadformular, keine Self-Link-CTAs im PageHero, Wissensartikel-Fließtext repariert, Referenz-Disclaimer-Ton korrigiert
- [x] Südzucker als einzige namentlich freigegebene Referenz; alle übrigen anonymisiert (`approvalStatus`-Feld in `src/data/references.ts`) — entspricht P0 „Referenzen freigeben/anonymisieren" aus dem HEXAFLOOR-Plan

---

## ✅ BEREITS ERREICHT (verifiziert 2026-06-07)

- [x] Astro/Cloudflare-Stack steht; vollständige Seitenstruktur (index, leistungen, branchen, wissen, referenzen, kontakt, impressum, datenschutz, karriere, sitemap, robots, danke)
- [x] Design-Qualitätssprung + A11y/WCAG-Kontrast-Fixes + Favicon/Console-Fix
- [x] Lighthouse: Desktop 100/100/100/100, Mobile 99/100/100/100 (gegen Prod-Build)
- [x] Gate grün: `check` 0/0/0 · `test:run` 8/8 · `build` ok
- [x] **Code committet + nach `origin/main` gepusht** (15 Commits, `main` synchron) — die Website IST versioniert & remote gesichert
- [x] Südzucker-Trust-Blocker gelöst (real + freigegeben)
- [x] Secrets rotiert (User 2026-06-06)
- [x] JSON-LD-Basis: Organization, LocalBusiness, FAQPage, BreadcrumbList
- [x] Lead-Pipeline-Code: `leadEndpoint` env-basiert, Formular degradiert sauber
- [x] n8n-Workflow vorhanden + lokal importiert/aktiv; node@20-Inkompatibilität gelöst
- [x] Cloudflare-Tunnel-Erreichbarkeit verifiziert (`--protocol http2`)
- [x] Entscheidungs-Report + Lead-Pipeline-Detailplan + Runbook geschrieben

## ⬜ NOCH ZU TUN (priorisiert nach Zielwirkung)

Reihenfolge bewusst gewählt: **(1) sichern → (2) Conversion scharf → (3) Ranking-Schutz → (4) Sichtbarkeit → (5) Messung → (6) Go-Live.** Ohne (3) verliert die Migration Ranking; ohne (2) ist Traffic wertlos.

---

## Phase 0 — Arbeitsstand sichern (autonom, sofort)

### Task 0.1: Ops-Helfer + Pläne committen & pushen
**Files:**
- `ops/n8n/run-n8n.sh`, `ops/n8n/README-runbook.md`
- `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`, `docs/superpowers/plans/2026-06-07-hsb-masterplan-golive.md`

- [ ] **Step 1: Stagen + committen**

```bash
cd /Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden
git add ops/n8n/run-n8n.sh ops/n8n/README-runbook.md docs/superpowers/plans/
git commit -m "ops(n8n): node@20-Starter, Runbook & Go-Live-Masterplan + Lead-Pipeline-Plan"
```

- [ ] **Step 2: Pushen**

Run: `git push origin main`
Expected: `main -> main`, danach `git status -sb` zeigt `## main...origin/main` ohne „voraus".

---

## Phase 1 — Lead-Pipeline scharf schalten (Conversion = #1 Ziel)

> Vollständige Tasks im Detailplan `2026-06-07-hsb-lead-pipeline.md`. Hier nur die Meilensteine zum Abhaken.

- [ ] **1.1** UI-Publish des n8n-Workflows (User-Klick auf `http://localhost:5678`) → production-Webhook registriert
- [ ] **1.2** SMTP-Credential + echten Empfänger setzen (User liefert Zugangsdaten) → Re-Publish
- [ ] **1.3** Lokaler Fake-Lead-E2E: 400 (invalid) / 200 + Mail + Archiv (valid)
- [ ] **1.4** Stabile öffentliche n8n-URL (Cloudflare Tunnel, `--protocol http2`, `WEBHOOK_URL` gesetzt)
- [ ] **1.5** `PUBLIC_LEAD_ENDPOINT` setzen + Website-E2E-Fake-Lead über Preview

---

## Phase 2 — Ranking-Schutz: 301-Redirect-Map (HERABGESTUFT — Befund 2026-06-07)

**Befund (verifiziert):** Die Live-WordPress-Seite (Yoast `sitemap_index.xml` → `page-sitemap.xml`) hat **nur EINE indexierte URL: die Homepage `https://hsb-boden.de/`**. Es gibt keine tiefen Unterseiten mit Ranking-Autorität. Damit ist die Migration ranking-seitig unkritisch — `/` → `/` ist 1:1, kein Redirect nötig.

### Task 2.1: Inventar bestätigt — minimaler Redirect-Bedarf
**Files:** keine

- [ ] **Step 1: Inventar gegenchecken** (ob seit heute neue URLs dazukamen)

Run: `for s in $(curl -s https://hsb-boden.de/sitemap_index.xml | grep -oE '<loc>[^<]+' | sed 's/<loc>//'); do curl -s "$s" | grep -oE '<loc>[^<]+' | sed 's/<loc>//'; done | grep -v '\.xml$' | sort -u`
Expected: nur `https://hsb-boden.de/` (Stand 2026-06-07). Bei mehr URLs → Task 2.2 ausführen.

### Task 2.2: `_redirects` NUR falls Inventar > Homepage
**Files:**
- Create (bedingt): `public/_redirects`

- [ ] **Step 1:** Nur wenn Task 2.1 zusätzliche alte Pfade zeigt: pro Pfad einen 301-Eintrag (`/alt /neu 301`) anlegen. Bei reinem Homepage-Inventar: **diese Phase entfällt**, kurz im Memory vermerken.

### Task 2.2: `_redirects` schreiben
**Files:**
- Create: `public/_redirects`

- [ ] **Step 1: Datei anlegen** (Format: `quelle ziel statuscode`; ein Eintrag pro alter URL)

```
# WordPress → Astro 301-Migration (Ranking-Erhalt)
/leistungen/saeureschutz.html   /leistungen/saeureschutzbau   301
/leistungen/keramik.html        /leistungen/industriekeramik  301
# ... ein Eintrag pro Eintrag aus Task 2.1 Step 2
```

- [ ] **Step 2: Build + lokal prüfen, dass _redirects ins dist gelangt**

Run: `npm run build && ls dist/_redirects 2>/dev/null || find dist -name _redirects`
Expected: Datei liegt im Build-Output.

- [ ] **Step 3: Nach Preview-Deploy 301 verifizieren** (curl -I gegen Preview)

Run: `curl -sI https://hsb-boden-preview.cherinojoel.workers.dev/leistungen/saeureschutz.html | grep -iE "HTTP|location"`
Expected: `HTTP/.. 301` + korrekte `location:`.

- [ ] **Step 4: Commit**

```bash
git add public/_redirects
git commit -m "seo(migration): 301-Redirect-Map WordPress → Astro"
```

---

## Phase 3 — AI-Overview/SEO-Content-Härtung (Sichtbarkeit)

### Task 3.1: Product/Service-Schema für Bodensysteme ergänzen
**Files:**
- Modify: `src/lib/schema.ts` (neue Builder neben den bestehenden)
- Modify: `src/pages/leistungen/[slug].astro` (Builder einbinden)

- [ ] **Step 1: Builder ergänzen** (analog zu `buildFaqJsonLd`)

```ts
export function buildServiceJsonLd(s: { name: string; description: string; areaServed?: string }) {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: s.name,
    description: s.description,
    provider: { "@type": "Organization", name: "HSB Boden" },
    areaServed: s.areaServed ?? "DE",
  };
}
```

- [ ] **Step 2:** In `leistungen/[slug].astro` einbinden + im `<head>` als `<script type="application/ld+json">` ausgeben (Muster: bestehende FAQ-Einbindung).
- [ ] **Step 3: Build + validieren**

Run: `npm run build` und stichprobenartig `grep -r '"@type": "Service"' dist/leistungen/ | head`
Expected: Service-JSON-LD im gerenderten HTML.

- [ ] **Step 4: Commit** — `git commit -am "seo(schema): Service-JSON-LD für Leistungsseiten"`

### Task 3.2: seo-content-reviewer über alle ungeprüften Seiten
**Files:** keine (Review)

- [ ] **Step 1:** Subagent `seo-content-reviewer` auf `leistungen/*`, `branchen/*`, `wissen/*`, `kontakt`, `impressum`, `datenschutz`, `karriere` ansetzen — Fokus: vage Claims, erfundene Zahlen, fehlende faktische Dichte (DIN-Normen statt „hoch belastbar").
- [ ] **Step 2:** Befunde sammeln, belegbare Fixes umsetzen (keine erfundenen Zahlen — `mistakes.md`), je Fix Gate + Commit.

---

## Phase 4 — Analytics & Search Console (Messung)

### Task 4.1: GA4/GTM einbinden (datenschutzkonform)
**Files:**
- Modify: `src/components/seo/SEOHead.astro` (oder Layout) — GA4-Snippet hinter Consent

- [ ] **Step 1:** Vom User GA4-Measurement-ID einholen (nicht erfindbar).
- [ ] **Step 2:** Snippet einbauen, erst nach Cookie-Consent laden; mit bestehendem `hsb:tracking`-Event koppeln.
- [ ] **Step 3:** Build + im Browser Network-Tab prüfen, dass GA erst nach Consent feuert. Commit.

### Task 4.2: Google Search Console
- [ ] **Step 1:** Nach DNS-Cutover (Phase 5) Property verifizieren + Sitemap `https://hsb-boden.de/sitemap.xml` einreichen.

---

## Phase 5 — Production Go-Live (⛔ GESPERRT bis Freigabe, siehe Arbeitszustand 2026-06-10)

### Task 5.1: Pre-Production-Gate (ADR-003)
- [ ] **Step 1:** `npm run check && npm run test:run && npm run build` → grün
- [ ] **Step 2:** Playwright Desktop(1440)+Mobile(390) gegen Prod-Build, 0 Console-Errors
- [ ] **Step 3:** Lighthouse ≥ 95/100, Zahlen notieren
- [ ] **Step 4: Dry-Run**

Run: `wrangler deploy --env production --dry-run`
Expected: kein Fehler, korrekte Routes (`hsb-boden.de/*`).

### Task 5.2: Production-Deploy + DNS-Cutover (NUR nach expliziter Freigabe)
> ⚠️ Live-WordPress NICHT anfassen, bis Cutover bewusst entschieden ist (Non-Negotiable AGENTS.md).

- [ ] **Step 1:** User-Freigabe für Production-Deploy einholen.
- [ ] **Step 2:** `npm run check && npm run test:run && npm run build && wrangler deploy --env production`
- [ ] **Step 3:** DNS `hsb-boden.de` von WordPress → Cloudflare umstellen (User, Domain-Zugang).
- [ ] **Step 4:** 301-Redirects live verifizieren (Task 2.2 Step 3 gegen Production).
- [ ] **Step 5:** Search Console verbinden (Task 4.2).

### Task 5.3: Memory/Handoff finalisieren
- [ ] **Step 1:** `CANONICAL_STATE.md` + `working_set.json` auf „live" aktualisieren.
- [ ] **Step 2:** `ai-state checkpoint --tool claude --task "hsb-boden Go-Live" --status completed`.

---

## 🔴 User-Inputs, die Tasks blockieren (nicht erfindbar)
| Input | Blockt |
|---|---|
| n8n UI-Publish (1 Klick) | Phase 1.1 |
| SMTP-Zugang + Empfänger-Mail | Phase 1.2 |
| WordPress-URL-Inventar (falls Sitemap unvollständig) | Phase 2.1 |
| GA4-Measurement-ID | Phase 4.1 |
| Freigabe Production-Deploy + DNS-Zugang | Phase 5.2 |
| Telefonnummer final bestätigen | Go-Live-Feinschliff |

## Skill-Einsatz (für die Umsetzung)
- **writing-plans** (dieser Plan) → **subagent-driven-development / executing-plans** (Umsetzung)
- **verification-before-completion** + ADR-003-Gate vor jedem „fertig"
- **seo-content-reviewer** (Subagent, Phase 3.2), **web-perf** (Lighthouse/Core Web Vitals)
- **wrangler** / **workers-best-practices** (Deploy, Phase 5), **playwright/chrome-devtools** (E2E)
- **systematic-debugging** bei Fehlern (wie beim n8n-Publish-Befund angewandt)

## Self-Review
- **Spec-Coverage:** Website-Push ✅ (bereits erfolgt, Phase 0 sichert Rest); Lead-Pipeline (Phase 1); Ranking-Schutz/301 (Phase 2); AI-Overview/Schema (Phase 3); Analytics (Phase 4); Go-Live/DNS (Phase 5). Alle MASTERPLAN- und PLAN_go-live-Punkte abgebildet.
- **Keine Platzhalter ohne Inhalt:** Redirect-/Schema-/Analytics-Tasks enthalten konkrete Befehle/Code; User-Inputs explizit als Blocker-Tabelle.
- **Konsistenz:** Lead-Pipeline nicht dupliziert, sondern referenziert (DRY).
