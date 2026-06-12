# Release Candidate Status

Projekt: HSB-Boden / HEXAFLOOR  
Stand: 2026-06-11  
Branch: `claude/hsb-boden-architecture-o2479f`  
HEAD: `a591724`  
PR: #5, Draft, offen, konfliktig  
Produktions-Cutover: nicht freigegeben

## Release Ready

**NEIN.**

Der Branch ist fachlich weit fortgeschritten und enthaelt die erwarteten finalen Website-, Referenz-, Medien-, Sprach- und Outreach-Readiness-Aenderungen. Er ist aber aktuell kein sauberer Release Candidate, weil zwei harte Nachweise fehlen:

1. PR #5 ist gegen `main` merge-konfliktig.
2. Die erreichbare Preview zeigt nicht eindeutig den aktuellen Branch-HEAD `a591724`.

## Offene Blocker

| Blocker | Status | Bedeutung |
| --- | --- | --- |
| Merge-Konflikte gegen `main` | offen | PR kann nicht sauber gemerged werden. |
| Preview/Branch-Mismatch | offen | Sichtbare Preview ist keine verlaessliche Abnahmebasis fuer `a591724`. |
| Branch-Alias 404 | offen | Commit-nahe Preview ist nicht verfuegbar oder nicht korrekt geroutet. |
| PR ist Draft | offen | Formal noch nicht freigabefaehig. |
| Kein aktuelles Post-Conflict-Gate | offen | Nach Konfliktloesung muessen Check, Tests und Build erneut laufen. |
| Kein Produktions-Cutover erlaubt | bewusst gesperrt | hsb-boden.de darf nicht aktiviert oder umgeschaltet werden. |

## Sichtbarer Stand vs. Branch

Die Preview unter `https://hsb-boden-preview.cherinojoel.workers.dev/` ist erreichbar und zeigt eine HSB-Seite. Sie zeigt jedoch nicht eindeutig den aktuellen Branch-Stand.

Erwartete Branch-Marker aus `a591724`, die auf der Preview nicht eindeutig sichtbar waren:

- Hero-Kontrastklasse `text-hsb-red-light`
- LogoCloud mit `Referenzkunden (Auszug)`
- freigegebene Referenzlogos / Klarnamen wie Molkerei Gropper, Peterstaler, Concept Color und Dahlhoff
- neuere Projektbild-Pfade aus `public/media/hsb/projekte/`
- Branch-Alias als eindeutiger Commit-/Branch-Nachweis

Bewertung: Die Preview ist fuer eine Release-Candidate-Freigabe aktuell nicht belastbar.

## Risiken

- Ein Merge ohne manuelle Konfliktloesung kann die finalisierte Website-Arbeit teilweise ueberschreiben.
- Ein Go-Live auf Basis der aktuellen Preview koennte einen aelteren Stand veroeffentlichen.
- Die lokalen ungetrackten Reports `DEPLOYMENT_BLOCKER_REPORT.md` und `WEBSITE_PRODUCTION_CONFIRMATION.md` sollten vor einer finalen Uebergabe einsortiert oder bewusst ignoriert werden, damit keine widerspruechliche Statuslage entsteht.
- Da kein Domain-Cutover freigegeben ist, bleibt jede Produktionsaktivierung gesperrt.

## Go/No-Go Empfehlung

**No-Go fuer Produktion.**

**Go fuer Release-Candidate-Stabilisierung**, aber nur in dieser Reihenfolge:

1. Merge-Konflikte gegen `main` in einem kontrollierten Merge-Prep-Schritt aufloesen.
2. Lokales Gate ausfuehren: `npm run check`, `npm run test:run`, `npm run build`.
3. Nach expliziter Freigabe Preview aktualisieren.
4. Preview gegen Branch-HEAD beziehungsweise Commit-SHA pruefen.
5. Erst danach PR #5 von Draft auf Ready setzen.
6. Domain-Cutover bleibt weiterhin separat gesperrt und braucht eigene Freigabe.

## Naechste Schritte

1. Konfliktdateien fachlich aufloesen:
   - `src/components/layout/Header.astro`
   - `src/components/references/ReferenceMapPreview.astro`
   - `src/components/sections/CTASection.astro`
   - `src/data/articles.ts`
   - `src/layouts/BaseLayout.astro`
   - `src/lib/content.ts`
   - `src/pages/index.astro`
   - `src/pages/wissen/[slug].astro`
   - `src/styles/global.css`
2. Danach lokale Verifikation ausfuehren.
3. Danach Preview gezielt auf `a591724` beziehungsweise den neuen Merge-Prep-Commit bringen.
4. Danach erneuten RC-Status erstellen.

## Abschlussbewertung

Der aktuelle Branch ist ein guter Release-Kandidat inhaltlich, aber kein finaler Release Candidate operativ. Der entscheidende naechste Schritt ist nicht weitere Website-Arbeit, sondern Konfliktloesung plus eindeutiger Preview-Nachweis.
