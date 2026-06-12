# Merge Resolution Plan

Projekt: HSB-Boden / HEXAFLOOR  
Stand: 2026-06-11  
Branch: `claude/hsb-boden-architecture-o2479f`  
HEAD: `a591724`  
Basis: `origin/main` (`d2d5e90`)  
Ziel: bestehenden Release Candidate stabilisieren, ohne neue Website-Features, Deployment, DNS oder Cutover.

## Ausgangslage

`BRANCH_DELTA_REPORT.md` weist 9 Merge-Konfliktdateien aus. Eine erneute Merge-Simulation bestaetigt dieselben Dateien.

Der Handoff vom 11. Juni nennt Go-Live-P0-Themen, aber der operative Repo-Stand zeigt weiterhin:

- PR #5 ist Draft.
- PR #5 ist `mergeable: CONFLICTING`.
- Der Arbeitsordner `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` steht auf `main` (`d2d5e90`), nicht auf dem Release-Branch.
- Der Release-Branch liegt im Review-Worktree `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review`.

Folgerung: DNS-/Go-Live-Arbeit darf erst nach Konfliktloesung, lokalem Gate und Preview-Verifikation beginnen.

## Konfliktmatrix

| Konfliktdatei | Konfliktursache | Bevorzugte Version | Begruendung | Risiko |
| --- | --- | --- | --- | --- |
| `src/components/layout/Header.astro` | Beide Seiten haben Header, Header-Farbe und Sprachlogik geaendert. `main` nutzt Query-Parameter-Sprachauswahl ueber `supportedLanguages`; der RC-Branch nutzt echte `lang`-Props, `i18n` und Sprachseiten. | RC-Branch als Basis; aus `main` nur rein visuelle Header-Politur uebernehmen, falls sie keine i18n-Logik ersetzt. | Der RC-Branch enthaelt die neuere Spracharchitektur mit echten Sprachseiten und passt zu `BaseLayout`, `LanguageSuggest` und SEO-Alternates. | Doppelte Sprachsysteme oder verlorene Sprachseiten; defekte Header-Imports, falls `supportedLanguages` und `Lang` vermischt werden. |
| `src/components/references/ReferenceMapPreview.astro` | `main` ueberarbeitet Layout und Copy; der RC-Branch erweitert die Karte mit `clientLocations`, bundesweiter Projektlogik und namentlichen Referenzzahlen. | RC-Branch als funktionale Basis; Layout-Details aus `main` nur selektiv und ohne Entfernen von `clientLocations`. | Die Referenzkarte ist ein zentraler RC-Marker. Ohne `clientLocations` geht der Deutschlandkarten-Ausbau verloren. | Karte zeigt weniger Standorte oder alte Referenzlogik; falsche Trust-Signale, falls Zahlen/Copy zur Datenbasis nicht passen. |
| `src/components/sections/CTASection.astro` | Beide Seiten haben CTA-Text minimal geaendert. `main` korrigiert Zeichensetzung; der RC-Branch setzt staerkeren Werksbegehungs-CTA. | RC-Branch-Text; optionale Zeichensetzung aus `main`, wenn Inhalt gleich bleibt. | Der Werksbegehungs-CTA ist konsistent mit Lead- und Outreach-Positionierung. | Schwaecherer CTA oder uneinheitliche Sprache zwischen Seiten und Formular. |
| `src/data/articles.ts` | `main` wandelt Artikel-Sections von einfachen Strings in Objekte mit `title` und `content`; der RC-Branch ergaenzt `relatedServices` und `relatedIndustries`. | Manuelle Hybrid-Version: `main`-Artikeltexte behalten und RC-Relationen ergaenzen. | Die Handoff-Qualitaet beruht auf voll ausgearbeiteten Wissensartikeln; der RC-Branch bringt die interne Verlinkung dazu. Beides muss erhalten bleiben. | Build-Fehler, wenn `articles.ts`, `src/lib/content.ts` und `src/pages/wissen/[slug].astro` nicht dieselbe Datenform erwarten. |
| `src/layouts/BaseLayout.astro` | `main` fuegt React-Komponenten fuer Consent/LanguageOffer ein; der RC-Branch fuegt Astro-Komponenten `CookieConsent`, `LanguageSuggest`, `lang`, `alternates` und lokalisierte Skip-Labels ein. | RC-Branch als Basis; keine doppelten Consent-/Language-Systeme. | Der RC-Branch ist konsistent mit vorhandenen Astro-Komponenten, Sprachseiten und SEO-Alternates. | Doppeltes Cookie-Banner, doppelte Sprachhinweise, Hydration-Fehler oder verlorene Hreflang-/Alternates-Logik. |
| `src/lib/content.ts` | `main` aendert `articleSchema.sections` auf Objektform; der RC-Branch ergaenzt Relationsfelder und internationale Landing-Pages fuer public page generation. | Manuelle Hybrid-Version: Objektform fuer `sections`, plus `relatedServices`, `relatedIndustries`, `relatedArticles` und Landing-Pages aus RC. | Muss die vollstaendigen Fachartikel aus `main` und die interne Link-/i18n-Logik aus RC gemeinsam validieren. | Schema passt nicht zu Daten; Wissensseiten oder Sitemap/SEO-Listen brechen beim Build. |
| `src/pages/index.astro` | `main` poliert Hero/Layout, nutzt aber weiter `text-hsb-red`; der RC-Branch fuegt `LogoCloud`, `homeAlternates`, Hero-Kontrast `text-hsb-red-light`, Hero-srcset und Performance-Attribute ein. | RC-Branch als Basis; visuelle Layout-Politur aus `main` nur selektiv, ohne RC-Marker zu verlieren. | LogoCloud, Hero-Kontrast und Bild-Performance sind explizite RC-Anforderungen und Preview-Verifikationsmarker. | LogoCloud fehlt, Kontrast-Regression, Preview kann nicht gegen HEAD verifiziert werden. |
| `src/pages/wissen/[slug].astro` | `main` rendert neue Artikelobjekte (`section.title`, `section.content`); der RC-Branch ergaenzt Related-Services/-Industries und CTA-Text. | Manuelle Hybrid-Version: Objekt-Rendering aus `main`, Related-Module und CTA aus RC. | Nur die Kombination erhaelt sowohl die neuen Fachtexte als auch interne Crosslinks. | Laufzeitfehler bei falscher Datenform; Verlust der internen Linkstruktur oder der ausgearbeiteten Artikeltexte. |
| `src/styles/global.css` | `main` fuegt Design-Tokens, Schatten, Radien und typografische Anpassungen ein; der RC-Branch korrigiert Dunkelton/Kontrast auf `#161a20` und passt Header-/Button-Farben an. | RC-Kontrastwerte als Pflicht; visuelle Tokens aus `main` nur uebernehmen, wenn sie keine Kontrast-/Mobile-/Banner-Fixes zurueckdrehen. | Hero-Kontrast und mobiles Banner waren konkrete RC-Fixes. Diese duerfen nicht durch aeltere Farb-/Layoutwerte verworfen werden. | A11y-Kontrast faellt wieder ab; mobile Banner-Fixes oder visuelle Konsistenz gehen verloren. |

## Empfohlene Reihenfolge der Konfliktloesung

1. `src/data/articles.ts`
2. `src/lib/content.ts`
3. `src/pages/wissen/[slug].astro`
4. `src/layouts/BaseLayout.astro`
5. `src/components/layout/Header.astro`
6. `src/styles/global.css`
7. `src/pages/index.astro`
8. `src/components/references/ReferenceMapPreview.astro`
9. `src/components/sections/CTASection.astro`

Begruendung: Erst Datenform und Schema stabilisieren, dann Layout-/Sprachsystem, dann sichtbare Startseiten- und Referenzdarstellung.

## Nicht-Ziele

- Keine neuen Features.
- Keine neue Designrichtung.
- Keine neuen Referenzen, Logos oder Claims.
- Kein Deployment.
- Kein DNS-Cutover.
- Keine SMTP-/n8n-Aktivierung in diesem Schritt.

## Abschlusskriterium fuer diese Phase

Die Konflikte gelten erst dann als stabil geloest, wenn nach dem Merge-Prep folgende Befehle erfolgreich laufen:

1. `npm run check`
2. `npm run test:run`
3. `npm run build`

Danach muss die Preview explizit gegen den dann aktuellen HEAD verifiziert werden.
