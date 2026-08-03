# SEO/GSC/GA4-Gesamtstrategie für HSB Hexagon — Design

Stand: 2026-08-03

## Ausgangslage (verifiziert)

HSB Hexagon ist ein B2B-Fachbetrieb für Industrieböden/Säureschutz. Zielgruppe sind
Entscheider in Produktionsbetrieben (Lebensmittel, Molkerei, Brauerei, Chemie, Pharma,
Backwaren), die aktiv nach einem Fachbetrieb suchen, wenn ein konkretes Problem oder
Bauvorhaben ansteht — kein Privatkundengeschäft.

**Bereits vorhanden (per Code-Prüfung, nicht neu zu bauen):**

- 6 Branchenseiten (`src/data/industries.ts`) mit strukturierten Feldern:
  `searchIntent`, `typicalProblems`, `floorRequirements`, `faqs`, `recommendedSystems`,
  `relatedReferences`, `relatedArticles` — bereits deutlich fundierter als bei den
  recherchierten Konkurrenten (Sinnofloor, KORODUR, Kuhn Industrieboden).
- 5 Wissensartikel (`src/data/articles.ts`), 3 Standortseiten (Bayern, Hamburg, NRW).
- Schema.org-Bausteine (`src/lib/schema.ts`): Organization, LocalBusiness, FAQ,
  Service, Breadcrumb, Article.
- GA4 mit Consent-Gate bereits live (`src/lib/analytics.ts`), Cloudflare Web Analytics
  ergänzt (PR #162).
- Seriöse Backlink-Strategie-Doku (`docs/seo/backlink-strategie.md`): B2B-Verzeichnisse
  (Wer liefert was, Europages, IHK), explizit keine gekauften Links/Linkspam.
- **E-E-A-T-Infrastruktur bereits vorbereitet, aber ungefüllt**: `src/data/trustContent.ts`
  (`teamProfileDrafts`, `caseStudyDrafts`) sind bewusst leere Arrays mit dem Kommentar
  "Intentionally empty until real people, evidence and publication consents are supplied."
  `src/lib/trust.ts` enthält vollständige Zod-Schemas inkl. `evidenceRef`-Pflichtfeldern
  und einem `publicationStatus`-Gate (`draft`/`verified`/`approved`). Es fehlt kein Code,
  es fehlen echte, freigegebene Personendaten.
- Fachliche Tiefe auf bestehenden Seiten übertrifft die recherchierte Konkurrenz:
  DIN EN 14411, DGUV, WHG, Rutschhemmklassen bis R13 V6, CIP-Reinigung sind bereits
  im Content — aber teils nicht in Meta-Title/Description sichtbar für Google.

**Reale Lücken (per Recherche, nicht Vermutung):**

1. Kein Autor-/Expertise-Byline auf Wissensartikeln, obwohl "jahrzehntelange Erfahrung"
   behauptet wird — die vorbereitete `trustContent.ts`-Struktur ist ungefüllt.
2. `HACCP` als meistgesuchter Compliance-Begriff der Lebensmittelbranche taucht in
   `typicalProblems`/FAQ auf, aber nicht durchgängig in Meta-Title/H1 der Branchenseite.
3. GA4 `generate_lead`-Event ist laut eigener Doku (`GA4_GTM_GSC_MAX_READINESS.md`,
   Stand 15.07., seither vermutlich durch Deploys überholt) nur lokal, nicht in
   DebugView verifiziert — Statusbehauptung ungeprüft.
4. Content-Cluster-Tiefe: aktuelle Best Practice 2026 (recherchiert) sagt, eine
   Pillar-Page + ein Dutzend unterstützende Artikel schlägt Einzelseiten. HSB hat die
   Pillar-Pages (6 Branchenseiten), es fehlen unterstützende Artikel zu konkreten,
   von mir recherchierten Fachbegriffen (Hohlkehlen-/Sockelausbildung, R12/R13-Klassen
   im Detail, WHG-Abdichtung als Einzelthema).
5. Nur 3 Standortseiten trotz bundesweiter Referenzprojekte (`src/data/references.ts`
   zeigt Standorte in Sachsen-Anhalt, Bayern, weitere).

## Wichtige Nuance (aus Recherche)

**HACCP ist kein Bodenzertifikat**, sondern ein verpflichtender Prozessstandard für
Lebensmittelbetriebe (EU-Basishygiene-VO). Es gibt keine "HACCP-Zertifizierung für
Böden" — korrekt ist die Formulierung "Böden, die HACCP-Anforderungen erfüllen"
(genau wie es aktuell in `industries.ts` steht). Diese Unterscheidung ist beim
Content-Ausbau strikt beizubehalten — jede Formulierung, die "HACCP-zertifiziert"
suggeriert, wäre eine unbelegte Aussage und verstößt gegen die Projekt-Nicht-Verhandelbaren
(keine unbelegten Zertifizierungs-Claims).

## Nicht in diesem Durchgang

- **E-E-A-T-Personendaten selbst beschaffen** — das Repo darf keine Namen/Fotos/Bios
  erfinden. Owner muss echte Team-Mitglieder-Daten + Publikations-Einwilligung liefern,
  bevor `teamProfileDrafts` befüllt wird.
- **GA4 DebugView-Verifikation, Key-Event-Markierung, GSC-Property-Zugriff** — das sind
  Owner-Gates in externen Google-Konten, nicht im Repo automatisierbar (bereits in
  `blocked_followups` als Google-Workspace-Owner-Reauth vermerkt).
- **Neue Standortseiten ohne belegte Referenzprojekte** — nur Standorte, für die
  `references.ts` bereits ein echtes Projekt zeigt.

## Design — drei Blöcke

### Block 1 — Technische Korrektheit & Meta-Daten (P0, kein Owner-Gate nötig)

1. Meta-Title/Description-Audit aller 6 Branchenseiten + 5 Wissensartikel:
   sicherstellen, dass Fachbegriffe (HACCP, WHG, R12/R13, IFS/BRC) dort auftauchen,
   wo sie im Content bereits belegt sind — keine neuen Behauptungen, nur Sichtbarkeit
   bestehender, korrekter Fakten erhöhen.
2. `buildArticleJsonLd()` um ein optionales `author`-Feld erweitern (Organization-Typ:
   "HSB Hexagon Säurebau GmbH", nicht Person — da keine Einzelperson-Daten vorliegen).
   Das ist ein zulässiger Zwischenschritt ohne Owner-Gate: Organisation als Autor ist
   in Schema.org valide und heute schon durch `buildOrganizationJsonLd()` belegt.
3. GSC-Sitemap-Check vorbereiten: Skript/Checkliste, die alle Pfade aus
   `sitemap.xml.ts` gegen die tatsächlich gebauten `dist/`-Seiten abgleicht (rein
   technischer Check, kein GSC-Zugriff nötig für diesen Teil).
4. Dokumentierte, klare Owner-Checkliste für die drei blockierten Punkte (DebugView,
   Key Event, GSC-Property) — bestehende Doku aktualisieren, Stand korrigieren.

### Block 2 — Content-Cluster-Erweiterung (größter Hebel)

Drei neue Wissensartikel, die bestehende Branchenseiten stützen (Cluster-Prinzip),
mit den recherchierten, tatsächlich gesuchten Fachbegriffen:

1. **"Rutschhemmklassen R9 bis R13 für Industrieböden — welche Klasse für welchen
   Bereich"** (verlinkt: Lebensmittelindustrie, Molkerei, Brauerei) — R12/R13 V4/V6
   sind ein konkreter, wiederkehrender Fachbegriff aus der Recherche.
2. **"Hohlkehle und Sockelausbildung im Industrieboden — Warum Detailanschlüsse
   über die Standzeit entscheiden"** (verlinkt: alle Branchen mit Nassbereich) —
   Hohlkehlen/Sockel wurden in der Recherche als kritischer, oft unterschätzter
   Schwachpunkt genannt.
3. **"WHG-Abdichtung für Industrieböden — Wann ist sie Pflicht"** (verlinkt: Chemie,
   Pharma, Lebensmittelindustrie) — WHG ist bereits im Content, aber kein eigener
   Artikel; eigenständiges Thema mit rechtlichem Anlass zur Suche.

Jeder Artikel verlinkt zurück auf mindestens zwei Branchenseiten (`relatedArticles`)
und nutzt `buildArticleJsonLd()` + `buildBreadcrumbJsonLd()` wie die bestehenden
5 Artikel. Kein neues Muster, reine Anwendung des vorhandenen.

### Block 3 — Konversions- und Local-Absicherung (teils Owner-Gate)

1. GA4-Konversions-Checkliste als eigenes, kurzes Dokument: konkrete Schritte für
   Owner, um `generate_lead` in DebugView zu verifizieren und als Key Event zu
   markieren (kein Code, reine Anleitung — vorhandene Doku ist dafür Grundlage,
   wird nur aktualisiert statt neu geschrieben).
2. Standortseiten-Kandidaten identifizieren: welche Regionen haben in
   `references.ts` echte Projekte, aber noch keine Standortseite (Bayern/Hamburg/NRW
   existieren bereits — Sachsen-Anhalt aus Südzucker-Referenz ist ein Kandidat).
   Nur als Vorschlagsliste, keine automatische Seiten-Erstellung ohne Bestätigung,
   welche Region tatsächlich priorisiert werden soll.

## Testing/Verifikation

- `npm run check`, `npm run test:run`, `npm run build` nach jeder Code-Änderung
  (Projekt-Standard, siehe `CLAUDE.md`).
- Neue Artikel gegen `references.ts` und `industries.ts` prüfen: keine neuen
  Kundennamen/Zertifikate ohne Beleg (siehe heutiger CodeRabbit-Fund zu
  "Meggle"/"Biovegan" als Warnung, wie so ein Fehler entsteht).
- Meta-Title-Änderungen: Duplicate-Content-Check (jede Seite einzigartiger Title).

## Reihenfolge

Block 1 zuerst (kein Risiko, keine Owner-Abhängigkeit), Block 2 danach (größter
Content-Hebel, direkt startbar), Block 3 zuletzt (enthält Owner-Gates, die parallel
angestoßen werden können, aber nicht den Implementierungsplan blockieren).
