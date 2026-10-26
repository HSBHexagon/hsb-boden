# Google-Messung und Search Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Google-Messung (GA4, Search Console) ist nach Googles aktueller Consent-Anleitung aufgebaut, durch Belege statt Annahmen abgesichert, und die Datenflüsse zu Google und Cloudflare stimmen mit dem Einwilligungstext überein.

**Architecture:** Erst die Reihenfolge der Consent-Aufrufe im Loader korrigieren (Code, testgetrieben), dann die tatsächlich genutzten Google-Ursprünge messen (Eingabe für die CSP im Cloudflare-Plan), dann die Einwilligungsfrage zum Cloudflare-Beacon klären, zuletzt die Owner-Belege in GA4 und Search Console.

**Tech Stack:** `gtag.js` (GA4, ohne GTM-Container), Astro, Vitest/jsdom, Playwright (vorhandene devDependency), Google Search Console.

**Spec:** Keine Spezifikation vorhanden. Vorarbeit im Repo: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` (Stand 2026-08-03). Dieser Plan schließt deren offene Owner-Gates, statt sie neu zu schreiben.

## Global Constraints

- Keine Website-Code-Änderung ohne Freigabe: `src/`, `public/`, `components/`, `layouts/`, `styles/`, `astro.config.*`, `wrangler.toml`, `package.json`, Lockfiles. Tasks, die sie berühren, beginnen mit „Freigabe einholen“.
- Kein Push, kein Deploy ohne Freigabe; `PROJECT_TRUTH.md`: „Keine produktive Website-Veröffentlichung durch diesen Auftrag.“ Keine Secrets, keine Messdaten mit Personenbezug in Repo oder Chat.
- Es wird kein GTM-Container, keine Property, kein Key Event und keine Search-Console-Verknüpfung aus dem Repository angelegt (so steht es in der Readiness-Doku); das sind **Owner-Aktionen**.
- Die Consent-Texte sind keine Rechtsberatung. Rechtliche Bewertung (Basic vs. Advanced Mode, Cloudflare-Beacon) trifft der Owner mit seiner Beratung.
- Produktions-GA4 darf auf Preview-Hosts nie laden (bestehende Isolation in `analytics.ts`, Test vorhanden) und bleibt so.
- Vor Commit `python3 scripts/verify_ssot.py` mit Exit 0; vor Abschluss `npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run` in `apps/website`.
- Datenquellen: Ahrefs-Connector antwortet „Insufficient plan“, Semrush meldet fehlende API-Einheiten (beide am 2026-10-26 geprüft). Der Plan stützt sich auf keine von beiden; Keyword- und Wettbewerbsdaten sind **nicht** Teil dieses Plans.

## Ist-Zustand (Belege)

| Befund | Beleg |
|---|---|
| GA4 lädt erst nach aktiver Analytics-Einwilligung (Basic-Variante). Beim Laden ruft der Loader `consent update` (nur `analytics_storage: granted`), dann `js`, dann `config`. Ein `consent default` wird nirgends gesetzt. | `apps/website/src/lib/analytics.ts:49-74`; `grep -n '"default"' apps/website/src/lib/analytics.ts` ohne Treffer |
| Widerruf sendet `consent update` mit allen vier Typen `denied`. | `analytics.ts:76-91` |
| Ein Cloudflare-Web-Analytics-Beacon wird auf der Produktionsdomain **ohne** Einwilligungsprüfung geladen; `consent.ts` beschreibt „Analyse“ als erst nach Einwilligung aktiv. | `apps/website/src/layouts/BaseLayout.astro:86-90`, `src/lib/cloudflareAnalytics.ts:5-16`, `src/data/consent.ts` |
| Die CSP erlaubt Google-Ads- und DoubleClick-Domains, obwohl „Marketing“ in V1 deaktiviert ist. | `apps/website/public/_headers:9`, `consent.ts` |
| Die Datenschutzerklärung nennt als Consent-Tool „Real Cookie Banner“ (WordPress-Plugin von devowl.io). Die Astro-Seite nutzt einen eigenen Banner (`CookieConsent.astro`); „Real Cookie Banner“ kommt sonst nirgends in `src/` vor. Der Cloudflare-Beacon wird in der Erklärung nicht genannt. | `apps/website/src/pages/datenschutz/index.astro:373-377`; `rg -i "real cookie" apps/website/src` |
| `google-site-verification` als Meta-Tag vorhanden. | `apps/website/src/components/seo/SEOHead.astro:26` |
| Offene Owner-Gates laut Readiness-Doku: richtige GA4-Property, DebugView-Beleg für `generate_lead`, Key Event, kanonische Search-Console-Property, Sitemap-Status, danach GA4/GSC-Verknüpfung. | `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` |
| `.com`-Akquise-Domain wird per 301 auf `www.hsb-boden.de` geleitet. | `apps/website/public/_redirects` (letzte Regel) |

## Quellen (abgerufen 2026-10-26)

- [S1] Google, Consent-Anleitung für Tags (Seitenstand 2026-10-13): https://developers.google.com/tag-platform/security/guides/consent. Vier Typen `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`; `gtag('consent','default',…)` gehört vor jeden `config`- oder `event`-Aufruf („If your consent code is called out of order, consent defaults won't work.“); `wait_for_update` nur für asynchrone CMPs; bei der erweiterten Variante muss auf der Seite mit der Zustimmung ein `update` folgen. Die Seite erklärt den Unterschied Basic/Advanced selbst nicht, sondern verweist auf eine Konzeptseite, die hier nicht gelesen wurde.
- [S2] Cloudflare, Distributed Web Performance Architecture: https://developers.cloudflare.com/reference-architecture/diagrams/content-delivery/distributed-web-performance-architecture/. Beschreibt Web Analytics als „privacy-first, cookie-less“. Das ist Herstellerbeschreibung, keine Rechtsbewertung.
- Nicht verwendet: Anbieter-Blogs zu Durchsetzungsterminen und zu einer angeblichen Änderung von `ad_storage` im Juni 2026. Die Aussagen sind nicht an Googles Dokumentation belegt.

## Review Focus

- Widerruf nach erteilter Einwilligung: Der Loader setzt `denied`; ob bereits gesetzte `_ga*`-Cookies danach bestehen bleiben, ist im Browser zu prüfen und festzuhalten (nicht zu behaupten).
- Ad-Blocker oder blockierter Google-Request: Der Lead-Abschluss und die Weiterleitung auf die Danke-Seite dürfen nicht an `generate_lead` hängen (die Doku nennt eine begrenzte Wartezeit); Verhalten mit blockiertem `gtag.js` prüfen.
- Preview-Hosts und `hsb-boden.pages.dev` laden nie das Produktions-GA4 (Test vorhanden), auch nicht mit gespeicherter Einwilligung.
- Nutzer ohne Einwilligung sehen keinen Request an `googletagmanager.com` (Netzwerkmitschnitt in Task 2).
- Sprachvarianten `/en/` und `/fr/` verwenden denselben Loader und denselben Consent-Schlüssel `hsb-consent-v1`; Gegenprobe in Task 2 auf allen drei Sprachen.

---

### Task 1: Consent-Default vor `config` setzen

**Files:**
- Modify: `apps/website/src/lib/analytics.ts` (Funktion `loadAfterConsent` in `createAnalyticsLoader`)
- Test: `apps/website/tests/analytics.test.ts`

**Interfaces:**
- Consumes: `createAnalyticsLoader(browserWindow: Window, browserDocument: Document, measurementId?: string, hostname?: string): { initialize(): void }` (bestehend).
- Produces: unverändert dieselbe Signatur; neues Verhalten: beim ersten Laden pro Seite steht in `window.dataLayer` die Reihenfolge `["consent","default",{…vier Typen "denied"}]`, `["consent","update",{analytics_storage:"granted",…}]`, `["js",…]`, `["config",MEASUREMENT_ID,…]`.

- [ ] **Step 1: Freigabe einholen** für `src/lib/analytics.ts`.
- [ ] **Step 2: Failing Test schreiben** in `analytics.test.ts`, Name `setzt vor config ein consent default mit allen vier Typen auf denied`. Assertions: Eintrag `consent/default` existiert, enthält `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization` jeweils `"denied"`; sein Index in `dataLayer` ist kleiner als der von `consent/update`, `js` und `config`. Zweiter Test, Name `sendet das consent default bei erneuter Zustimmung nach Widerruf nicht erneut`.
- [ ] **Step 3: Run.** `cd apps/website && npx vitest run tests/analytics.test.ts`. Expected: die neuen Tests FAIL, die fünf bestehenden PASS.
- [ ] **Step 4: Implementieren** in `loadAfterConsent`: Der Default wird nur im Zweig `if (loaded) return;` davor einmalig gesetzt (vor dem ersten `update`). Hinweis: In der Basic-Variante existiert vor der Einwilligung kein `gtag`; der Default wirkt daher in demselben Aufruf wie das `update`. Er erfüllt die Reihenfolge aus [S1] und ist in Task 4 im Tag-Assistant zu belegen.
- [ ] **Step 5: Run.** `npx vitest run tests/analytics.test.ts && npm run check`. Expected: alle PASS, 0 Fehler.
- [ ] **Step 6: Commit.** `git add apps/website/src/lib/analytics.ts apps/website/tests/analytics.test.ts`, Nachricht `fix(analytics): Consent-Default vor config setzen`.

### Task 2: Tatsächlich genutzte Google-Ursprünge messen

**Files:**
- Create: `apps/website/scripts/capture-google-origins.mjs`
- Create: `docs/analytics/GOOGLE_ORIGINS_EVIDENCE_2026-10.md`

**Interfaces:**
- Produces: Skript `node scripts/capture-google-origins.mjs <baseUrl>`; Ausgabe: je Szenario („ohne Einwilligung“, „mit Analytics-Einwilligung“, „nach Widerruf“) eine sortierte Liste der Hosts, an die der Browser Requests sendet. Ergebnisdatei ist die Eingabe für Task 4 im Cloudflare-Plan.

- [ ] **Step 1: Skript schreiben** mit der vorhandenen Playwright-Version: Seite öffnen, `page.on("request")` sammeln, Einwilligung über den Cookie-Banner setzen (Bedienelemente aus `CookieConsent.astro` lesen), Seiten `/`, `/en/`, `/fr/` je Szenario. Das Skript lädt nur die übergebene URL und setzt kein Produktions-GA4 voraus: gegen die lokale Vorschau `npm run preview` laufen die Google-Requests laut Hostprüfung gar nicht; für den Produktionsbelegfall übergibt der Owner den Mitschnitt aus dem Browser (Netzwerk-Tab, HAR ohne Cookies), den das Skript lesen kann (`--har <datei>`).
- [ ] **Step 2: Run (ohne Einwilligung).** `node scripts/capture-google-origins.mjs http://localhost:4321`. Expected: keine Hosts mit `google` im Namen.
- [ ] **Step 3: Ergebnis auswerten:** Liste der benötigten Origins gegen `script-src`, `connect-src` und `img-src` in `public/_headers` halten; Differenz (erlaubt, aber nie genutzt) in die Evidenzdatei schreiben.
- [ ] **Step 4: Commit.** `git add apps/website/scripts/capture-google-origins.mjs docs/analytics/GOOGLE_ORIGINS_EVIDENCE_2026-10.md`, Nachricht `docs(analytics): benötigte Google-Origins belegt`.

### Task 3: Einwilligung und Datenschutztext in Einklang bringen (Owner-Entscheidung)

**Files:**
- Modify (nach Entscheidung): `apps/website/src/layouts/BaseLayout.astro`, `apps/website/src/lib/cloudflareAnalytics.ts`, `apps/website/src/data/consent.ts` oder `apps/website/src/pages/datenschutz/index.astro`
- Test: `apps/website/tests/cloudflare-analytics.test.ts`

**Interfaces:**
- Produces: Entscheidung D2 für den Beacon mit zwei Varianten. (a) Beacon erst nach Analytics-Einwilligung laden, Signatur `initializeCloudflareAnalytics(browserWindow, browserDocument, hostname?)` bleibt, intern analog zu `createAnalyticsLoader` auf `hsb:consent` hören. (b) Beacon unverändert lassen und Datenschutzseite sowie Consent-Text anpassen, damit sie ihn korrekt nennen. Entscheidung D3: Der Abschnitt „Real Cookie Banner“ in der Datenschutzerklärung wird durch eine Beschreibung des tatsächlich eingesetzten Banners ersetzt.

- [ ] **Step 1: Ist belegen.** Run: `grep -n -i "web analytics\|beacon\|real cookie" apps/website/src/pages/datenschutz/index.astro apps/website/src/data/consent.ts`. Expected: Treffer nur in `datenschutz/index.astro:373-377` („Real Cookie Banner“, allgemeines „Web-Beacons“); der Cloudflare-Beacon ist nirgends genannt.
- [ ] **Step 2: Owner entscheidet D2 und D3** (mit rechtlicher Beratung; dieser Plan bewertet nichts rechtlich). Empfehlung D2: Variante (a), weil sie den vorhandenen Consent-Text ohne Textänderung einhält. [S2] nennt den Dienst cookie-los; das ersetzt die rechtliche Bewertung nicht. Empfehlung D3: Der Text beschreibt, was die Seite tatsächlich einsetzt; welche Formulierung rechtlich trägt, entscheidet die Beratung des Owners.
- [ ] **Step 3: Bei Variante (a): Failing Test** in `cloudflare-analytics.test.ts`, Name `lädt den Beacon nicht vor einer Analytics-Einwilligung`; zweiter Test `lädt den Beacon nach einem positiven hsb:consent-Ereignis genau einmal`. Run: `npx vitest run tests/cloudflare-analytics.test.ts`. Expected: der erste FAIL.
- [ ] **Step 4: Implementieren und Run.** Expected: alle PASS, `npm run check` ohne Fehler.
- [ ] **Step 5: Commit.** `git add` der geänderten Dateien einzeln, Nachricht `fix(analytics): Cloudflare-Beacon nur nach Einwilligung`.

### Task 4: Messbelege in GA4 (Owner-Aktion)

**Files:**
- Create: `docs/analytics/EVIDENCE_GA4_2026-10.md`

**Interfaces:**
- Produces: Belegdatei mit Datum, Browserprofil und beobachtetem Ergebnis je Zeile (Screenshots ohne personenbezogene Daten).

- [ ] **Step 1: Frisches Browserprofil** auf einer Vorschau öffnen. Expected: kein Request an `googletagmanager.com` vor der Einwilligung.
- [ ] **Step 2: Einwilligung erteilen.** Im Tag-Assistant: `consent default` (alle `denied`) steht vor `config`; danach `consent update` mit `analytics_storage: granted` und den drei übrigen `denied` (belegt Task 1).
- [ ] **Step 3: Testlead über die Vorschau** (keine Produktionsdaten) senden. Expected: `generate_lead` erscheint in DebugView ohne personenbezogene Parameter.
- [ ] **Step 4: Erst danach** `generate_lead` als Key Event markieren (Owner, laut Readiness-Doku).
- [ ] **Step 5: Widerruf testen:** `denied`-Update sichtbar; Verhalten der `_ga*`-Cookies in der Belegdatei festhalten.
- [ ] **Step 6: Commit.** `git add docs/analytics/EVIDENCE_GA4_2026-10.md`, Nachricht `docs(analytics): GA4-Belege 2026-10`.

### Task 5: Search Console prüfen und verknüpfen (Owner-Aktion)

**Files:**
- Modify: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` (Statuszeile und Gate-Liste)

**Interfaces:**
- Produces: aktualisierter Status je Gate (erledigt mit Datum, offen mit Grund).

- [ ] **Step 1: Property festlegen.** Im Konto prüfen, ob eine Domain-Property (DNS-Verifizierung) oder eine URL-Präfix-Property besteht. Das Meta-Tag in `SEOHead.astro:26` gehört zur Präfix-Methode. Keine zweite Property anlegen (Readiness-Doku).
- [ ] **Step 2: Sitemap und Indexierung:** Status der Sitemap und Ausschlussgründe in der Search Console ablesen. Lokal vorab `cd apps/website && npm run build && npm run check:sitemap`. Expected: Exit 0.
- [ ] **Step 3: Weiterleitung prüfen:** `curl -sI https://hsb-boden.com/` liefert 301 auf `https://www.hsb-boden.de/` (nur lesend).
- [ ] **Step 4: GA4/GSC-Verknüpfung** erst setzen, wenn Task 4 abgeschlossen ist.
- [ ] **Step 5: Core-Web-Vitals-Bericht** der Search Console ansehen und Auffälligkeiten ohne Zahlenbehauptung in die Readiness-Doku übernehmen (Quelle: der Bericht des Owners).
- [ ] **Step 6: Commit.** `git add docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`, Nachricht `docs(analytics): Search-Console-Gates aktualisiert`.
