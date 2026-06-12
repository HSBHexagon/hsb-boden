# Branch Delta Report

Projekt: HSB-Boden / HEXAFLOOR  
Stand: 2026-06-11  
Branch: `claude/hsb-boden-architecture-o2479f`  
HEAD: `a591724`  
Vergleichsbasis: `origin/main` (`d2d5e90`)  
Merge-Base: `e897ab2`  
PR: #5, Draft, offen, `mergeable: CONFLICTING`

## 1. Umfang des Checks

Dieser Bericht ist ein Release-Candidate-Abgleich zwischen `main` und `claude/hsb-boden-architecture-o2479f`.

Nicht ausgefuehrt:

- kein Merge
- kein Rebase
- kein Deployment
- kein Domain-Cutover
- keine Website-Neuentwicklung
- keine Feature-Erweiterung

## 2. Commits auf dem Release-Branch

Commits auf `claude/hsb-boden-architecture-o2479f`, die nicht in `origin/main` enthalten sind:

| Commit | Inhalt |
| --- | --- |
| `a591724` | Website fuer Outreach-Readiness finalisiert |
| `ab2b5d2` | Mobile Banner, DSGVO-technische Verfeinerung, Env-Platzhalter |
| `7d1f9f8` | Full-Site-Review-Endstand dokumentiert |
| `885f6f0` | Bildslot fuer Leistungsseiten mit freigegebenen Reserve-Projektfotos |
| `92c7a81` | Interne Cross-Links Branchen zu Leistungen/Wissen |
| `263d987` | Hero-Bild Performance: eager loading, async decoding |
| `ef58f62` | Sprachhinweis-Banner im Dokumentfluss statt fixed Overlay |
| `4c6426f` | Kompaktes mobiles Consent-Banner |
| `923db5d` | Visuelle QA und Lighthouse-Befunde dokumentiert |
| `08dbc3e` | Pro-Seite-Findings aus Content-Audit |
| `d79d0ac` | Routenliste und Sitemap-Abgleich |
| `e7fe8cc` | Statusmatrix konsolidiert |
| `0c41e8e` | Darstellung nach Phase 2 dokumentiert |
| `c6ef35e` | Full-Site-Review-Plan |
| `8b19c48` | Master-Handoff fuer Codex |
| `f0fa816` | Phase-2-Gate-Report |
| `8702008` | Interne Verlinkung, OG-Image, Hero-srcset, Positionierung, CTA |
| `901ab3f` | Competitive Gap Report |
| `df1460e` | Master Execution Plan V2 und Phase-0-Statusmatrix |
| `219b050` | Klarnamen-Referenzen, Deutschlandkarte, neue Projektfotos |
| `7ffad2a` | Regenerierte Astro-Typdefinitionen |
| `f49a580` | Dunkelton minimal angehoben, Referenzen-Freigabe-Liste |
| `6852ebf` | Sechs reale Projektfotos optimiert und eingebunden |
| `96f1524` | Mehrsprachigkeit, Sprachvorschlag, DSGVO-Cookie-Banner |

## 3. Relevante Aenderungen

Der Branch enthaelt gegenueber `main` insgesamt 76 geaenderte Dateien mit ca. 3.388 Einfuegungen und 108 Loeschungen.

Wesentliche Bereiche:

- Layout und UX: Header, Footer, BaseLayout, globale Styles, Cookie Consent, Sprachhinweis.
- Internationalisierung: Sprachseiten fuer `en`, `fr`, `nl`, `pl`, `tr` und i18n-Logik.
- SEO und Ausspielung: SEOHead, OG-Image, Sitemap- und Audit-Dokumentation.
- Startseite: Hero-Performance, CTA, LogoCloud, Proof-/Referenzfuehrung.
- Referenzen: erweiterte Referenzdaten, Deutschlandkarte, Kundenlogos nach Freigabelogik.
- Medien: neue optimierte WebP-Projektbilder unter `public/media/hsb/projekte/`.
- Content: Branchen, Leistungen, Wissensartikel, interne Verlinkung.
- Tests/Tooling: Playwright als Abhaengigkeit fuer visuelle Checks.
- Dokumentation: Audit-, Launch-, Superpowers- und Statusdokumente.

## 4. Merge-Konflikte gegen `main`

GitHub markiert PR #5 als konfliktig. Eine lokale Merge-Simulation bestaetigt Konflikte in folgenden Dateien:

| Datei | Konfliktart | Relevanz |
| --- | --- | --- |
| `src/components/layout/Header.astro` | Content-Konflikt | Navigation, Sprache, Header-UX |
| `src/components/references/ReferenceMapPreview.astro` | Content-Konflikt | Referenzkarte / Preview-Darstellung |
| `src/components/sections/CTASection.astro` | Content-Konflikt | Conversion-Fuehrung |
| `src/data/articles.ts` | Content-Konflikt | Wissenscontent / SEO |
| `src/layouts/BaseLayout.astro` | Content-Konflikt | globale Layout-, Script- und Consent-Logik |
| `src/lib/content.ts` | Content-Konflikt | Content-Ausleitung / Validierung |
| `src/pages/index.astro` | Content-Konflikt | Startseite / Hero / LogoCloud |
| `src/pages/wissen/[slug].astro` | Content-Konflikt | Wissensseiten-Template |
| `src/styles/global.css` | Content-Konflikt | Designsystem, Mobile, Banner, Kontrast |

## 5. Preview-Abgleich

Gepruefte Preview:

- `https://hsb-boden-preview.cherinojoel.workers.dev/` liefert HTTP 200.
- Branch-Alias-Varianten fuer den PR-Branch lieferten HTTP 404 und sind dadurch nicht als Nachweis fuer `a591724` verwendbar.

Sichtbar auf der Preview:

- HSB-Astro-Seite ist grundsaetzlich erreichbar.
- Startseite, Referenzen und Leistungsseite sind sichtbar.
- Sprachhinweis beziehungsweise Sprachlogik ist im Markup erkennbar.
- Referenzseite zeigt Karte und Referenzkarten.

Nicht sichtbar beziehungsweise nicht eindeutig auf dem aktuellen Preview-Stand nachweisbar:

- Startseiten-Hero nutzt sichtbar noch `text-hsb-red` statt des Branch-Standes `text-hsb-red-light`.
- `LogoCloud` mit `Referenzkunden (Auszug)` war auf der Preview nicht nachweisbar.
- Neu freigegebene Klarnamen-/Logo-Referenzen wie Molkerei Gropper, Peterstaler, Concept Color und Dahlhoff waren auf `/referenzen/` nicht nachweisbar.
- Neuere Projektbild-Pfade aus `public/media/hsb/projekte/` waren nicht eindeutig sichtbar.
- Der sichtbare Preview-Stand wirkt daher nicht deckungsgleich mit Branch-HEAD `a591724`.

Bewertung: Die Preview ist erreichbar, aber sie beweist aktuell nicht, dass `a591724` live auf der Preview laeuft.

## 6. Risiken

| Risiko | Schwere | Bewertung |
| --- | --- | --- |
| PR #5 ist merge-konfliktig | hoch | Kein sauberer Release Candidate, solange Konflikte gegen `main` bestehen. |
| Preview passt nicht eindeutig zu `a591724` | hoch | Sichtbarer Stand kann nicht als RC-Abnahmebasis verwendet werden. |
| Branch-Alias liefert 404 | mittel | Erschwert eindeutige Zuordnung Preview zu Branch/Commit. |
| Viele zentrale UI-/Content-Dateien konfliktig | hoch | Manuelle Konfliktloesung muss fachlich passieren, nicht mechanisch. |
| Lokale ungetrackte Reports existieren | niedrig bis mittel | `DEPLOYMENT_BLOCKER_REPORT.md` und `WEBSITE_PRODUCTION_CONFIRMATION.md` sind lokal ungetrackt und koennen den Status verunklaren. |

## 7. Merge-Strategie

Kein automatischer Merge.

Empfohlene Strategie:

1. Einen separaten Merge-Prep-Stand aus `claude/hsb-boden-architecture-o2479f` erstellen.
2. `main` in diesen Stand integrieren und Konflikte Datei fuer Datei manuell aufloesen.
3. Bei Website-/UX-Konflikten grundsaetzlich den finalisierten PR-Stand als fachliche Basis verwenden, sofern `main` keine neueren Sicherheits-, Build- oder Rechtsanforderungen enthaelt.
4. Bei Content-/Datenkonflikten (`articles.ts`, `content.ts`, `wissen/[slug].astro`) beide Seiten fachlich vergleichen und Schema-/Link-Erweiterungen aus beiden Staenden erhalten.
5. Bei `BaseLayout.astro` und `global.css` besonders auf Consent-, Sprach-, SEO- und Mobile-Logik achten.
6. Nach Konfliktloesung lokal verifizieren: `npm run check`, `npm run test:run`, `npm run build`.
7. Erst nach gruenem lokalen Gate und expliziter Freigabe eine Preview-Aktualisierung ausloesen.
8. Danach Preview gegen Commit-SHA pruefen und erst dann PR von Draft auf Ready stellen.

## 8. Fazit

Der Branch enthaelt die erwarteten Release-Verbesserungen, ist aber in seinem aktuellen Zustand kein eindeutig produktionsreifer Release Candidate, weil PR #5 gegen `main` konfliktig ist und die erreichbare Preview nicht eindeutig Branch-HEAD `a591724` abbildet.
