# Release Path

Projekt: HSB-Boden / HEXAFLOOR  
Stand: 2026-06-11  
Aktueller Status: Release Ready = NEIN  
Grund: PR #5 ist Draft, konfliktig und die Preview ist nicht eindeutig gegen HEAD verifiziert.

## Grundsatz

Dieser Pfad beschreibt die Reihenfolge zur Stabilisierung des bestehenden Release Candidates.

In diesem Dokument wird nichts ausgefuehrt:

- kein Merge
- kein Deployment
- kein DNS
- kein Domain-Cutover
- keine SMTP-Aktivierung
- keine n8n-Aktivierung

## Schritt 1: Konflikte loesen

Konfliktdateien:

1. `src/components/layout/Header.astro`
2. `src/components/references/ReferenceMapPreview.astro`
3. `src/components/sections/CTASection.astro`
4. `src/data/articles.ts`
5. `src/layouts/BaseLayout.astro`
6. `src/lib/content.ts`
7. `src/pages/index.astro`
8. `src/pages/wissen/[slug].astro`
9. `src/styles/global.css`

Arbeitsregel:

- In einem separaten Merge-Prep-Stand arbeiten.
- RC-Branch als fachliche Basis verwenden.
- `main`-Aenderungen nur selektiv uebernehmen, wenn sie keine RC-Anforderungen rueckgaengig machen.
- Datenform fuer Wissensartikel konsistent ueber `articles.ts`, `content.ts` und `wissen/[slug].astro` halten.

## Schritt 2: `npm run check`

Ziel:

- Astro-/TypeScript-Check ohne Fehler.
- Besonders pruefen: i18n-Props, BaseLayout-Props, Artikel-Schema, Related-Content-Felder.

Erwartung:

- Exit Code 0.

## Schritt 3: `npm run test:run`

Ziel:

- Bestehende Tests bestaetigen, dass Content-Schema, SEO-Grundlagen, Referenzlogik und Formularvalidierung weiter funktionieren.

Erwartung:

- Exit Code 0.
- Keine fehlgeschlagenen Tests.

## Schritt 4: `npm run build`

Ziel:

- Produktionsbuild lokal erstellen.
- Sicherstellen, dass alle generierten Seiten, Sprachseiten, Wissensartikel, Referenzseiten und Assets zusammenpassen.

Erwartung:

- Exit Code 0.
- Keine defekten Imports.
- Keine Schema- oder Routingfehler.

## Schritt 5: Preview aktualisieren

Status:

- Nicht in dieser Phase ausfuehren.
- Erst nach erfolgreichem lokalen Gate und expliziter Freigabe.

Ziel:

- Preview muss den nach Konfliktloesung aktuellen HEAD abbilden.
- Branch-/Commit-Zuordnung muss eindeutig sein.

## Schritt 6: Preview gegen HEAD `a591724` verifizieren

Hinweis:

- Falls durch Konfliktloesung ein neuer Commit entsteht, muss gegen diesen neuen HEAD verifiziert werden, nicht mehr gegen `a591724`.

Zu pruefende Marker:

- LogoCloud sichtbar.
- Referenzkarte mit erweitertem Standort-/Kundenmodell sichtbar.
- Zusätzliche Projektbilder sichtbar.
- ProofMedia-Erweiterung sichtbar.
- LanguageSuggest vorhanden.
- Interne Crosslinks auf Wissensseiten vorhanden.
- Hero-Kontrast nutzt `text-hsb-red-light` beziehungsweise die finale kontraststarke Klasse.
- Cookie-Banner-Fix mobil sichtbar kompakt.

Erwartung:

- Preview zeigt denselben Stand wie der verifizierte Branch-HEAD.

## Schritt 7: Release Ready erneut bewerten

Bewertungskriterien:

- PR #5 nicht mehr konfliktig.
- PR nicht mehr Draft oder bewusst bereit fuer finale Review.
- Lokales Gate gruen: `check`, `test:run`, `build`.
- Preview eindeutig auf aktuellem HEAD.
- Keine neuen Claims, Logos, Referenzen oder Standortdaten ohne Freigabe.
- Produktions-Cutover weiterhin separat freigegeben.

Moegliche Entscheidung:

- `Release Ready: JA` nur, wenn alle Kriterien erfuellt sind.
- `Release Ready: NEIN`, wenn Merge, Build, Preview oder Freigabelogik offen bleibt.

## Go-Live-Abgrenzung

DNS-Cutover, SMTP und n8n sind echte Go-Live-P0-Themen. Sie duerfen aber erst nach stabilisiertem Release Candidate angefasst werden.

Aktuelle Empfehlung:

1. Erst RC-Konflikte loesen.
2. Dann lokale Gates ausfuehren.
3. Dann Preview gegen HEAD verifizieren.
4. Danach erst DNS/SMTP/n8n als separate Go-Live-Phase starten.
