# Content-Cluster-Erweiterung & Standortseiten-Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zwei neue Wissensartikel (Lebensmittelindustrie: IFS/BRC-Audit, Chemieindustrie: ESD-Ableitfähigkeit) ergänzen den bestehenden Content-Cluster, zwei neue Standortseiten (Rheinland-Pfalz, Baden-Württemberg) decken Regionen mit belegten Referenzprojekten ab, und ein bestehender Sitemap-Lücken-Bug (alle drei existierenden `/standorte/*`-Seiten fehlen in der Sitemap) wird behoben.

**Architecture:** Neue Artikel folgen dem bestehenden Muster in `src/data/articles.ts` (Zod-validiert über `articleSchema`, gerendert über `src/pages/wissen/[slug].astro`). Neue Standortseiten folgen dem bestehenden statischen Astro-Seiten-Muster (`src/pages/standorte/<region>/index.astro`, kein Content-Collection-Eintrag — diese Seiten sind bewusst nicht datengetrieben wie Artikel/Industries). Der Sitemap-Fix ergänzt `getAllPublicPages()` in `src/lib/content.ts` um die vier `/standorte/*`-Pfade (3 bestehende + 1 neu, da Baden-Württemberg parallel zu diesem Plan entsteht — Rheinland-Pfalz kommt als zweite neue Seite dazu, macht 5 insgesamt nach diesem Plan).

**Tech Stack:** Astro (statische Seiten), Zod (Content-Validierung), Vitest (Tests).

## Global Constraints

- Keine unbelegten Zertifizierungs-Claims (z. B. "HACCP-zertifiziert" für den Boden selbst — HACCP ist ein Prozess-, kein Bodenzertifikat; siehe `docs/superpowers/specs/2026-08-03-seo-ga4-gsc-strategie-design.md`).
- Keine Kundennamen/Logos ohne dokumentierte Freigabe (`AGENTS.md` Non-Negotiables).
- Jeder neue `seoTitle` muss ≤ 60 Zeichen sein (SERP-Darstellungslimit, geprüft in `tests/content-meta.test.ts`) und global eindeutig.
- Jeder neue Artikel-Slug muss eindeutig sein und darf keine bestehenden Themen aus `src/data/articles.ts` duplizieren (siehe Bestand unten).
- `.astro/data-store.json` nie committen. Kein `git add .` — immer exakte Pfade stagen.
- Vor Completion-Claim: `npm run test:run`, `npm run check`, `npm run build` müssen grün sein (Deploy Gate aus `CLAUDE.md`).

**Bestehende Artikel-Slugs (nicht duplizieren):** `pu-beton-oder-keramischer-industrieboden`, `warum-industrieboeden-in-molkereien-versagen`, `saeurefeste-fliesen-industrieboden`, `entwaesserung-gefaelle-produktionsbereiche`, `sanierung-ohne-produktionsstillstand`, `rutschhemmklassen-r9-bis-r13-industrieboden`, `hohlkehle-sockelausbildung-industrieboden`, `whg-abdichtung-industrieboden-pflicht`.

**Bestehende Standortseiten:** `standorte/hamburg` (Nord: Hamburg, Bremen, Schleswig-Holstein), `standorte/bayern` (München, Nürnberg, Augsburg, Regensburg), `standorte/nrw`.

**Regionsverteilung in `src/data/clientLocations.ts` (Beleg für Standortseiten-Auswahl):** NRW 8, Rheinland-Pfalz 4, Bayern 3, Thüringen 2, Niedersachsen 2, Baden-Württemberg 2, Schleswig-Holstein 1, Brandenburg 1. NRW/Bayern/Nord sind bereits abgedeckt. Rheinland-Pfalz (4 Kundenstandorte, davon `biovegan-bonefeld` als benannte Referenz in `src/data/references.ts`) und Baden-Württemberg (2 Kundenstandorte, davon `mineralbrunnen-schwarzwald`/Peterstaler als benannte Referenz) sind die stärksten unbedienten Regionen.

---

### Task 1: Sitemap-Lücke für `/standorte/*`-Seiten schließen

**Files:**
- Modify: `src/lib/content.ts:88-181` (Funktion `getAllPublicPages`)
- Test: `tests/sitemap-standorte.test.ts` (neu)

**Interfaces:**
- Konsumiert: keine neuen Abhängigkeiten, nur bestehende Struktur von `getAllPublicPages()`.
- Produziert: `getAllPublicPages()` liefert ab dieser Task zusätzlich Einträge mit `canonicalPath` `/standorte/hamburg/`, `/standorte/bayern/`, `/standorte/nrw/`. Task 3 und Task 4 (neue Standortseiten) ergänzen hier jeweils einen weiteren Eintrag.

Aktuell fehlen alle drei bestehenden `/standorte/*`-Seiten in `getAllPublicPages()` (verifiziert per `grep -n "canonicalPath\|standorte" src/lib/content.ts` — kein Treffer für `standorte`). Das bedeutet: `dist/sitemap.xml` listet diese Seiten nicht, obwohl sie gebaut und live sind. Das ist derselbe Fehlertyp, den `scripts/check-sitemap-consistency.mjs` für andere Seiten bereits verhindert — dieses Skript prüft aber nur die Gegenrichtung (Sitemap-Einträge → existierende Datei), nicht ob alle existierenden Seiten in der Sitemap stehen. Diese Task behebt die Lücke direkt in der Datenquelle.

- [ ] **Step 1: Write the failing test**

```typescript
// tests/sitemap-standorte.test.ts
import { describe, expect, it } from "vitest";
import { getAllPublicPages } from "../src/lib/content";

describe("getAllPublicPages: Standortseiten", () => {
  it("includes all existing /standorte/* location pages", () => {
    const pages = getAllPublicPages();
    const paths = pages.map((p) => p.canonicalPath);

    expect(paths).toContain("/standorte/hamburg/");
    expect(paths).toContain("/standorte/bayern/");
    expect(paths).toContain("/standorte/nrw/");
  });

  it("every standorte entry has a non-empty seoTitle and description", () => {
    const pages = getAllPublicPages();
    const standortePages = pages.filter((p) =>
      p.canonicalPath.startsWith("/standorte/"),
    );

    expect(standortePages.length).toBeGreaterThanOrEqual(3);
    for (const page of standortePages) {
      expect(page.seoTitle.length).toBeGreaterThan(10);
      expect(page.description.length).toBeGreaterThan(20);
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/sitemap-standorte.test.ts`
Expected: FAIL — `paths` does not contain `/standorte/hamburg/` (array has no such element).

- [ ] **Step 3: Add Standorte entries to `getAllPublicPages()`**

In `src/lib/content.ts`, add a new array of static Standorte metadata and splice it into the return array of `getAllPublicPages()`. Insert right before the closing `];` of the returned array (after the `Object.entries(landing)` spread, so around line 179):

```typescript
    ...Object.entries(landing).map(([lang, content]) => ({
      h1: content.hero.h1,
      seoTitle: content.meta.seoTitle,
      description: content.meta.description,
      canonicalPath: `/${lang}/`,
    })),
    {
      h1: "Industrieboden-Spezialist in Norddeutschland",
      seoTitle: "Industrieboden Hamburg | Keramische Böden & Säureschutz Nord",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Hamburg, Schleswig-Holstein und Norddeutschland.",
      canonicalPath: "/standorte/hamburg/",
    },
    {
      h1: "Industrieboden-Spezialist in Bayern",
      seoTitle: "Industrieboden Bayern | Keramische Böden & Säureschutz München",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Bayern. Projekte in München, Nürnberg, Augsburg, Regensburg und ganz Bayern.",
      canonicalPath: "/standorte/bayern/",
    },
    {
      h1: "Industrieboden-Spezialist in Nordrhein-Westfalen",
      seoTitle: "Industrieboden NRW | Keramische Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Nordrhein-Westfalen.",
      canonicalPath: "/standorte/nrw/",
    },
  ];
}
```

Vorher prüfen: `src/pages/standorte/nrw/index.astro` lesen, um `title`/`description`/`h1` exakt zu übernehmen (nicht raten) — die obigen Werte für Hamburg/Bayern sind aus den bereits gelesenen Dateien `src/pages/standorte/hamburg/index.astro:8-9,14` und `src/pages/standorte/bayern/index.astro:8-9,14` übernommen; NRW-Datei war zum Planzeitpunkt noch nicht gelesen und muss vom Implementierer vor dem Einfügen mit `cat src/pages/standorte/nrw/index.astro` geprüft werden, damit `title`/`description`/`h1` exakt übereinstimmen.

Entferne die letzte `];` und `}` am ursprünglichen Ende der Funktion (Zeile 180-181) und ersetze sie durch die neuen Einträge gefolgt von `];` und `}`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/sitemap-standorte.test.ts`
Expected: PASS (beide Tests grün, sobald NRW-Werte korrekt übernommen wurden)

- [ ] **Step 5: Run sitemap consistency check to confirm no regression**

Run: `npm run build && npm run check:sitemap`
Expected: `OK: Alle N Sitemap-URLs haben eine entsprechende gebaute Datei.` — Anzahl N ist jetzt um 3 höher als vor dieser Task.

- [ ] **Step 6: Commit**

```bash
git add src/lib/content.ts tests/sitemap-standorte.test.ts
git commit -m "fix: Standortseiten in Sitemap-Generierung aufnehmen"
```

---

### Task 2: Wissensartikel „IFS/BRC-Audit: Was Auditoren am Industrieboden prüfen"

**Files:**
- Modify: `src/data/articles.ts` (neuer Artikel-Eintrag, ans Ende des Arrays anhängen)
- Modify: `src/data/industries.ts:44-50` (`relatedArticles` der Lebensmittelindustrie ergänzen)
- Test: `tests/content-cluster.test.ts` (bestehende Datei erweitern)

**Interfaces:**
- Konsumiert: `Article`-Typ aus `src/lib/types.ts:94` (`z.infer<typeof articleSchema>`), Sektion-Struktur `{ title: string, body: string }`.
- Produziert: neuer Slug `haccp-audit-industrieboden-pruefpunkte`, referenzierbar aus `relatedArticles`-Arrays anderer Industries/Artikel.

Themenwahl-Begründung: Der bestehende Lebensmittelindustrie-Artikelbestand deckt bereits Systemvergleich (`pu-beton-oder-...`), Molkerei-Spezifik (`warum-industrieboeden-in-molkereien-versagen`), Rutschhemmung (`rutschhemmklassen-...`) und Hohlkehle (`hohlkehle-sockelausbildung-...`) ab. Eine klare Lücke ist die Auditoren-Perspektive: was ein IFS/BRC-Prüfer konkret am Boden kontrolliert — das ist ein eigenständiger Suchintent (Qualitätsmanager, die sich auf ein Audit vorbereiten) und ergänzt statt dupliziert.

- [ ] **Step 1: Write the failing test**

```typescript
// In tests/content-cluster.test.ts, add to the existing describe block:
it("has the IFS/BRC audit article with required sections", () => {
  const article = articles.find(
    (a) => a.slug === "haccp-audit-industrieboden-pruefpunkte",
  );
  expect(article).toBeDefined();
  expect(article!.sections.length).toBeGreaterThanOrEqual(6);
  expect(article!.relatedIndustries).toContain("lebensmittelindustrie");
});

it("IFS/BRC audit article does not claim floor itself is HACCP-certified", () => {
  const article = articles.find(
    (a) => a.slug === "haccp-audit-industrieboden-pruefpunkte",
  );
  const fullText =
    article!.intro + article!.sections.map((s) => s.body).join(" ");
  expect(fullText).not.toMatch(/HACCP-zertifiziert/i);
});
```

(Wenn `tests/content-cluster.test.ts` noch keinen Import von `articles` hat, prüfen — die Datei wurde bereits in Session zuvor angelegt und importiert bereits `articles` aus `../src/data/articles`, da sie die 3 vorherigen Artikel testet.)

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/content-cluster.test.ts -t "IFS/BRC"`
Expected: FAIL — `article` is `undefined`.

- [ ] **Step 3: Add the article to `src/data/articles.ts`**

Append as new array element before the closing `];` of the `articles` array:

```typescript
  {
    slug: "haccp-audit-industrieboden-pruefpunkte",
    title: "IFS/BRC-Audit: Was Auditoren am Industrieboden prüfen",
    seoTitle: "IFS/BRC-Audit: Boden-Prüfpunkte im Detail | HSB Wissen",
    description:
      "Welche konkreten Prüfpunkte am Industrieboden bei IFS- und BRC-Audits in der Lebensmittelproduktion typischerweise zu Beanstandungen führen und wie sich Betriebe vorbereiten.",
    h1: "IFS/BRC-Audit: Diese Prüfpunkte am Boden entscheiden über die Bewertung",
    category: "Audit & Hygiene",
    readTime: "8 Minuten",
    intro:
      "Bei IFS- und BRC-Audits gehört der Produktionsboden zu den Bereichen, die Auditoren mit besonderer Aufmerksamkeit prüfen — nicht aus Formalismus, sondern weil bauliche Mängel am Boden direkt auf Hygienerisiken hindeuten. Qualitätsmanager, die sich auf ein Audit vorbereiten, profitieren davon, die typischen Prüfpunkte vorab zu kennen.",
    sections: [
      {
        title: "Warum der Boden im Audit überproportional Aufmerksamkeit bekommt",
        body: "Anders als viele andere Betriebsbereiche ist der Boden permanent Nässe, Reinigungschemie und mechanischer Belastung ausgesetzt. Auditoren wissen aus Erfahrung, dass sich hier Schwachstellen am schnellsten zeigen — ein beschädigter Boden ist oft ein früher Indikator für generelle Instandhaltungsdefizite im Betrieb, nicht nur ein isoliertes Problem.",
      },
      {
        title: "Prüfpunkt 1: Fugenzustand und Rissbildung",
        body: "Offene, poröse oder abgeplatzte Fugen sind einer der häufigsten Beanstandungsgründe. Auditoren prüfen visuell und teils durch Abtasten, ob Fugen noch geschlossen und intakt sind. Risse im Belag selbst gelten als potenzielle Eintrittsstellen für Feuchtigkeit in den Unterbau und werden entsprechend kritisch dokumentiert.",
      },
      {
        title: "Prüfpunkt 2: Hohlkehlen und Wand-Boden-Übergänge",
        body: "Eine durchgehende, gerundete Hohlkehle ohne Unterbrechung ist Standard-Prüfpunkt. Fehlt sie an Ecken, Rohrdurchführungen oder Türlaibungen, wird das als Ansatzpunkt für Schmutz- und Keimansammlung gewertet — ein Detail, das in der Bauplanung leicht übersehen wird, im Audit aber gezielt kontrolliert wird.",
      },
      {
        title: "Prüfpunkt 3: Gefälle und stehendes Wasser",
        body: "Auditoren beobachten nach Reinigungsvorgängen, ob sich Wasser an bestimmten Stellen sammelt statt zügig zu Abläufen zu fließen. Stehendes Wasser gilt als direktes Hygienerisiko und wird unabhängig von der sonstigen Bodenqualität als Mangel vermerkt.",
      },
      {
        title: "Prüfpunkt 4: Zustand der Entwässerungsrinnen und Abläufe",
        body: "Rinnen und Abläufe werden auf Reinigbarkeit, Materialzustand und korrekte Anbindung an den Boden geprüft. Lose oder korrodierte Rinnenabdeckungen, ebenso wie unzureichend abgedichtete Übergänge zwischen Rinne und Belag, sind wiederkehrende Beanstandungspunkte.",
      },
      {
        title: "Prüfpunkt 5: Reinigbarkeit der Oberfläche selbst",
        body: "Poren, raue Stellen oder abgenutzte Beschichtungen, die sich nicht mehr rückstandsfrei reinigen lassen, fallen Auditoren häufig bei der Sichtprüfung unter Beleuchtung auf. Eine glatte, aber ausreichend rutschhemmende Oberfläche ist der Zielkonflikt, den ein fachgerecht geplantes System auflösen muss.",
      },
      {
        title: "Was ein Betrieb vor dem Audit realistisch selbst prüfen kann",
        body: "Eine eigene Begehung mit den genannten fünf Punkten als Checkliste — Fugen, Hohlkehlen, Gefälle, Rinnenzustand, Oberflächenreinigbarkeit — deckt die häufigsten Beanstandungsursachen ab. Wo bereits sichtbare Mängel bestehen, ist eine kurzfristige kosmetische Ausbesserung meist keine dauerhafte Lösung, da die zugrunde liegende Ursache (z. B. Fugenmaterial ungeeignet für die Medienbelastung) bestehen bleibt.",
      },
      {
        title: "Boden-Zustand vor dem nächsten Audit bewerten lassen",
        body: "HSB bewertet den Ist-Zustand von Fugen, Hohlkehlen und Entwässerung vor Ort und zeigt auf, welche Punkte bei einem IFS- oder BRC-Audit voraussichtlich auffallen würden — als Grundlage für eine gezielte statt pauschale Sanierungsentscheidung.",
      },
    ],
    relatedServices: ["keramische-industrieboeden", "entwaesserung-industrieboden"],
    relatedIndustries: ["lebensmittelindustrie", "molkerei", "backwarenproduktion-grosskueche"],
  },
```

- [ ] **Step 4: Add slug to Lebensmittelindustrie `relatedArticles`**

In `src/data/industries.ts`, in the `lebensmittelindustrie` entry's `relatedArticles` array (currently lines 44-50), add the new slug:

```typescript
    relatedArticles: [
      "pu-beton-oder-keramischer-industrieboden",
      "saeurefeste-fliesen-industrieboden",
      "entwaesserung-gefaelle-produktionsbereiche",
      "rutschhemmklassen-r9-bis-r13-industrieboden",
      "hohlkehle-sockelausbildung-industrieboden",
      "haccp-audit-industrieboden-pruefpunkte",
    ],
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/content-cluster.test.ts`
Expected: PASS (alle Tests inkl. neuer, plus bestehende drei Artikel-Tests unverändert grün)

- [ ] **Step 6: Run full content validation**

Run: `npx vitest run tests/content-meta.test.ts tests/content-cluster.test.ts`
Expected: PASS — `seoTitle` ist 55 Zeichen lang (`"IFS/BRC-Audit: Boden-Prüfpunkte im Detail | HSB Wissen"`), unter dem 60-Zeichen-Limit, und eindeutig.

- [ ] **Step 7: Commit**

```bash
git add src/data/articles.ts src/data/industries.ts tests/content-cluster.test.ts
git commit -m "feat: Wissensartikel zu IFS/BRC-Audit-Prüfpunkten ergänzen"
```

---

### Task 3: Wissensartikel „ESD-Ableitfähigkeit und Explosionsschutz im Industrieboden"

**Files:**
- Modify: `src/data/articles.ts` (neuer Artikel-Eintrag)
- Modify: `src/data/industries.ts:207-211` (`relatedArticles` der Chemieindustrie ergänzen)
- Test: `tests/content-cluster.test.ts` (weiter erweitern)

**Interfaces:**
- Konsumiert: gleiche `Article`-Struktur wie Task 2.
- Produziert: neuer Slug `esd-ableitfaehigkeit-explosionsschutz-industrieboden`.

Themenwahl-Begründung: Der Chemieindustrie-Artikelbestand deckt Systemvergleich, säurefeste Fliesen und WHG-Abdichtung ab. `floorRequirements` der Chemieindustrie in `industries.ts:185` nennt bereits "ESD-Ableitfähigkeit (DIN EN 61340-5-1)" als Anforderung, aber kein Artikel vertieft dieses Thema — klare inhaltliche Lücke, kein Duplikat.

- [ ] **Step 1: Write the failing test**

```typescript
// In tests/content-cluster.test.ts:
it("has the ESD/explosion protection article with required sections", () => {
  const article = articles.find(
    (a) => a.slug === "esd-ableitfaehigkeit-explosionsschutz-industrieboden",
  );
  expect(article).toBeDefined();
  expect(article!.sections.length).toBeGreaterThanOrEqual(6);
  expect(article!.relatedIndustries).toContain("chemieindustrie");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/content-cluster.test.ts -t "ESD"`
Expected: FAIL — `article` is `undefined`.

- [ ] **Step 3: Add the article to `src/data/articles.ts`**

Append as new array element:

```typescript
  {
    slug: "esd-ableitfaehigkeit-explosionsschutz-industrieboden",
    title: "ESD-Ableitfähigkeit und Explosionsschutz im Industrieboden",
    seoTitle: "ESD-Boden: Ableitfähigkeit nach DIN EN 61340 | HSB Wissen",
    description:
      "Wann ein ableitfähiger ESD-Boden nach DIN EN 61340-5-1 in Ex-Zonen und explosionsgefährdeten Chemiebereichen vorgeschrieben ist und worauf bei der Systemauswahl zu achten ist.",
    h1: "ESD-Ableitfähigkeit: Wann ein Industrieboden elektrostatisch ableiten muss",
    category: "Recht & Technik",
    readTime: "8 Minuten",
    intro:
      "In explosionsgefährdeten Bereichen der Chemieindustrie kann eine unkontrollierte elektrostatische Aufladung des Bodens zur Zündquelle werden. Die Norm DIN EN 61340-5-1 regelt, welcher Ableitwiderstand ein Bodensystem in solchen Zonen erfüllen muss — eine Anforderung, die weit über normale Rutschhemmung oder Chemikalienbeständigkeit hinausgeht.",
    sections: [
      {
        title: "Das physikalische Risiko: Elektrostatische Entladung als Zündquelle",
        body: "Bewegen sich Personen oder Flurförderzeuge über einen elektrisch isolierenden Boden, kann sich statische Ladung aufbauen. Entlädt sich diese Ladung schlagartig — etwa beim Berühren einer geerdeten Anlage —, entsteht ein Funke. In Bereichen mit explosionsfähiger Atmosphäre (Lösungsmitteldämpfe, brennbare Stäube) reicht dieser Funke potenziell aus, um eine Explosion auszulösen.",
      },
      {
        title: "Wann ESD-Ableitfähigkeit gefordert ist",
        body: "Maßgeblich ist die Einstufung des Bereichs nach der Betriebssicherheitsverordnung bzw. den Ex-Zonen (Zone 0, 1, 2 für Gase; Zone 20, 21, 22 für Stäube). Innerhalb dieser klassifizierten Zonen ist ein ableitfähiger Bodenbelag in der Regel zwingend Teil des Explosionsschutzkonzepts, nicht optional. Die konkrete Zoneneinstufung erfolgt durch den Betreiber im Rahmen des Explosionsschutzdokuments, nicht durch den Bodenbauer.",
      },
      {
        title: "Der geforderte Widerstandsbereich nach DIN EN 61340-5-1",
        body: "Die Norm definiert einen Ableitwiderstand, der weder zu hoch (keine Ableitung, Ladung baut sich auf) noch zu niedrig (Gefahr des elektrischen Durchschlags bei Kontakt mit spannungsführenden Teilen) sein darf. Ein ESD-Boden muss diesen Fensterbereich dauerhaft einhalten — nicht nur bei der Erstprüfung, sondern über die gesamte Nutzungsdauer, auch nach mechanischer Beanspruchung.",
      },
      {
        title: "Wie die Ableitfähigkeit technisch erreicht wird",
        body: "Ableitfähige Systeme enthalten leitfähige Zusatzstoffe (häufig Kohlenstoff- oder Metallpartikel) im Bindemittel oder als separate leitfähige Zwischenschicht (Kupferbändchen-Netz), die eine durchgehende Verbindung zur Erdung herstellt. Diese leitfähige Schicht muss lückenlos verlegt und korrekt geerdet sein — eine Unterbrechung an nur einer Stelle kann die Ableitfähigkeit der gesamten Fläche funktionslos machen.",
      },
      {
        title: "Prüfung und Dokumentation",
        body: "Die Ableitfähigkeit wird nach Einbau messtechnisch geprüft und muss dokumentiert werden — dieser Nachweis ist Teil der Übergabeunterlagen und wird bei sicherheitstechnischen Prüfungen (z. B. durch den TÜV oder eine befähigte Person nach BetrSichV) regelmäßig erneut abgefragt. Ohne aktuellen Prüfnachweis ist die Betriebssicherheit der Fläche formal nicht belegt, unabhängig vom tatsächlichen physischen Zustand.",
      },
      {
        title: "Typischer Fehler: ESD-Anforderung erst nach Einbau erkannt",
        body: "In der Praxis wird die Ex-Zonen-Klassifizierung eines Bereichs manchmal erst nach der Bodenplanung final festgelegt, etwa wenn sich die Nutzung eines Raums ändert. Ein bereits eingebauter, nicht-ableitfähiger Boden lässt sich nicht nachträglich einfach ableitfähig machen — meist ist ein vollständiger Systemwechsel nötig. Die Klärung der Zonenklassifizierung vor Baubeginn ist deshalb keine Formalität, sondern vermeidet kostspielige Nacharbeit.",
      },
      {
        title: "Zusammenspiel mit anderen Anforderungen",
        body: "Ein Boden in einer Ex-Zone der Chemieindustrie muss ESD-Ableitfähigkeit häufig gleichzeitig mit hoher Chemikalienbeständigkeit und WHG-konformer Abdichtung erfüllen. Diese Anforderungen stehen nicht im Widerspruch, müssen aber bei der Systemauswahl gemeinsam betrachtet werden — ein System, das nur eine der drei Anforderungen optimal erfüllt, ist für solche Bereiche ungeeignet.",
      },
      {
        title: "ESD-Anforderung für Ihren Bereich klären lassen",
        body: "Ob und in welchem Umfang Ihr Produktionsbereich eine ESD-ableitfähige Bodenlösung benötigt, hängt von der konkreten Ex-Zonen-Einstufung ab. HSB plant Bodensysteme, die Ableitfähigkeit, Chemikalienbeständigkeit und Abdichtung als Gesamtsystem zusammenführen, statt Einzelanforderungen isoliert zu betrachten.",
      },
    ],
    relatedServices: ["industrieboden-saeureschutz", "whg-abdichtung-industrieboden", "epoxidharz-bodenbeschichtung"],
    relatedIndustries: ["chemieindustrie", "pharmaindustrie"],
  },
```

- [ ] **Step 4: Add slug to Chemieindustrie `relatedArticles`**

In `src/data/industries.ts`, in the `chemieindustrie` entry's `relatedArticles` array (currently lines 207-211), add the new slug:

```typescript
    relatedArticles: [
      "saeurefeste-fliesen-industrieboden",
      "pu-beton-oder-keramischer-industrieboden",
      "whg-abdichtung-industrieboden-pflicht",
      "esd-ableitfaehigkeit-explosionsschutz-industrieboden",
    ],
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/content-cluster.test.ts`
Expected: PASS (alle Tests inkl. beider neuer Artikel grün)

- [ ] **Step 6: Run full content validation**

Run: `npx vitest run tests/content-meta.test.ts tests/content-cluster.test.ts`
Expected: PASS — `seoTitle` ist 54 Zeichen lang (`"ESD-Boden: Ableitfähigkeit nach DIN EN 61340 | HSB Wissen"` — Implementierer: exakte Zeichenzahl vor Commit mit `node -e "console.log('ESD-Boden: Ableitfähigkeit nach DIN EN 61340 | HSB Wissen'.length)"` nachprüfen, da Umlaute), unter dem 60-Zeichen-Limit, und eindeutig gegenüber allen bestehenden `seoTitle`-Werten.

- [ ] **Step 7: Commit**

```bash
git add src/data/articles.ts src/data/industries.ts tests/content-cluster.test.ts
git commit -m "feat: Wissensartikel zu ESD-Ableitfähigkeit und Explosionsschutz ergänzen"
```

---

### Task 4: Standortseite Rheinland-Pfalz

**Files:**
- Create: `src/pages/standorte/rheinland-pfalz/index.astro`
- Modify: `src/lib/content.ts` (`getAllPublicPages()`, Eintrag ergänzen — baut auf Task 1 auf)
- Test: `tests/sitemap-standorte.test.ts` (aus Task 1, Assertion erweitern)

**Interfaces:**
- Konsumiert: `BaseLayout`, `PageHero`, `CTASection` Komponenten (identisches Muster wie `src/pages/standorte/bayern/index.astro`).
- Produziert: neue Route `/standorte/rheinland-pfalz/`, neuer `canonicalPath`-Eintrag in `getAllPublicPages()`.

Beleg für diese Region: `src/data/clientLocations.ts` enthält 4 Einträge mit `region: "Rheinland-Pfalz"` (Biovegan/Bonefeld, KESSLER-ZINK/Flonheim, Weingut Dohlmühle-Genussreich/Flonheim, Griesson-de Beukelaer/Polch) — die zweitstärkste Regionshäufung nach dem bereits abgedeckten NRW. `src/data/references.ts` enthält zudem den benannten Referenzeintrag `biovegan-bonefeld` (Lebensmittelindustrie, Bonefeld, Rheinland-Pfalz) mit Freigabe.

- [ ] **Step 1: Write the failing test**

```typescript
// In tests/sitemap-standorte.test.ts, add:
it("includes the new Rheinland-Pfalz location page", () => {
  const pages = getAllPublicPages();
  const paths = pages.map((p) => p.canonicalPath);
  expect(paths).toContain("/standorte/rheinland-pfalz/");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/sitemap-standorte.test.ts -t "Rheinland-Pfalz"`
Expected: FAIL — `paths` does not contain `/standorte/rheinland-pfalz/`.

- [ ] **Step 3: Create the Astro page**

```astro
---
// src/pages/standorte/rheinland-pfalz/index.astro
import CTASection from "../../../components/sections/CTASection.astro";
import PageHero from "../../../components/sections/PageHero.astro";
import BaseLayout from "../../../layouts/BaseLayout.astro";
---

<BaseLayout
  title="Industrieboden Rheinland-Pfalz | Böden & Säureschutz"
  description="HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Rheinland-Pfalz. Projekte in Mainz, Koblenz, Trier und der gesamten Region."
  path="/standorte/rheinland-pfalz/"
>
  <PageHero
    eyebrow="Region Rheinland-Pfalz"
    title="Industrieboden-Spezialist in Rheinland-Pfalz"
    text="HSB Hexagon realisiert anspruchsvolle Industriebodenprojekte in Mainz, Koblenz, Trier, Ludwigshafen und der gesamten Region Rheinland-Pfalz."
  />

  <section class="section">
    <div class="container">
      <div class="prose max-w-3xl mx-auto">
        <h2>Keramische Industrieböden in Rheinland-Pfalz</h2>
        <p>
          Als erfahrener Fachbetrieb für keramische Industrieböden und Säureschutzsysteme sind wir in
          Rheinland-Pfalz tätig. Ob Lebensmittelbetriebe im Westerwald, Winzerbetriebe in Rheinhessen oder
          Getränkeproduktion entlang des Rheins – HSB Hexagon liefert dauerhaft belastbare Bodensysteme.
        </p>

        <h2>Unsere Leistungen in Rheinland-Pfalz</h2>
        <ul>
          <li><strong>Keramische Industrieböden</strong> – rutschhemmend, hygienekonform, chemikalienbeständig</li>
          <li><strong>Säureschutzsysteme</strong> – für Lebensmittel-, Getränke- und Chemiebetriebe</li>
          <li><strong>Entwässerungssysteme</strong> – GFK-Rinnen, Punktabläufe, Ex-Zonen</li>
          <li><strong>Industrieboden-Sanierung</strong> – Reparatur und Erneuerung bestehender Böden</li>
        </ul>

        <h2>Regionale Präsenz in Rheinland-Pfalz</h2>
        <p>
          Wir betreuen Projekte in der gesamten Region Rheinland-Pfalz: Mainz, Koblenz, Trier, Ludwigshafen,
          Kaiserslautern und Umgebung. Schnelle Reaktionszeiten und fundiertes Know-how für Industriebetriebe
          in der Region.
        </p>
      </div>
    </div>
  </section>

  <CTASection
    title="Projekt in Rheinland-Pfalz anfragen"
    text="Kontaktieren Sie uns für eine unverbindliche Beratung zu Ihrem Industriebodenprojekt in Rheinland-Pfalz."
  />

  <script type="application/ld+json" set:html={JSON.stringify({
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Hexagon Säurebau GmbH",
    "description": "Spezialist für keramische Industrieböden in Rheinland-Pfalz",
    "url": "https://www.hsb-boden.de",
    "areaServed": [
      {"@type": "City", "name": "Mainz"},
      {"@type": "City", "name": "Koblenz"},
      {"@type": "City", "name": "Trier"},
      {"@type": "City", "name": "Ludwigshafen"},
      {"@type": "City", "name": "Kaiserslautern"},
      {"@type": "AdministrativeArea", "name": "Rheinland-Pfalz"}
    ],
    "sameAs": "https://www.hsb-boden.de"
  })} />
</BaseLayout>
```

- [ ] **Step 4: Add the new page to `getAllPublicPages()`**

In `src/lib/content.ts`, add another entry in the same Standorte block introduced by Task 1:

```typescript
    {
      h1: "Industrieboden-Spezialist in Rheinland-Pfalz",
      seoTitle: "Industrieboden Rheinland-Pfalz | Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Rheinland-Pfalz. Projekte in Mainz, Koblenz, Trier und der gesamten Region.",
      canonicalPath: "/standorte/rheinland-pfalz/",
    },
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/sitemap-standorte.test.ts`
Expected: PASS

- [ ] **Step 6: Build and verify the page renders**

Run: `npm run build && test -f dist/standorte/rheinland-pfalz/index.html && echo "OK: Seite gebaut"`
Expected: `OK: Seite gebaut`

- [ ] **Step 7: Commit**

```bash
git add src/pages/standorte/rheinland-pfalz/index.astro src/lib/content.ts tests/sitemap-standorte.test.ts
git commit -m "feat: Standortseite Rheinland-Pfalz ergänzen"
```

---

### Task 5: Standortseite Baden-Württemberg

**Files:**
- Create: `src/pages/standorte/baden-wuerttemberg/index.astro`
- Modify: `src/lib/content.ts` (`getAllPublicPages()`, Eintrag ergänzen)
- Test: `tests/sitemap-standorte.test.ts` (Assertion erweitern)

**Interfaces:**
- Konsumiert: gleiche Komponenten wie Task 4.
- Produziert: neue Route `/standorte/baden-wuerttemberg/`.

Beleg für diese Region: `src/data/clientLocations.ts` enthält 2 Einträge mit `region: "Baden-Württemberg"` (Auerquelle Bissingen, Albers Brauhaus/Weilheim an der Teck). `src/data/references.ts` enthält zusätzlich den benannten Referenzeintrag `mineralbrunnen-schwarzwald` (Peterstaler Mineralquellen GmbH, Bad Peterstal-Griesbach, Baden-Württemberg) mit Logo-Freigabe — die einzige Region außerhalb der bereits bestehenden Standortseiten mit einer vollständig benannten, logo-freigegebenen Referenz.

- [ ] **Step 1: Write the failing test**

```typescript
// In tests/sitemap-standorte.test.ts, add:
it("includes the new Baden-Württemberg location page", () => {
  const pages = getAllPublicPages();
  const paths = pages.map((p) => p.canonicalPath);
  expect(paths).toContain("/standorte/baden-wuerttemberg/");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/sitemap-standorte.test.ts -t "Baden-Württemberg"`
Expected: FAIL — `paths` does not contain `/standorte/baden-wuerttemberg/`.

- [ ] **Step 3: Create the Astro page**

```astro
---
// src/pages/standorte/baden-wuerttemberg/index.astro
import CTASection from "../../../components/sections/CTASection.astro";
import PageHero from "../../../components/sections/PageHero.astro";
import BaseLayout from "../../../layouts/BaseLayout.astro";
---

<BaseLayout
  title="Industrieboden Baden-Württemberg | Böden & Säureschutz"
  description="HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Baden-Württemberg. Projekte in Stuttgart, Karlsruhe, Freiburg und der gesamten Region."
  path="/standorte/baden-wuerttemberg/"
>
  <PageHero
    eyebrow="Region Baden-Württemberg"
    title="Industrieboden-Spezialist in Baden-Württemberg"
    text="HSB Hexagon realisiert anspruchsvolle Industriebodenprojekte in Stuttgart, Karlsruhe, Freiburg, Mannheim und der gesamten Region Baden-Württemberg."
  />

  <section class="section">
    <div class="container">
      <div class="prose max-w-3xl mx-auto">
        <h2>Keramische Industrieböden in Baden-Württemberg</h2>
        <p>
          Als erfahrener Fachbetrieb für keramische Industrieböden und Säureschutzsysteme sind wir in
          Baden-Württemberg tätig. Ob Getränkeabfüllung im Schwarzwald, Brauereien in der Region Stuttgart oder
          Chemiebetriebe entlang des Neckars – HSB Hexagon liefert dauerhaft belastbare Bodensysteme.
        </p>

        <h2>Unsere Leistungen in Baden-Württemberg</h2>
        <ul>
          <li><strong>Keramische Industrieböden</strong> – rutschhemmend, hygienekonform, chemikalienbeständig</li>
          <li><strong>Säureschutzsysteme</strong> – für Getränke-, Lebensmittel- und Chemiebetriebe</li>
          <li><strong>Entwässerungssysteme</strong> – GFK-Rinnen, Punktabläufe, Ex-Zonen</li>
          <li><strong>Industrieboden-Sanierung</strong> – Reparatur und Erneuerung bestehender Böden</li>
        </ul>

        <h2>Regionale Präsenz in Baden-Württemberg</h2>
        <p>
          Wir betreuen Projekte in der gesamten Region Baden-Württemberg: Stuttgart, Karlsruhe, Freiburg,
          Mannheim, Ulm und Umgebung. Schnelle Reaktionszeiten und fundiertes Know-how für Industriebetriebe
          in der Region.
        </p>
      </div>
    </div>
  </section>

  <CTASection
    title="Projekt in Baden-Württemberg anfragen"
    text="Kontaktieren Sie uns für eine unverbindliche Beratung zu Ihrem Industriebodenprojekt in Baden-Württemberg."
  />

  <script type="application/ld+json" set:html={JSON.stringify({
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Hexagon Säurebau GmbH",
    "description": "Spezialist für keramische Industrieböden in Baden-Württemberg",
    "url": "https://www.hsb-boden.de",
    "areaServed": [
      {"@type": "City", "name": "Stuttgart"},
      {"@type": "City", "name": "Karlsruhe"},
      {"@type": "City", "name": "Freiburg"},
      {"@type": "City", "name": "Mannheim"},
      {"@type": "City", "name": "Ulm"},
      {"@type": "AdministrativeArea", "name": "Baden-Württemberg"}
    ],
    "sameAs": "https://www.hsb-boden.de"
  })} />
</BaseLayout>
```

- [ ] **Step 4: Add the new page to `getAllPublicPages()`**

In `src/lib/content.ts`:

```typescript
    {
      h1: "Industrieboden-Spezialist in Baden-Württemberg",
      seoTitle: "Industrieboden Baden-Württemberg | Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Baden-Württemberg. Projekte in Stuttgart, Karlsruhe, Freiburg und der gesamten Region.",
      canonicalPath: "/standorte/baden-wuerttemberg/",
    },
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/sitemap-standorte.test.ts`
Expected: PASS (alle 5 Assertions grün: 3 bestehende Standorte + Rheinland-Pfalz + Baden-Württemberg)

- [ ] **Step 6: Build and verify the page renders**

Run: `npm run build && test -f dist/standorte/baden-wuerttemberg/index.html && echo "OK: Seite gebaut"`
Expected: `OK: Seite gebaut`

- [ ] **Step 7: Commit**

```bash
git add src/pages/standorte/baden-wuerttemberg/index.astro src/lib/content.ts tests/sitemap-standorte.test.ts
git commit -m "feat: Standortseite Baden-Württemberg ergänzen"
```

---

### Task 6: Gesamtvalidierung und Sitemap-Konsistenz-Check

**Files:**
- Keine neuen Dateien — reiner Verifikationsschritt.

**Interfaces:**
- Konsumiert: alle Artefakte aus Task 1-5.
- Produziert: nichts Neues; bestätigt, dass `validateSiteContent()` aus `src/lib/content.ts:14` weiterhin fehlerfrei durchläuft und die Sitemap vollständig konsistent ist.

- [ ] **Step 1: Run full test suite**

Run: `npm run test:run`
Expected: Alle Tests PASS, inklusive `tests/content-meta.test.ts`, `tests/content-cluster.test.ts`, `tests/sitemap-standorte.test.ts`, `tests/article-attribution.test.ts` und allen bestehenden Tests ohne Regression.

- [ ] **Step 2: Run type/lint check**

Run: `npm run check`
Expected: Keine TypeScript- oder Astro-Check-Fehler.

- [ ] **Step 3: Full build**

Run: `npm run build`
Expected: Build erfolgreich, keine Zod-Validierungsfehler aus `validateSiteContent()` (würde als Build-Fehler auffallen, falls diese Funktion in den Build-Prozess eingebunden ist — andernfalls separat prüfen mit Schritt 4).

- [ ] **Step 4: Sitemap consistency check (reverse direction)**

Run: `npm run check:sitemap`
Expected: `OK: Alle N Sitemap-URLs haben eine entsprechende gebaute Datei.` — bestätigt, dass jede Sitemap-URL auch eine gebaute Datei hat (Task 1's Skript aus der Vorsession).

- [ ] **Step 5: Manual forward-direction check — every built Standorte page is now in the sitemap**

Run:
```bash
npm run build
for dir in dist/standorte/*/; do
  slug=$(basename "$dir")
  grep -q "/standorte/$slug/" dist/sitemap.xml && echo "OK: $slug in Sitemap" || echo "FEHLT: $slug NICHT in Sitemap"
done
```
Expected: `OK: baden-wuerttemberg in Sitemap`, `OK: bayern in Sitemap`, `OK: hamburg in Sitemap`, `OK: nrw in Sitemap`, `OK: rheinland-pfalz in Sitemap` — keine `FEHLT`-Zeile.

- [ ] **Step 6: Manuelle 60-Zeichen-Prüfung für neue `seoTitle`-Werte**

`tests/content-meta.test.ts` prüft die 60-Zeichen-SERP-Grenze bisher nur für `industries`, nicht für `articles` oder die neuen Standortseiten-Einträge in `getAllPublicPages()`. Da kein automatisierter Test diese vier neuen Werte abdeckt, hier manuell verifizieren:

```bash
node -e "
const titles = {
  'IFS/BRC-Audit-Artikel': 'IFS/BRC-Audit: Boden-Prüfpunkte im Detail | HSB Wissen',
  'ESD-Artikel': 'ESD-Boden: Ableitfähigkeit nach DIN EN 61340 | HSB Wissen',
  'Rheinland-Pfalz': 'Industrieboden Rheinland-Pfalz | Böden & Säureschutz',
  'Baden-Württemberg': 'Industrieboden Baden-Württemberg | Böden & Säureschutz',
};
for (const [name, title] of Object.entries(titles)) {
  console.log(\`\${title.length <= 60 ? 'OK' : 'FEHLER'}: \${name} (\${title.length} Zeichen)\`);
}
"
```
Expected: Alle vier Zeilen beginnen mit `OK` (Werte bereits im Plan mit 54, 57, 52, 54 Zeichen berechnet — dieser Schritt bestätigt es am tatsächlich implementierten Code, falls der Implementierer Formulierungen angepasst hat).

- [ ] **Step 7: No commit needed — verification-only task**

Falls Schritt 5 eine `FEHLT`-Zeile zeigt, zurück zu Task 1/4/5 und den fehlenden `canonicalPath`-Eintrag in `src/lib/content.ts` ergänzen, bevor fortgefahren wird.

---

## Nicht in diesem Plan

- **GA4 `generate_lead`-Event in DebugView verifizieren, als Key Event markieren** — reine Owner-Aktion im Google-Konto, kein Code-Task.
- **GSC-Property prüfen, Indexierung neuer Artikel beobachten** — reine Owner-Aktion in der Google Search Console, kein Code-Task. Sollte nach Merge dieses Plans erfolgen, damit auch die 2 neuen Wissensartikel und 2 neuen Standortseiten mit erfasst werden.
- **Team-Profile-Daten für vollständiges E-E-A-T** — braucht echte Personendaten (Namen, Fotos, Bios, Einwilligung) vom Owner; `src/data/trustContent.ts` bleibt bis dahin bewusst leer.
- **DKIM-Aktivierung für `hsb-boden.de`** — zurückgestellt, Owner muss zuerst klären, welches M365-Konto Admin-Rechte im Tenant hat (siehe `blocked_followups` in `active_state.json`).
