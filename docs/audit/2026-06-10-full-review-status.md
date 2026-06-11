# Full-Site-Review Status (erstellt 2026-06-11, Branch claude/hsb-boden-architecture-o2479f)

> Plan: `docs/superpowers/plans/2026-06-11-hsb-full-site-review.md`
> Geltungsbereich: Preview-/Entwurfsmodus. PR #2 bleibt unmerged, kein Go-Live, keine erfundenen Claims/Logos (AGENTS.md + Masterplan-Arbeitszustand 2026-06-10).

## 1. Statusmatrix (konsolidiert aus Planungsdokumenten)

| Bereich | Status | Offene Punkte | Quelle |
|---|---|---|---|
| Seitenstruktur (DE: index, leistungen, branchen, wissen, referenzen, kontakt, karriere, impressum, datenschutz, danke) | ✅ steht | — | masterplan-golive (Bereits erreicht) |
| Mehrsprachigkeit (en/fr/nl/pl/tr) + Cookie-Consent + Projektfotos | ✅ auf PR-#5-Branch | Sprachvarianten-Qualität prüfen (dieser Review, Task 3) | PR #5 |
| Referenzen-Freigabe | ✅ 5 Klarnamen freigegeben (per Kundenliste „Referenzprojekte 2025"), `pharma-hessen` bewusst anonymisiert | pharma-hessen Re-Check (Task 9); echte Markenlogos = blockiert (Kundenlieferung) | referenzen-freigabe.md §0/§1 |
| Referenzkarte Deutschland (21 zusätzliche Kundenstandorte) | ✅ umgesetzt (`clientLocations.ts`, ReferenceMap) | Visuelle Darstellung prüfen (Task 4) | referenzen-freigabe.md §0.3 |
| Projektfotos (12 WebP in `public/media/hsb/projekte/`) | ✅ eingebunden, KLINGER-Fotos aussortiert | Ungenutzte Fotos für Leistungs-Bildslot prüfen (Task 5/10) | referenzen-freigabe.md §3/§4 |
| 301-Redirect-Map WordPress→Astro | ✅ erledigt (PR #1, 12 Einträge, gegen Preview verifiziert) | — | masterplan Phase 2 |
| Service-JSON-LD Leistungsseiten | ✅ erledigt (TDD) | — | masterplan Phase 3.1 |
| seo-content-reviewer-Härtung | ✅ Durchlauf erfolgt (PR #1/#3/#4) | Neue/geänderte Texte dieses Reviews erneut prüfen (Task 8/9) | masterplan Phase 3.2 |
| Lighthouse-Stand (2026-06-07, gegen Prod-Build) | ✅ Desktop 100/100/100/100, Mobile 99/100/100/100 | Neu messen gegen PR-#5-Preview (Task 4) | masterplan (Bereits erreicht) |
| Lead-Pipeline (n8n UI-Publish, SMTP, Tunnel, `PUBLIC_LEAD_ENDPOINT`) | ⬜ offen | **Out of scope dieses Reviews** (User-Inputs: SMTP, UI-Publish) | lead-pipeline.md, masterplan Phase 1 |
| GA4/GTM + Search Console | ⬜ offen | **Out of scope** (GA4-ID = User-Input; GSC erst nach DNS-Cutover) | masterplan Phase 4 |
| Juristische Prüfung Impressum/Datenschutz | ⬜ offen (Entwürfe) | **Out of scope** (externe juristische Stelle) | hexafloor-abgleich §4 |
| Production-Deploy + DNS-Cutover | ⛔ gesperrt bis Freigabe | **Out of scope**; PR #2 bleibt unmerged | masterplan Phase 5 / Arbeitszustand 2026-06-10 |
| Akquise-System (Flyer, CRM-Light, n8n-Workflows A–E, Pilot, Skalierung) | ⬜ offen | **Out of scope** (außerhalb Repo, Compliance-SOP gilt) | hexafloor-abgleich §2/§3 |
| Launch-Checkliste „Vor Staging" (Gates, Desktop/Mobile, Referenzfreigaben) | 🔄 laufend | Genau das deckt dieser Review ab (Tasks 3–11) | checklist.md |
| Ist-Audit-Lücken der alten WordPress-Seite (Landingpages, Alt-Texte, H-Struktur) | ✅ in Astro-Site adressiert | Verifikation pro Seite (Task 3) | current-state.md |

**Lesart:** Alles mit „Out of scope" wird in diesem Review weder angefasst noch „mit erledigt" (Leitplanke 4). Dieser Review deckt ausschließlich den Website-Entwurf auf dem PR-#5-Branch ab.

## 2. Routenliste (Task 2)

Quelle: `src/lib/content.ts` → `getAllPublicPages()` (von `sitemap.xml.ts` konsumiert) + `src/pages/`-Baum. **34 HTML-Seiten** gesamt.

**DE-Kernseiten (10):** `/` · `/leistungen/` · `/branchen/` · `/referenzen/` · `/wissen/` · `/kontakt/` · `/danke-projektanfrage/` · `/karriere/` · `/impressum/` · `/datenschutz/`

**Leistungen (8):** `industrieboden-saeureschutz` · `keramische-industrieboeden` · `pu-beton-industrieboden` · `epoxidharz-bodenbeschichtung` · `entwaesserung-industrieboden` · `whg-abdichtung-industrieboden` · `bodensanierung-laufender-betrieb` · `dehnungsfugen-rammschutz-industrieboden` (alle unter `/leistungen/<slug>/`)

**Branchen (6):** `lebensmittelindustrie` · `molkerei` · `brauerei-getraenkeindustrie` · `chemieindustrie` · `pharmaindustrie` · `backwarenproduktion-grosskueche` (alle unter `/branchen/<slug>/`)

**Wissen (5):** `pu-beton-oder-keramischer-industrieboden` · `warum-industrieboeden-in-molkereien-versagen` · `saeurefeste-fliesen-industrieboden` · `entwaesserung-gefaelle-produktionsbereiche` · `sanierung-ohne-produktionsstillstand` (alle unter `/wissen/<slug>/`)

**Sprachvarianten (5):** `/en/` · `/fr/` · `/nl/` · `/pl/` · `/tr/` — jeweils nur eine Landingpage (`index.astro` via `InternationalLanding.astro`), KEINE übersetzten Unterseiten.

**Technisch:** `/robots.txt` · `/sitemap.xml` (SSR-Routen)

**Sitemap-Abgleich:**
- Sitemap enthält: 8 Kernseiten (ohne impressum/datenschutz) + 8 Leistungen + 6 Branchen + 5 Wissen + 5 Sprach-Landings = **32 URLs**.
- ⚠️ Befund: `/impressum/` und `/datenschutz/` sind NICHT in `getAllPublicPages()` und damit nicht in der Sitemap. Schweregrad: niedrig (Rechtsseiten in Sitemap optional, Seiten sind verlinkt und crawlbar) — Entscheidung in Task 5.

## 3. Pro-Seite-Findings (Task 3, 4 parallele Read-only-Agents, 2026-06-11)

**Gesamtbild:** 34 Seiten geprüft. H1/seoTitle/description auf ALLEN Seiten vorhanden, einzigartig und inhaltlich sinnvoll. Keine erfundenen Zahlen/Claims gefunden. Alle Bild-alt-Texte vorhanden und beschreibend. hreflang vollständig (6 Sprachen + x-default). Referenz-Freigaben in `references.ts` deckungsgleich mit `referenzen-freigabe.md`.

| Seite | Befund | Schweregrad | Vorschlag |
|---|---|---|---|
| wissen/* (alle 5 Artikel) | Artikel-Sections enthalten nur Überschriften; das Template rendert generische Einordnungssätze statt fachlichem Fließtext | mittel (bekannt) | **Zurückgestellt:** Fließtext kommt aus dem Gemini-Deep-Research-Auftrag (`GEMINI_DEEP_RESEARCH_PROMPT_WISSENSARTIKEL.md`). KEINE generierten Fachzahlen einsetzen (mistakes.md: keine erfundenen Zahlen) |
| branchen/lebensmittelindustrie | `relatedServices` ohne `entwaesserung-industrieboden` (obwohl „stehendes Wasser" als Problem genannt); `relatedArticles` ohne `entwaesserung-gefaelle-produktionsbereiche` | mittel | Felder ergänzen (Task 8) |
| branchen/molkerei | `relatedServices` ohne `industrieboden-saeureschutz` (Milchsäure in description); `relatedArticles` ohne `sanierung-ohne-produktionsstillstand` | mittel | Felder ergänzen (Task 8) |
| branchen/brauerei-getraenkeindustrie | `relatedServices` ohne `industrieboden-saeureschutz` (Säureschutz in description) | mittel | Feld ergänzen (Task 8) |
| branchen/backwarenproduktion-grosskueche | `relatedServices` ohne `entwaesserung-industrieboden` (Nassbereiche zentral); `relatedArticles` mit nur 1 Eintrag | mittel | Felder ergänzen (Task 8) |
| branchen/chemieindustrie, pharmaindustrie | `relatedArticles`/`relatedServices` dünn (je 1 Artikel); Keramik-Bezug nicht verlinkt obwohl `applications` ihn nennt | niedrig | Punktuell ergänzen (Task 8) |
| leistungen/* (alle 8) | Kein Service↔Service-Linkfeld (`relatedServices` existiert in services.ts nicht); Querbezüge laufen nur indirekt über Branchen/Artikel | mittel | In Task 5 entscheiden: Feld analog bestehender related-Patterns ergänzen oder zurückstellen (Leitplanke 5: kein Over-Engineering) |
| leistungen/* (alle 8) | Keine Bilder auf Leistungsseiten (kein Bildfeld in services.ts) — Branchen haben `industryImages`-Äquivalent | mittel | Kandidat Task 10 (nur mit ungenutzten, logo-freien Fotos) |
| lib/i18n.ts (NL) | Agent meldete „farma-" als Tippfehler — **manuell verifiziert: FALSE POSITIVE.** „voedings-, dranken-, farma- en chemieproductie" ist korrekte niederländische Samentrekking (Ergänzungsstrich auf „-productie") | — | Keine Änderung |
| Sprachvarianten en/fr/nl/pl/tr | Übersetzungen vollständig und idiomatisch, Diakritika korrekt (ą/ć/ę…, ü/ş/ç…, è/é/ç…) — KEINE Platzhalter-Stummel | — | Keine Änderung |
| data/clientLocations.ts | 22 Einträge statt der dokumentierten 21 (referenzen-freigabe.md §0.3) — kein funktionaler Fehler, reine Doku-Diskrepanz | niedrig | Doku-Zahl bei nächster Gelegenheit korrigieren (kein eigener Commit nötig) |
| Sitemap | `/impressum/` + `/datenschutz/` fehlen (siehe Abschnitt 2) | niedrig | Entscheidung Task 5 |

Sammelzeilen der Agents: Branchen 6/6 geprüft (0 ohne Befund, alle Befunde = Link-Lücken) · Leistungen 8/8 (Texte/SEO sauber, Befunde = Links/Bilder) · Wissen 5/5 (Struktur sauber, Fließtext fehlt) · Sonstige 16 Seiten/Komponenten (15 ohne Befund).

## 4. Visuelle QA (Task 4, 2026-06-11)

**Geprüfte URL:** `https://claude-hsb-boden-architecture-o2479f-hsb-boden.cherinojoel.workers.dev` (Branch-Alias PR #5, verifiziert auf PR-#5-Stand: 6 hreflang-Sprachen + neue Referenzen-Galerie). 14 Full-Page-Screenshots (7 Seiten × 1440px/390px) unter `/tmp/hsb-review/`.

**Screenshot-Befunde:**

| Befund | Schweregrad | Detail |
|---|---|---|
| Sprachhinweis-Banner überdeckt H1 auf Mobile | **mittel-hoch** | `LanguageSuggest.astro:17` nutzt `fixed top-[72px]` — auf 390px verdeckt der (umbrochene) Banner die erste H1-Zeile (verifiziert auf /kontakt/: „Projektanfrage" unsichtbar). Betrifft genau die internationalen Besucher, auf die PR #5 zielt. → Quick Win Task 5/D |
| Footer auf Sprachseiten (/en/ etc.) bleibt deutsch | niedrig | Spaltenüberschriften/Links (LEISTUNGEN/BRANCHEN/…) nicht lokalisiert; ehrlicher Hinweis „Detailed technical pages are currently available in German" ist vorhanden. → zurückstellen (größerer i18n-Umbau) |
| Referenzkarte + 22 Kundenstandorte + Foto-Galerie auf /referenzen/ | ✅ ok | Drei Galerie-Motive + Karte mit Markern + Namensliste rendern sauber (Desktop + Mobile) |
| Layout/Typografie/Abstände über Seitentypen | ✅ ok | Keine Layoutbrüche, keine abgeschnittenen Bilder/Texte (außer Banner-Befund oben) |

**Lighthouse (mobile-emuliert, gegen Branch-Preview, 2026-06-11):**

| Seite | Performance | Accessibility | Best Practices | SEO |
|---|---|---|---|---|
| `/` | 93 | 97 | 100 | 61 |
| `/branchen/molkerei/` | 93 | 100 | 100 | 69 |
| `/referenzen/` | 100 | 100 | 100 | 69 |

Einordnung der Abweichungen vom dokumentierten Stand (Desktop 100/100/100/100, Mobile 99/100/100/100 vom 2026-06-07):
1. **SEO 61–69 = reines Preview-Artefakt:** Der Branch-Alias liefert `x-robots-tag: noindex` (Cloudflare-Automatik für Versions-Aliase); `hsb-boden-preview.cherinojoel.workers.dev` sendet diesen Header NICHT (gegengeprüft). Kein Handlungsbedarf — auf Produktions-/Preview-Worker nicht vorhanden.
2. **A11y 97 nur auf `/`:** `span.text-hsb-red` im Hero-H1 (#cb0000 auf #161a20) = Kontrast 2.94:1, unter 3:1 für große Schrift. → Quick Win Task 5/D.
3. **Performance 93 auf `/` und Branchenseiten:** CLS 0.113, Verursacher `#cookie-consent` (Banner schiebt Layout beim Einblenden); Speed Index 4.3 s (throttled). → Quick Win: Consent-Banner ohne Layout-Shift positionieren (Task 5/D).

## 5. Optimierungsbacklog (Task 5)

| Kandidat | Entscheidung | Umsetzung / Begründung |
|---|---|---|
| Mobiles Cookie-Consent-Banner kompakter gestalten | **Umgesetzt** | Layout-only-Fix in `src/components/layout/CookieConsent.astro`: reduzierte Mobile-Abstände, kompaktere Typografie, platzsparende Button-Anordnung. Consent-Speicherung, Events, Kategorie-Toggle und Footer-Reopen bleiben unverändert. |
| CLS-Befund `#cookie-consent` reduzieren | **Umgesetzt** | Der Banner bleibt `fixed bottom-0`, nimmt aber auf 360-430px deutlich weniger vertikalen Raum ein. Ziel ist ein kleinerer visueller Eingriff im First View ohne Änderung der DSGVO-Mechanik. |
| Hero-H1-Kontrast auf `/` verbessern | **Umgesetzt** | `src/pages/index.astro`: Highlight im Hero von `text-hsb-red` auf die bestehende hellere Brand-Klasse `text-hsb-red-light` geändert. Keine Textänderung, nur Kontrastkorrektur. |
| Sprachhinweis-Banner überdeckt Mobile-H1 | **Zurückgestellt** | Relevanter Befund, aber nicht Teil dieses Takeovers. Empfehlung: nächster UI-Fix an `src/components/layout/LanguageSuggest.astro`, ohne i18n-Logik zu ändern. |
| Interne Links Branchen↔Leistungen↔Wissen ergänzen | **Zurückgestellt** | Inhaltlich sinnvoll, aber Content-/Datenänderung mit größerer Verlinkungswirkung. Sollte separat mit seo-content-reviewer laufen. |
| Service↔Service-Linkfeld für Leistungsseiten | **Zurückgestellt** | Neues Datenmodell wäre Over-Engineering für diesen kurzen Fix. Bestehende Patterns nicht ohne gesonderte Freigabe erweitern. |
| Leistungs-Bildslot analog Branchenbilder | **Zurückgestellt** | Nur sinnvoll nach erneuter Fotoinventur; keine neuen Bildzuordnungen ohne KLINGER-/Logo-Prüfung und klare Motiventscheidung. |
| Sitemap: `/impressum/` und `/datenschutz/` aufnehmen | **Zurückgestellt** | Niedrige Priorität; Rechtsseiten sind intern verlinkt und crawlbar. Änderung kann später zusammen mit SEO-Feinschliff erfolgen. |
| Kundenstandorte 21/22 | **Dokumentiert** | `src/data/clientLocations.ts` enthält 22 Einträge. Der Audit verwendet ab jetzt 22; die ältere Freigabe-Doku nennt noch 21 und sollte bei der nächsten Dokumentationsrunde angepasst werden. |

## 6. Endergebnis (Task 12)

**Umgesetzt in der Codex-Takeover-Runde nach Claude-Limit:**

- `src/components/layout/CookieConsent.astro`: Mobile-Layout kompakter gemacht; DSGVO-Mechanik unverändert.
- `src/pages/index.astro`: Hero-H1-Highlight auf `text-hsb-red-light` umgestellt, um den Lighthouse-Kontrastbefund zu beheben.
- Dieser Audit-Report: Optimierungsbacklog ergänzt und zurückgestellte Punkte explizit abgegrenzt.

**Verifikation:**

| Prüfung | Ergebnis |
|---|---|
| seo-content-reviewer | PASS für `CookieConsent.astro`, `index.astro`, diesen Audit-Report |
| `npm run check` | PASS: 0 Fehler, 0 Warnungen, 0 Hinweise |
| `npm run test:run` | PASS: 3 Testdateien, 9/9 Tests |
| `npm run build` | PASS: Astro/Cloudflare-Build erfolgreich |
| Mobile Visual-Check 390px | PASS: Cookie-Banner 203px hoch bei 844px Viewport (= 24,1%); kein horizontaler Overflow; Screenshot `/tmp/hsb-cookie-mobile-after.png` |
| Hero-Kontrastklasse | PASS: Hero-Highlight rendert lokal als `rgb(255, 138, 125)` |
| Lighthouse lokal (`/`, `/branchen/molkerei/`, `/referenzen/`) | A11y/Best Practices/SEO jeweils 100; Performance im lokalen Dev-Server 63/67/65 und daher nicht mit Cloudflare-Preview vergleichbar |

**Bewusst zurückgestellt (Stand Codex-Runde):**

- `LanguageSuggest.astro`: Mobile-H1-Überdeckung bleibt der nächste UI-Fix.
- Interne Link-Erweiterungen in Datenmodellen und Leistungs-Bildslots bleiben eigene Content-/Medienphase.
- Sitemap-Aufnahme von `/impressum/` und `/datenschutz/` bleibt SEO-Feinschliff mit niedriger Priorität.
- Korrektur der älteren `referenzen-freigabe.md`-Zahl von 21 auf 22 Kundenstandorte bleibt Dokumentationsnachzug; der aktuelle Datenstand ist in `src/data/clientLocations.ts` eindeutig 22.

---

**Abschlussrunde Claude (2026-06-11, nach User-Freigabe „zum Ende bringen") — Endergebnis je Backlog-Punkt:**

| Punkt | Status | Detail |
|---|---|---|
| Sprachhinweis-Banner überdeckt Mobile-H1 | ✅ **erledigt** | `LanguageSuggest.astro`: `fixed top-[72px]`-Overlay → normaler Dokumentfluss (Banner schiebt Content statt ihn zu verdecken). Visuell verifiziert auf /kontakt/ 390px: H1 „Projektanfrage für Industrieböden" vollständig sichtbar |
| Hero `loading="eager"` + `decoding="async"` | ✅ **erledigt** | `src/pages/index.astro` (srcset/fetchpriority/width/height waren bereits vorhanden) |
| Hero-H1-Kontrast | ✅ erledigt (Codex) | `text-hsb-red-light` (#ff8a7d), bestehende Brand-Klasse |
| Cookie-Banner mobil kompakter (CLS) | ✅ erledigt (Codex) | Layout-only, DSGVO-Mechanik unverändert |
| OG-Image | ✅ **verifiziert, keine Lücke** | `public/brand/og-image.png` existiert (1200×630), liefert HTTP 200, in `SEOHead.astro:30` korrekt absolut referenziert |
| Interne Cross-Links Branchen→Leistungen/Wissen | ✅ **erledigt** | `industries.ts`: Lebensmittel +Entwässerung (Service+Artikel), Molkerei +Säureschutz/+Sanierungs-Artikel, Chemie +Keramik/+PU-Vergleich, Pharma +Keramik/+Sanierungs-Artikel, Backwaren +Entwässerung/+PU-Vergleich. Brauerei-Befund war False Positive (Links vorhanden). Review: PASS (Slugs existieren, sachlich belegt u. a. durch eingebundene Chemie-/Pharma-Keramik-Projektfotos, keine Duplikate) |
| Service↔Service-Linkfeld | ⏸ zurückgestellt | Neues Datenmodell = Over-Engineering für diese Runde (Leitplanke 5), bestätigt |
| Leistungs-Bildslot | ✅ **erledigt** | `leistungen/[slug].astro`: `serviceImages`-Slot 1:1 analog `industryImages`. Befüllt mit den 2 designierten Reserve-Fotos aus referenzen-freigabe.md §3: `saeulen-anschluss-keramik.webp` → industrieboden-saeureschutz, `verlegung-keramik.webp` → keramische-industrieboeden. Beide Fotos vor Einbau visuell auf Fremdlogos geprüft (keine — KLINGER-Regel eingehalten) |
| pharma-hessen Re-Check | ✅ **geprüft, bleibt anonymisiert** | `clientLocations.ts` (22 Einträge): KEIN Pharma-Eintrag (nur Brauerei 5/Chemie 1/Getränke 6/Lebensmittel 6/Molkerei 4); einziger Hessen-Eintrag ist eine Weinkellerei (Getränke). Weiterhin kein eindeutiger Treffer → Status unverändert (Default referenzen-freigabe.md §1) |
| Sitemap/robots final | ✅ **verifiziert** | Build-Output: 32 `<loc>`-URLs inkl. 5 Sprachvarianten, robots.txt valide mit Sitemap-Verweis. Impressum/Datenschutz-Aufnahme bleibt zurückgestellt (Entscheidung Codex-Runde bestätigt) |
| Wissensartikel-Fließtext | ⏸ zurückgestellt | Inhalt kommt aus Gemini-Deep-Research-Auftrag; KEINE generierten Fachzahlen (mistakes.md) |
| Footer-Lokalisierung Sprachseiten | ⏸ zurückgestellt | Größerer i18n-Umbau; ehrlicher EN-Hinweis vorhanden |
| Echte Markenlogos | ⛔ blockiert | Externe Lieferung durch Kunden erforderlich |
| GA4 / SMTP / n8n / juristische Prüfung | ⛔ out of scope | Masterplan Phase 1/4/5, User-Inputs erforderlich |

**Hinweis für parallele Sessions:** Das Haupt-Repo (`projects/hsb-boden`, Branch `main`) hat uncommittete Änderungen einer anderen Session; ein Review-Agent meldete dort mögliche Merge-Konflikt-Marker in `articles.ts`/`content.ts`. Dieser Worktree (`hsb-boden-review`) ist davon NICHT betroffen (grep + Build verifiziert).
