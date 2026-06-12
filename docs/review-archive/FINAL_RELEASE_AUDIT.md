# Final Release Audit

Projekt: HSB-Boden / HEXAFLOOR  
Rolle: Release Engineer  
Stand: 2026-06-11  
Branch: `claude/hsb-boden-architecture-o2479f`  
HEAD: `a591724233a44d1470ce4814e2d3a7ad486a1bc4`  
PR: #5, Draft, `CONFLICTING`  
Release Ready: **NEIN**

## 1. Pruefgrundlage

Verwendete Quellen:

- GitHub PR #5 ueber `gh pr view`
- lokaler Git-Stand im Worktree `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review`
- Cloudflare OAuth/Wrangler gegen Account `043ec899a435f150995d89f402ed7b12`
- Cloudflare Worker Deployments fuer `hsb-boden-preview` und `hsb-boden`
- HTTP-Pruefung der erreichbaren URLs
- Marker-Vergleich zwischen Branch-HEAD und sichtbarer Preview

Cloudflare-MCP-Status:

- `cloudflare`, `cloudflare-docs`, `cloudflare-bindings`, `cloudflare-builds`, `cloudflare-observability` wurden global registriert.
- OAuth/Login fuer Cloudflare wurde erfolgreich abgeschlossen.
- In dieser laufenden Codex-Sitzung wurden die neu registrierten Build-MCP-Tools nicht als direkte Tool-Namespace nachgeladen. Cloudflare wurde deshalb ueber die eingerichtete OAuth-Session mit Wrangler und HTTP-Pruefungen abgefragt.

Nicht ausgefuehrt:

- keine Website-Aenderungen
- keine Features
- kein Merge
- kein Deployment
- kein DNS
- kein Domain-Cutover

## 2. Branch Status

| Punkt | Status |
| --- | --- |
| Branch | `claude/hsb-boden-architecture-o2479f` |
| HEAD | `a591724233a44d1470ce4814e2d3a7ad486a1bc4` |
| PR | #5 |
| PR-Status | Draft |
| Merge-Status | `CONFLICTING` |
| GitHub/Cloudflare Check | `Workers Builds: hsb-boden` = `SUCCESS` |
| Build-Zeit laut GitHub | 2026-06-11T18:18:51Z |
| Cloudflare Build-Link | `https://dash.cloudflare.com/043ec899a435f150995d89f402ed7b12/workers/services/view/hsb-boden/production/builds/b1e395b7-c916-472f-9e94-b4830c85dde9` |

Bewertung:

Der Branch ist gebaut worden, aber nicht releasefaehig, weil PR #5 weiterhin Draft und merge-konfliktig ist.

## 3. Cloudflare Preview / Deployment Status

### Worker `hsb-boden-preview`

Letztes Deployment laut Cloudflare/Wrangler:

- Deployment ID: `22192345-382b-4f9e-b82e-7f6c5d06a566`
- Version ID: `dacc8a59-2f2e-42dc-acf5-90557be0c34f`
- Erstellt: `2026-06-10T16:50:49.150355Z`
- URL: `https://hsb-boden-preview.cherinojoel.workers.dev/`
- HTTP-Status: `200`

Bewertung:

Dieser Preview-Worker ist oeffentlich erreichbar, aber sein letztes Deployment liegt vor den finalen PR #5-Commits vom 11. Juni. Er kann daher nicht HEAD `a591724` enthalten.

### Worker `hsb-boden`

Letztes Deployment laut Cloudflare/Wrangler:

- Deployment ID: `aef1d78a-0508-43c9-9702-69f936999b0f`
- Version ID: `9120dbfc-ced2-411a-b3da-e7988aae3a9e`
- Erstellt: `2026-06-11T18:27:08.62662Z`
- workers.dev URL `https://hsb-boden.cherinojoel.workers.dev/`: HTTP `404`
- Branch-Alias `https://claude-hsb-boden-architecture-o2479f-hsb-boden.cherinojoel.workers.dev/`: HTTP `404`

Bewertung:

Der Worker `hsb-boden` hat ein aktuelleres Deployment, ist aber ueber workers.dev nicht sichtbar. Da `hsb-boden.de` weiterhin WordPress/Apache ausliefert, kann dieser Worker aktuell nicht als sichtbare Preview fuer HEAD verifiziert werden.

### Produktionsdomain

`https://hsb-boden.de/` liefert weiterhin WordPress:

- HTTP `200`
- Header/HTML enthalten `wp-json` und `wp-content`
- `https://hsb-boden.de/referenzen/` liefert WordPress-404

Bewertung:

Kein DNS-Cutover erfolgt. Produktionsdomain ist nicht Teil der RC-Abnahme.

## 4. Preview gegen HEAD

Gepruefte oeffentliche Preview:

`https://hsb-boden-preview.cherinojoel.workers.dev/`

### Sichtbar

| Marker | Preview sichtbar? | Einordnung |
| --- | --- | --- |
| Referenzkarte | JA | Referenzseite zeigt schematische Karte und Referenzkarten. |
| Language UI | JA, aber nicht RC-Variante | Sichtbar ist `LanguageOffer`/Query-Parameter-Logik aus dem Main-/Altstand, nicht `LanguageSuggest` aus HEAD. |
| Cookie UI | JA, aber nicht RC-Variante | Sichtbar ist React `CookieConsent`, nicht der Astro-`CookieConsent` aus HEAD. |
| Header-Aufhellung / Header-Politur | JA | Preview zeigt den helleren `#171b22`-Header aus Main-/Altstand. |

### Nicht sichtbar / fehlt gegen HEAD `a591724`

| Erwartete Branch-Aenderung | Preview sichtbar? | Befund |
| --- | --- | --- |
| LogoCloud | NEIN | Marker `Referenzkunden (Auszug)` / `Vertrauen durch reale Umsetzung` nicht sichtbar. |
| Klarnamen-Referenzen / Logos | NEIN | `Molkerei Gropper`, `Peterstaler`, `Concept Color`, `Dahlhoff` nicht sichtbar. |
| Erweiterte Projektbilder | NEIN | Preview nutzt auf `/referenzen/` alte `/media/hsb/current/referenzflaeche-*` Assets statt neuer `/media/hsb/projekte/*`-Bilder. |
| ProofMedia-Erweiterung | NICHT ALS HEAD VERIFIZIERBAR | Neue Marker wie `keramik-halle-rinnen.webp`, `chemie-anlage-keramik.webp`, `pharma-halle-keramik.webp` nicht eindeutig im sichtbaren Stand. |
| `LanguageSuggest` | NEIN | Preview nutzt `LanguageOffer.B9djb1kF.js`; Branch-HEAD nutzt `src/components/layout/LanguageSuggest.astro`. |
| interne Crosslinks Wissen | NEIN | Wissensseite rendert alte Platzhaltertexte und kein Modul `Passende Leistungen und Branchen`. |
| Hero-Kontrast | NEIN | Hero-H1 nutzt weiter `text-hsb-red`; Branch-HEAD erwartet `text-hsb-red-light`. |
| Cookie-Banner-Fix aus RC | NICHT ALS HEAD VERIFIZIERBAR | Preview nutzt React `CookieConsent.7Ahwtuw4.js`; Branch-HEAD nutzt Astro-Komponente `CookieConsent.astro` mit kompakten mobilen Klassen. |
| Hero-srcset / eager decoding aus RC | NEIN | Preview-Hero zeigt kein `srcset` / `sizes` / `loading="eager"` aus HEAD. |
| CTA `Werksbegehung anfragen` | NEIN | Preview zeigt weiterhin `Ersteinschätzung anfordern`. |

## 5. Welche Commits sind in der Preview sichtbar?

Eine exakte Commit-SHA ist aus dem ausgelieferten HTML nicht ableitbar, weil kein Commit-Hash in HTML, Assets oder Headern sichtbar ist.

Der sichtbare Preview-Stand ist aber eindeutig **nicht** HEAD `a591724`.

Begruendung:

- `hsb-boden-preview` wurde zuletzt am 10. Juni 2026 um 16:50 UTC deployed.
- HEAD `a591724` wurde am 11. Juni 2026 um 18:17 UTC committed.
- Die Preview enthaelt keine finalen Marker aus `a591724`.
- Die Preview enthaelt auch nicht konsistent den vollstaendigen `origin/main`-Stand `d2d5e90`, weil z. B. Wissensartikel weiterhin alte generische Platzhaltertexte ausgeben.

Wahrscheinliche Einordnung:

Die oeffentliche Preview ist ein aelterer oder manuell erzeugter Zwischenstand. Sie enthaelt Teile der Header-/Language-/Consent-Politur, aber nicht die finalen RC-Branch-Aenderungen.

## 6. Konflikte

GitHub markiert PR #5 als `CONFLICTING`. Die Merge-Simulation bestaetigt 9 Konfliktdateien:

| Datei | Exakte Ursache | Risiko |
| --- | --- | --- |
| `src/components/layout/Header.astro` | `main` nutzt `supportedLanguages` + Query-Parameter-Sprachwahl; HEAD nutzt `Lang`-Props und i18n-Sprachseiten. Beide aendern Header-Farbe und Navigation. | Doppelte oder defekte Sprachlogik; Header-Regression. |
| `src/components/references/ReferenceMapPreview.astro` | `main` poliert Layout/Copy; HEAD erweitert Karte mit `clientLocations` und bundesweiter Projektlogik. | Verlust der Deutschlandkarten-Erweiterung oder falsche Referenzzahlen. |
| `src/components/sections/CTASection.astro` | `main` korrigiert Text/Zeichensetzung; HEAD setzt `Werksbegehung`-CTA. | Uneinheitlicher oder abgeschwaechter Lead-CTA. |
| `src/data/articles.ts` | `main` nutzt voll ausgearbeitete Artikel-Objekte mit `title`/`content`; HEAD ergaenzt Relationsfelder fuer Crosslinks. | Build-/Schemafehler oder Verlust der Fachtexte/Crosslinks. |
| `src/layouts/BaseLayout.astro` | `main` bindet React `LanguageOffer`/`CookieConsent` ein; HEAD bindet Astro `LanguageSuggest`/`CookieConsent`, `lang`, `alternates` ein. | Doppelte Consent-/Sprachsysteme oder verlorene hreflang-Logik. |
| `src/lib/content.ts` | `main` passt Artikelschema auf Objekt-Sections an; HEAD ergaenzt `relatedServices`, `relatedIndustries`, `relatedArticles` und i18n-Landingpages. | Datenmodell bricht zwischen Artikeldatei, Schema und Template. |
| `src/pages/index.astro` | `main` poliert Hero/Layout; HEAD fuegt `LogoCloud`, `homeAlternates`, `text-hsb-red-light`, Hero-srcset und Performance-Attribute ein. | Verlust zentraler RC-Marker und Preview-Nachweisbarkeit. |
| `src/pages/wissen/[slug].astro` | `main` rendert Artikelobjekte; HEAD rendert Related-Content-Module und neuen CTA. | Entweder fehlen Fachtexte oder interne Crosslinks. |
| `src/styles/global.css` | `main` fuegt Design-Tokens und visuelle Politur ein; HEAD korrigiert Kontrast-/Dunkelton- und Bannerwerte. | A11y-Kontrast- oder Mobile-Banner-Regression. |

## 7. Risiken

| Risiko | Schwere | Bewertung |
| --- | --- | --- |
| PR #5 ist konfliktig | hoch | Kein mergefaehiger Release Candidate. |
| PR #5 ist Draft | mittel | Noch nicht formal bereit fuer finale Review. |
| Preview zeigt nicht HEAD | hoch | Keine belastbare Abnahmebasis fuer `a591724`. |
| Aktueller Worker `hsb-boden` ist nicht oeffentlich pruefbar | hoch | Erfolgreicher Build reicht nicht; sichtbarer Stand fehlt. |
| Preview ist Misch-/Altstand | hoch | Sichtbare Website kann falsche Freigabe suggerieren. |
| Produktionsdomain zeigt WordPress | bewusst gesperrt | Kein Cutover; fuer RC korrekt, fuer Go-Live offen. |
| Konflikte betreffen zentrale Architekturdateien | hoch | Automatischer Merge wuerde sehr wahrscheinlich Features verlieren. |

## 8. Fehlende Branch-Aenderungen in der sichtbaren Preview

Folgende Branch-Aenderungen muessen nach Konfliktloesung und Preview-Aktualisierung erneut sichtbar geprueft werden:

1. `LogoCloud.astro` auf Startseite.
2. Freigegebene Klarnamen-/Logo-Referenzen.
3. Erweiterte Deutschlandkarte mit `clientLocations`.
4. Neue Projektbilder unter `/media/hsb/projekte/`.
5. ProofMedia-Erweiterung.
6. `LanguageSuggest.astro` statt React-`LanguageOffer`.
7. Astro-`CookieConsent.astro` mit kompaktem mobilen Layout.
8. `text-hsb-red-light` im Hero-H1.
9. interne Crosslinks auf Wissensseiten.
10. voll ausgearbeitete Wissensartikel plus Related-Module.
11. `Werksbegehung anfragen` als finaler CTA.

## 9. Release Ready

**Release Ready: NEIN.**

Begruendung:

- PR #5 ist Draft.
- PR #5 ist `CONFLICTING`.
- Der sichtbare Preview-Worker `hsb-boden-preview` ist nicht HEAD `a591724`.
- Der aktuelle Worker `hsb-boden` hat zwar ein Deployment vom 11. Juni, ist aber ueber workers.dev nicht sichtbar und ueber `hsb-boden.de` nicht erreichbar, weil die Domain weiter WordPress ausliefert.
- Es gibt keine oeffentlich verifizierbare URL, die den aktuellen Branch-Stand abbildet.

## 10. Empfohlener naechster Schritt

Nicht DNS, nicht Deployment, nicht Feature-Arbeit.

Naechster sicherer Schritt:

1. Konflikte gemaess `MERGE_RESOLUTION_PLAN.md` in einem kontrollierten Merge-Prep-Stand loesen.
2. Lokale Gates ausfuehren:
   - `npm run check`
   - `npm run test:run`
   - `npm run build`
3. Erst danach Preview gezielt aktualisieren.
4. Preview gegen den dann aktuellen HEAD verifizieren.
5. Danach Release Ready neu bewerten.

Bis dahin bleibt der Status:

**NO-GO fuer Produktion.**
