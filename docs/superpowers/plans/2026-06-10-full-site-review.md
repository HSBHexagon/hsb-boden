# Vollständiger Site-Review & Optimierungsplan (HSB Hexagon Säurebau, Preview)

## Kontext

Die Website (`hsb-boden`, Astro 5, Cloudflare Workers, Branch `claude/hsb-boden-architecture-o2479f`,
PR #5 draft) befindet sich in der finalen Entwurfsphase auf der Preview-Umgebung
(`hsb-boden-preview.cherinojoel.workers.dev` bzw. der Branch-Preview-URL). Der Nutzer will,
bevor weiterer Go-Live-Voraussetzungen (GA4, SMTP, n8n, rechtliche Prüfung – alle außerhalb
dieses Plans, siehe `docs/superpowers/plans/2026-06-10-hexafloor-abgleich.md`) angegangen
werden, **einmal die gesamte Webseite vollständig durchgehen**: jede Seite gegen die
bestehenden Aufgaben-/Checklisten-Dokumente abgleichen, alle bisher vorgeschlagenen
Optimierungen (siehe letzte Antwort: Hero-Performance, srcset, OG-Image, interne
Verlinkung, Leistungs-Bildslot, Sitemap/robots, Lighthouse, Logos, pharma-hessen-Abgleich)
**verifizieren und – soweit sinnvoll und risikofrei – umsetzen**. Ergebnis soll ein
„Meisterwerk"-Niveau in Design und Text sein, ohne gegen `AGENTS.md` oder die Standing
Constraints (PR #2 bleibt unmerged, kein Go-Live, keine erfundenen Claims/Logos) zu
verstoßen.

Dieser Plan ist als **selbstständig abarbeitbare Checkliste** für eine Folge-Session
formuliert (kein Rückfragen-Bedarf, alle Entscheidungen sind bereits getroffen oder
unten als Default festgelegt).

## Phase A — Inventar & Soll/Ist-Abgleich (Read-only)

1. Sitemap/Routenliste erzeugen: `src/pages/sitemap.xml.ts` Logik lesen bzw.
   `getStaticPaths()` aller `[slug].astro`-Seiten auswerten → vollständige URL-Liste
   (DE + Sprachvarianten `/en/ /fr/ /nl/ /pl/ /tr/`, Branchen, Leistungen, Wissen,
   Referenzen, Karriere, Kontakt, Impressum, Datenschutz).
2. Bestehende Status-/Planungsdokumente einlesen und zu einer aktuellen
   **Statusmatrix** konsolidieren (eine Tabelle: Bereich → Status → offene Punkte):
   - `docs/launch/checklist.md`
   - `docs/launch/referenzen-freigabe.md`
   - `docs/audit/current-state.md`
   - `docs/superpowers/plans/2026-06-06-hsb-go-live.md`
   - `docs/superpowers/plans/2026-06-07-hsb-lead-pipeline.md`
   - `docs/superpowers/plans/2026-06-07-hsb-masterplan-golive.md`
   - `docs/superpowers/plans/2026-06-10-hexafloor-abgleich.md`
3. Für jede Seite aus Schritt 1 prüfen (per `general-purpose`/`Explore`-Agent,
   parallelisiert nach Bereich: Branchen / Leistungen / Wissen / Sonstige):
   - H1 vorhanden & einzigartig, `seoTitle`/`description` vorhanden (Zod-Schema in
     `src/lib/content.ts` erzwingt Mindestlängen – stichprobenartig auf Sinnhaftigkeit
     statt nur Länge prüfen)
   - Bilder: `alt`-Text vorhanden, beschreibend, kein Fremdlogo
   - Interne Links: Cross-Links Branche↔Leistung↔Wissen vorhanden oder fehlend
   - Sprachvarianten (`/en/` etc.): Platzhalter-Qualität vs. vollwertiger Content
     prüfen, hreflang-Konsistenz
4. Output: `docs/audit/2026-06-10-full-review-status.md` (neue Datei) mit
   Statusmatrix + Pro-Seite-Findings-Tabelle (Seite | Befund | Schweregrad |
   Vorschlag).

## Phase B — Visuelle/Design-QA im Browser

Nutzt die `run`-Skill-Patterns (Playwright/`chromium-cli` gegen die Branch-Preview-URL,
da kein lokaler Dev-Server nötig ist):

1. Branch-Preview-URL ermitteln (aus dem letzten Cloudflare-Webhook-Kommentar des PR
   oder erneut über `mcp__github__pull_request_read` / PR-Kommentare).
2. Für eine repräsentative Auswahl an Seiten (Startseite, je 1 Branchen-/Leistungs-/
   Wissen-Seite, `/referenzen/`, `/kontakt/`, eine Sprachvariante) Screenshots bei
   Desktop- (1440px) und Mobile-Breite (390px) erstellen.
3. Screenshots visuell prüfen auf: Layoutbrüche, abgeschnittene Bilder/Texte,
   Kontrast/Lesbarkeit, Konsistenz von Abständen/Typografie zwischen Seitentypen,
   korrekte Darstellung der neuen Referenzkarte (21 Kundenstandorte) und der neuen
   Foto-Galerie auf `/referenzen/`.
4. Lighthouse (über Chrome DevTools/Playwright oder `npx lighthouse <url>`) für
   Startseite + 1 Branchenseite + `/referenzen/`: Performance/SEO/Accessibility/
   Best-Practices-Scores erfassen.
5. Befunde in dieselbe Audit-Datei (`docs/audit/2026-06-10-full-review-status.md`,
   Abschnitt „Visuelle QA") eintragen.

## Phase C — Optimierungsbacklog verifizieren & priorisieren

Aus der letzten Antwort übernommene Vorschläge + neue Findings aus A/B in einer
Tabelle zusammenführen, je Punkt bewerten:

| Kandidat | Machbarkeit prüfen anhand | Einordnung |
|---|---|---|
| Hero-Bild `loading="eager"`/`fetchpriority="high"` + `srcset` | `src/components/sections/HeroSection.astro` (oder Äquivalent), aktuelle `<img>`-Nutzung | Quick Win |
| OG-Image aktualisieren | `src/lib/seo.ts` / `SEOHead.astro`, vorhandene OG-Asset-Pfade | Quick Win |
| Interne Verlinkung Branchen↔Leistungen↔Wissen | `src/data/{industries,services,articles}.ts` – vorhandene `relatedServices`/`relatedReferences`-Felder erweitern bzw. im Fließtext verlinken | Quick Win |
| Leistungs-Bildslot (analog `industryImages` in `branchen/[slug].astro`) | Nur umsetzen, wenn **neue, einzigartige** Fotos verfügbar sind (siehe Foto-Restbestand-Hinweis aus letzter Antwort) – sonst zurückstellen | Bedingt |
| Sitemap/robots Re-Check nach Bild-/Seitenänderungen | `src/pages/sitemap.xml.ts`, `src/pages/robots.txt.ts` | Quick Win (Verifikation) |
| `srcset`/responsive Breiten für die 6 neuen WebP-Bilder | Bildgrößen in `public/media/hsb/projekte/` ggf. zusätzliche Breiten via `sharp` erzeugen | Mittel |
| Echte Markenlogos statt Wordmark-SVGs | **Blockiert** – externe Lieferung durch Kunde erforderlich, nicht automatisierbar | Zurückstellen |
| `pharma-hessen` erneut gegen Kundenliste abgleichen | `src/data/clientLocations.ts` / `Referenzprojekte 2025`-Liste erneut sichten | Quick Win (Recherche) |
| GA4/SMTP/n8n/rechtliche Prüfung | Außerhalb Repo-Scope, **nicht Teil dieses Plans** | Out of scope |

Für jeden „Quick Win"/„Mittel"-Punkt: konkrete Datei(en) + minimal-invasive Änderung
festlegen, bevor implementiert wird (kein Over-Engineering, bestehende Patterns
wiederverwenden).

## Phase D — Umsetzung (nur verifizierte, risikofreie Punkte)

Reihenfolge, jede mit anschließendem Gate `npm run check && npm run test:run &&
npm run build`:

1. Hero-Performance (eager/fetchpriority, ggf. `srcset`) auf Startseite.
2. OG-Image prüfen/aktualisieren (falls Lücke gefunden).
3. Interne Cross-Links zwischen Branchen-, Leistungs- und Wissen-Seiten ergänzen
   (im Fließtext, nicht als neue Komponenten – bestehende Link-Patterns nutzen).
4. `pharma-hessen` gegen die interne Kundenliste abgleichen; falls Treffer:
   gleiches Vorgehen wie bei den 4 bereits freigegebenen Referenzen (siehe
   `referenzen-freigabe.md` §0) – sonst Status unverändert lassen.
5. Falls in Phase A neue, bislang ungenutzte und logo-freie Fotos identifiziert
   wurden: Leistungs-Bildslot-Komponente (analog Branchen-Pattern) bauen und
   befüllen.
6. Sitemap/robots final verifizieren (Build-Output stichprobenartig prüfen).
7. Vor jedem Content-/Text-Commit: `seo-content-reviewer`-Agent laufen lassen
   (PASS erforderlich, sonst nachbessern wie in dieser Session bei den 4
   Referenztexten).

## Phase E — Abschluss & Reporting

1. Vollständiges Gate (`check` 0/0/0, `test:run` alle grün, `build` erfolgreich).
2. Geänderte Seiten erneut per Screenshot gegenprüfen (Phase B wiederholen für
   geänderte Seiten).
3. `docs/audit/2026-06-10-full-review-status.md` mit Endergebnis aktualisieren
   (erledigt/zurückgestellt/blockiert je Punkt).
4. Commit + Push auf `claude/hsb-boden-architecture-o2479f` (PR #5 aktualisiert
   sich automatisch); Cloudflare-Deploy-Webhook abwarten und Branch-Preview-URL
   stichprobenartig erneut prüfen.
5. Im Abschlussbericht an den Nutzer: Tabelle „erledigt / zurückgestellt (Grund) /
   blockiert (Grund, z. B. fehlende Logo-Lieferung, GA4/SMTP/n8n/rechtlich)".

## Leitplanken (gelten für die gesamte Ausführung)

- PR #2 bleibt unmerged; keine Aktion, die `hsb-boden.de` produktiv übernimmt.
- Keine erfundenen Zahlen/Statistiken/Claims; keine neuen Kundennamen/Logos ohne
  dieselbe Freigabelogik wie in `referenzen-freigabe.md` §0.
- Keine Fremd-/Maschinenlogos auf neuen Fotos (KLINGER-Regel).
- GA4, SMTP/Formularversand, n8n, juristische Prüfung bleiben außerhalb dieses
  Plans (siehe Masterplan) – nicht anfassen, nicht „mit erledigen".
- Nur bestehende Patterns/Komponenten wiederverwenden (kein neues
  Abstraktions-Layer für einmalige Anpassungen).
