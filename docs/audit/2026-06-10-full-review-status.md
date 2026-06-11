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

## 3. Pro-Seite-Findings (Task 3)

| Seite | Befund | Schweregrad | Vorschlag |
|---|---|---|---|

_(wird in Task 3 befüllt)_

## 4. Visuelle QA (Task 4)

_(wird in Task 4 befüllt)_

## 5. Optimierungsbacklog (Task 5)

_(wird in Task 5 befüllt)_

## 6. Endergebnis (Task 12)

_(wird in Task 12 befüllt)_
