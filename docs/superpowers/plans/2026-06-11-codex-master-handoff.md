# HSB-Boden / HEXAFLOOR — Master-Handoff für Codex (Stand 2026-06-11)

> Dieses Dokument ist ein vollständiger, eigenständiger Übergabe-Prompt. Es fasst
> den gesamten bisherigen Arbeitsstand zusammen und definiert den verbindlichen
> Rahmen für die Fortsetzung durch ein anderes Coding-Agent-System (Codex).
> Codex benötigt **keinen** Zugriff auf die vorherige Konversation — alle
> relevanten Informationen stehen hier oder in den referenzierten Repo-Dateien.

## 1. Projektkontext

- Repository: `cherinojoel-lang/hsb-boden` (Astro 5, TypeScript, Tailwind,
  Cloudflare Workers / `output: "server"`).
- Arbeitsbranch: `claude/hsb-boden-architecture-o2479f` (PR #5, **draft**, offen).
- Cloudflare Auto-Deploy auf jeden Push: Branch-Preview-URL
  `https://claude-hsb-boden-architecture-o2479f-hsb-boden.cherinojoel.workers.dev`.
- Ziel: Kein "fertiges Website-Projekt", sondern ein vollständiges
  B2B-Akquise-, Vertriebs-, Vertrauens-, SEO-, Referenz-, Lead-, CRM- und
  Autoritätssystem für HSB-Boden / HEXAFLOOR Säurebau GmbH (Industrieböden,
  Säureschutzbau, Keramik, PU-Beton, Entwässerung, Sanierung — Schwerpunkt
  Lebensmittel-/Getränke-/Chemie-/Pharmaindustrie, NRW/Münsterland).

## 2. Standing Constraints (NICHT verhandelbar, gelten für JEDEN Schritt)

1. **Einzige Sperre** (aus dem Master Execution Plan V2): KEINE
   Domainübernahme, KEIN DNS-Cutover, KEINE Produktionsaktivierung, KEINE
   Live-Umschaltung von `hsb-boden.de`. PR #2 (Worker-Umbenennung →
   Produktion) bleibt **unmerged**. Alles andere darf analysiert, vorbereitet,
   verbessert, getestet und produktionsreif vorbereitet werden.
2. **AGENTS.md-Regeln** (im Repo-Root, vollständig lesen und befolgen):
   - Keine erfundenen Zahlen/Statistiken/Claims.
   - Keine neuen Kundennamen/Logos/Standorte ohne dieselbe Freigabelogik wie
     in `docs/launch/referenzen-freigabe.md` §0 dokumentiert.
   - Keine Fremd-/Maschinenlogos auf neuen Fotos (z. B. KLINGER-Logo-Regel,
     siehe `referenzen-freigabe.md` §4 für bereits geprüfte/aussortierte
     Bilder).
3. **Vor jedem Content-/Page-Commit**: `seo-content-reviewer`-Agent (siehe
   `.claude/agents/seo-content-reviewer.md`) muss **PASS** zurückgeben
   (prüft erfundene Claims, Duplicate H1, Alt-Texte, Meta-Längen,
   Trust-Integrität). Bei FAIL: Text nachbessern, erneut prüfen.
4. **Vor jedem Commit Gate**:
   - `npm run check` → Ziel 0 Fehler / 0 Warnungen / 0 Hinweise
   - `npm run test:run` → Ziel 9/9 grün (Tests erzwingen u. a. die
     Referenz-Freigabelogik: anonyme Referenzen dürfen nie mit
     Logo/Klarname/exaktem Standort angezeigt werden)
   - `npm run build` → muss erfolgreich durchlaufen
5. **Pflicht-Gate nach jeder Phase** (siehe Abschnitt 6): Analyse, Änderungen,
   Verifikation, Risiken, Empfehlungen, Nächster Schritt — danach **stoppen**,
   keine automatische Fortsetzung zur nächsten Phase ohne Freigabe.

## 3. Governing Protocol

Vollständiges 12-Phasen-Protokoll:
`docs/superpowers/plans/2026-06-10-master-execution-plan-v2.md`
("HEXAFLOOR / HSB-BODEN — Master Execution Plan V2 — Claude Autonomous
Execution Protocol"). Kernregel: **Nach Prioritäten arbeiten, nicht nach
starrer Phasenreihenfolge** — wie ein autonomes Expertenteam, jede Entscheidung
muss mindestens eines verbessern: Vertrauen, Fachautorität, Sichtbarkeit,
Conversion, Leadqualität, Skalierbarkeit, Markenwahrnehmung.

Phasenübersicht (0–12): Project Reality Audit → Wettbewerbsanalyse → Website
Excellence → Referenzen/Logos/Medien → Authority Excellence → SEO Excellence →
Cloudflare Excellence → Lead Engine Excellence → CRM & E-Mail → Flyer &
Kampagne → Analytics Excellence → Go-Live Readiness Audit →
Produktionsfreigabe (nur durch den Nutzer, nach allen Phasen).

## 4. Bisheriger Arbeitsstand (Phasen 0–2, abgeschlossen)

### Phase 0 — Project Reality Audit (Commit `df1460e`)
Output: `docs/audit/2026-06-10-master-status-matrix.md` — 16-Bereiche-Matrix
(Repo, Build/Tests, Seitenstruktur, Referenzen, Medien, SEO, interne
Verlinkung, Wissen, Design/Mobile, Lead-Engine, CRM, Flyer, Analytics,
Cloudflare, Rechtliches, Wettbewerb, Go-Live-Sperre) je mit Status/Risiko/
Potenzial. Konsolidierte Prioritätenliste (1. interne Verlinkung, 2.
OG-Image+srcset, 3. Mobile/Lighthouse-Audit, 4. Wettbewerbsanalyse, 5.
Wissen-Vertiefung+FAQ, 6. Cloudflare-Härtung, 7. Lead/CRM/E-Mail/Analytics).
Offene User-Inputs (außerhalb Repo, blockieren jeweilige Punkte): SMTP, GA4-ID,
n8n-Hosting, juristische Prüfung, echte Kundenlogos als Dateien,
Projektflyer-Quelldatei, Videomaterial.

### Phase 1 — Wettbewerbsanalyse (Commit `901ab3f`)
Output: `docs/audit/2026-06-10-competitive-gap-report.md` — 8 Wettbewerber
auditiert (Steuler Linings, Remmers, Sika/Ucrete, StoCretec, ARDEX, Korodur,
**KSB Räckers** und **Ahauser Säurebau** als direkte Regionalwettbewerber).
Vergleichsmatrix + 6 Kernerkenntnisse + priorisierte Chancenliste P1–P11.
Wichtigste Befunde:
- HSBs Deutschlandkarte ist ein **Alleinstellungsmerkmal** (kein Wettbewerber
  hat sowas).
- "Planung + Ausführung aus einer Hand" ist die **größte
  Positionierungs-Chance** (kein Wettbewerber besetzt das explizit).
- Lücken: Zertifikate (DEKRA/TÜV/WHG §19), persönliche Ansprechpartner mit
  Foto, technische Downloads/LV-Vorlagen — alle **blockiert durch fehlende
  User-Inputs**.

### Phase 2 — Website Excellence (Commits `8702008`, `f0fa816`)
Output: `docs/audit/2026-06-11-phase2-website-excellence.md`. Visuelles Audit
per Playwright (35 Screenshots, 7 Seiten × 5 Breakpoints) gegen die
Branch-Preview-URL. Umgesetzte Änderungen:
1. **Interne Verlinkung** (Schema in `src/lib/content.ts` um
   `relatedArticles`/`relatedServices`/`relatedIndustries` erweitert; Daten in
   `src/data/{services,industries,articles}.ts` befüllt; neue Cross-Link-
   Sektionen in `src/pages/{leistungen,branchen,wissen}/[slug].astro`).
2. **OG-Image**: `public/brand/og-image.png` (1200×630, per sharp aus Logo +
   Brand-Farben generiert), eingebunden in `src/components/seo/SEOHead.astro`
   (vorher 322×237-Logo).
3. **Hero-srcset**: `public/media/hsb/current/industrieboden-baustelle-640.webp`
   (640px-Variante) + `srcset`/`sizes` in `src/pages/index.astro`.
4. **P1-Positionierung**: neue Startseiten-Sektion „Planung und Ausführung aus
   einer Hand" direkt unter dem Hero.
5. **P2-Referenzkarte als USP**: `ReferenceMapPreview.astro` Eyebrow zu
   „Projektkarte Deutschland" + Erläuterungssatz (nach
   seo-content-reviewer-Hinweis präzisiert: „Kunden und Projektstandorte"
   statt pauschal „umgesetzt", um keine Übergeneralisierung der 21
   nicht-vertieften Standorte zu erzeugen).
6. **P5-CTA geschärft**: `src/components/sections/CTASection.astro`
   Default-Title/Label von „Kostenlose Ersteinschätzung vor Ort" /
   „Ersteinschätzung anfordern" zu „Werksbegehung oder technische
   Bodenanalyse anfragen" / „Werksbegehung anfragen" (wirkt global über
   Default-Props; `wissen/[slug].astro` PageHero-CTA für Konsistenz
   angeglichen).
7. `playwright@1.60.0` als devDependency ergänzt.

Alle Gates grün, seo-content-reviewer PASS, Cloudflare-Deploy verifiziert.

**Neuer, noch offener Befund aus Phase 2:** Mobiles Cookie-Consent-Banner
(`src/components/layout/CookieConsent.astro`) verdeckt bei 390px Breite ca.
45–50 % des ersten Bildschirms (CTA-Buttons + Teile der H1) beim ersten
Seitenaufruf. Funktional/rechtlich korrekt (DSGVO-Banner, schließt nach
Auswahl), aber conversion-kritisch. **Bewusst nicht behoben** — DSGVO-Mechanik
darf nicht angefasst werden, nur Layout/Abstände, mit besonderer Sorgfalt.

## 5. Technisches Setup-Wissen (für Codex wichtig)

- **Playwright/Chromium-Workaround**: Das im Sandbox-Image installierte
  `/opt/pw-browsers/` enthält nur Chromium-Build `chromium-1194`, während
  `playwright@1.60.0` standardmäßig Build `1223` erwartet. Funktionierender
  Launch:
  ```js
  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    args: ["--disable-quic", "--disable-features=EncryptedClientHello", "--ignore-certificate-errors"],
  });
  ```
  Die Flags sind nötig, weil das Sandbox-Netzwerk QUIC/ECH zur
  Cloudflare-Preview-URL sonst mit `ERR_QUIC_PROTOCOL_ERROR` /
  `ERR_ECH_FALLBACK_CERTIFICATE_INVALID` abbricht.
- **Node-Skripte für Playwright** müssen im Projektverzeichnis liegen (nicht
  `/tmp`) und die Endung `.cjs` haben (Projekt ist `"type": "module"`).
- **Semrush MCP** (`mcp__*` Toolkit) ist NICHT nutzbar (Plan ohne MCP-Zugang) —
  nicht erneut versuchen, stattdessen direkte WebFetch/WebSearch-Audits.
- Referenz-/Logo-System: `getPublicReferences()` in `src/lib/content.ts`
  berechnet `displayName`/`displayLocation`/`canShowExactLocation`/`logo`
  basierend auf `approvalStatus: "approved" | "anonymous" | "internal"`.
  `tests/content.test.ts` erzwingt: anonyme Referenzen NIE mit
  Logo/Klarname/Standort.

## 6. Pflicht-Gate-Format (für jede Phase exakt einhalten)

```
## Phase X — <Name>: Pflicht-Gate-Report

1. Analyse — was wurde geprüft/gefunden
2. Änderungen — konkrete Diffs/Dateien/Commits
3. Verifikation — check/test/build-Ergebnisse, seo-content-reviewer-Verdikt,
   Visual-Check
4. Risiken — was ist riskant, was wurde bewusst nicht angefasst und warum
5. Empfehlungen — nächste sinnvolle Schritte
6. Nächster Schritt — STOPP, auf Freigabe warten
```

## 7. Aufgabe für Codex (Fortsetzung)

Setze die Arbeit gemäß Master Execution Plan V2 fort, priorisiert wie folgt:

1. **Mobiles Cookie-Consent-Banner kompakter gestalten**
   (`src/components/layout/CookieConsent.astro`): Ziel ist, dass auf
   360–430px Breite weniger vertikaler Platz vom Banner verbraucht wird
   (z. B. kompaktere Typografie/Abstände, Buttons nebeneinander statt
   gestapelt, ggf. Text kürzen). Die DSGVO-Logik (localStorage-Consent,
   `hsb:consent`-Event, Kategorien-Toggle, Footer-Reopen) **darf nicht
   verändert werden** — nur Layout/CSS. Vorher/Nachher-Screenshot bei 390px
   erstellen.
2. **Lighthouse-Audit nachholen** für Startseite, eine Branchenseite (z. B.
   `/branchen/molkerei/`) und `/referenzen/` gegen die Branch-Preview-URL.
   Ergebnisse (Performance/SEO/Accessibility/Best-Practices) in einem neuen
   Audit-Dokument unter `docs/audit/` festhalten.
3. **Phase 3 — Referenzen/Logos/Medien**: Referenzinventar vervollständigen
   (Kunden, Logos, Standorte, Projekte, Bilder, Videos), Deutschlandkarte ggf.
   ausbauen, Medienstrategie dokumentieren. Nur mit bereits freigegebenen/
   dokumentierten Referenzen/Fotos arbeiten (siehe
   `docs/launch/referenzen-freigabe.md`). Keine neuen Kundennamen/Logos ohne
   dieselbe Freigabelogik wie in §0 dokumentiert.
4. Danach nach Priorität weiter (Phase 4 Wissen-Vertiefung+FAQ, Phase 5 SEO,
   Phase 6 Cloudflare-Härtung, ...) — siehe konsolidierte Prioritätenliste in
   `docs/audit/2026-06-10-master-status-matrix.md`.

Nach jeder Phase: Pflicht-Gate-Report (Abschnitt 6), Commit + Push auf
`claude/hsb-boden-architecture-o2479f`, dann **STOPPEN**.
