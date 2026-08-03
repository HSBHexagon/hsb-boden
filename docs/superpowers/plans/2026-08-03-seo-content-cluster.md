# SEO Meta-Audit & Content-Cluster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bestehende Fachbegriffe (HACCP, WHG, R12/R13) in Meta-Titles sichtbar machen, eine sichtbare Autoren-/Herkunfts-Box auf Wissensartikeln ergänzen, einen Sitemap-Build-Konsistenz-Check schreiben, und drei neue Wissensartikel als Content-Cluster-Erweiterung hinzufügen.

**Architecture:** Reine Datei- und Datenänderungen in einem bestehenden Astro-Projekt. Keine neuen Abhängigkeiten, keine neuen Architekturmuster — jede Aufgabe folgt einem Muster, das im Repo bereits an mindestens einer Stelle existiert (bestehende Branchenseite, bestehender Wissensartikel, bestehender Test).

**Tech Stack:** Astro (static output), TypeScript, Zod (Datenvalidierung in `src/lib/types.ts`), Vitest.

## Global Constraints

- Keine unbelegten Zertifizierungs-/Referenzclaims, keine Kundennamen/Logos ohne Freigabe (`CLAUDE.md`, `AGENTS.md`).
- HACCP ist kein Bodenzertifikat, sondern ein Prozessstandard — nie als "HACCP-zertifiziert" formulieren, nur als "erfüllt HACCP-Anforderungen" (siehe Design-Spec, Abschnitt "Wichtige Nuance").
- Kein `git add .` — immer exakte Pfade stagen (`CLAUDE.md`).
- Vor jedem Abschluss-Claim: `npm run check`, `npm run test:run`, `npm run build` müssen grün sein (`CLAUDE.md` Deploy Gate).
- Jede neue/geänderte Seite braucht einen einzigartigen `seoTitle` (kein Duplicate-Content).
- Keine Push/Deploy-Aktion ohne Freigabe (`CLAUDE.md`) — dieser Plan endet bei lokal committeten Änderungen.

---

### Task 1: Meta-Title-Audit — HACCP/WHG/R-Klassen in Branchenseiten sichtbar machen

**Files:**
- Modify: `src/data/industries.ts:7` (Lebensmittelindustrie `seoTitle`)
- Modify: `src/data/industries.ts:167` (Chemieindustrie `seoTitle`)
- Test: `tests/content-meta.test.ts` (neu)

**Interfaces:**
- Konsumiert: `Industry`-Typ aus `src/lib/types.ts` (Feld `seoTitle: z.string().min(20)` — bereits vorhanden, keine Schema-Änderung nötig).
- Produziert: nichts Neues für andere Tasks — reine Datenkorrektur.

**Kontext:** Aktuell fehlt `HACCP` im `seoTitle` der Lebensmittelindustrie-Seite (`"Industrieboden für Lebensmittelindustrie | Hexagon Säurebau"`), obwohl `HACCP` bereits in `floorRequirements` und `faqs` derselben Seite belegt vorkommt (Zeilen 22, 45 in `industries.ts`). Gleiches gilt für `WHG` bei der Chemieindustrie-Seite (`seoTitle: "Säureschutz & WHG-Industrieböden | Hexagon Säurebau"` — hier ist WHG bereits enthalten, nur zur Vollständigkeit prüfen ob weitere Fachbegriffe fehlen).

- [ ] **Step 1: Aktuellen Zustand lesen und Ziel-Title festlegen**

Lies `src/data/industries.ts` Zeile 1-58 (Lebensmittelindustrie-Objekt komplett) um den exakten Kontext zu bestätigen.

- [ ] **Step 2: Schreibe den fehlschlagenden Test**

Erstelle `tests/content-meta.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { industries } from "../src/data/industries";

describe("industry meta titles reflect documented compliance terms", () => {
  it("includes HACCP in the Lebensmittelindustrie seoTitle since HACCP is already a documented requirement for this industry", () => {
    const lebensmittel = industries.find((i) => i.slug === "lebensmittelindustrie");
    expect(lebensmittel).toBeDefined();
    expect(lebensmittel!.floorRequirements.some((r) => r.includes("HACCP"))).toBe(true);
    expect(lebensmittel!.seoTitle).toContain("HACCP");
  });

  it("every industry has a unique seoTitle (no duplicate content)", () => {
    const titles = industries.map((i) => i.seoTitle);
    const uniqueTitles = new Set(titles);
    expect(uniqueTitles.size).toBe(titles.length);
  });

  it("every industry seoTitle stays under 60 characters for SERP display", () => {
    for (const industry of industries) {
      expect(industry.seoTitle.length).toBeLessThanOrEqual(60);
    }
  });
});
```

- [ ] **Step 3: Test ausführen, Fehlschlag bestätigen**

Run: `npx vitest run tests/content-meta.test.ts`
Expected: FAIL bei "includes HACCP in the Lebensmittelindustrie seoTitle" (aktueller Title enthält `HACCP` nicht).

- [ ] **Step 4: `seoTitle` der Lebensmittelindustrie-Seite anpassen**

In `src/data/industries.ts`, ändere Zeile 7 von:
```typescript
    seoTitle: "Industrieboden für Lebensmittelindustrie | Hexagon Säurebau",
```
zu:
```typescript
    seoTitle: "HACCP-konformer Industrieboden Lebensmittelindustrie | HSB",
```

Prüfe die neue Zeichenlänge (`"HACCP-konformer Industrieboden Lebensmittelindustrie | HSB"` = 59 Zeichen, unter dem 60-Zeichen-Limit aus Step 2).

- [ ] **Step 5: Test erneut ausführen, Erfolg bestätigen**

Run: `npx vitest run tests/content-meta.test.ts`
Expected: PASS (alle drei Tests grün).

- [ ] **Step 6: Astro-Build-Check ausführen**

Run: `npm run check`
Expected: 0 Fehler (reine Textänderung an bereits typisiertem Datenobjekt, keine neuen TS-Fehler zu erwarten).

- [ ] **Step 7: Commit**

```bash
git add src/data/industries.ts tests/content-meta.test.ts
git commit -m "fix(seo): surface HACCP in Lebensmittelindustrie meta title"
```

---

### Task 2: Sichtbare Autoren-/Herkunfts-Box auf Wissensartikeln

**Files:**
- Create: `src/components/sections/ArticleAttribution.astro`
- Modify: `src/pages/wissen/[slug].astro:22-25`
- Test: `tests/article-attribution.test.ts` (neu)

**Interfaces:**
- Konsumiert: `site` aus `src/data/site.ts` (bereits importiert an anderen Stellen wie `src/lib/schema.ts:1` — exportiert mindestens `domain`, `email`, `phone`, `description`).
- Produziert: `ArticleAttribution.astro`-Komponente, die `wissen/[slug].astro` ab jetzt einbindet — keine weiteren Tasks hängen davon ab.

**Kontext:** `buildArticleJsonLd()` in `src/lib/schema.ts:114-134` setzt bereits ein `author`-Feld (Organization-Typ) im JSON-LD — das ist nur für Crawler sichtbar, nicht für menschliche Leser. `src/data/trustContent.ts` hat bewusst leere `teamProfileDrafts`/`caseStudyDrafts`-Arrays mit dem Kommentar "Intentionally empty until real people, evidence and publication consents are supplied" — echte Personendaten sind ein Owner-Gate und **nicht** Teil dieses Tasks. Diese Komponente zeigt stattdessen die bereits belegte Organisation (kein Personenname) sichtbar im Artikel an.

- [ ] **Step 1: Prüfe die `site`-Datenstruktur**

Lies `src/data/site.ts` komplett, um die exakten verfügbaren Felder zu bestätigen (erwartet: `domain`, `email`, `phone`, `description`, evtl. weitere).

- [ ] **Step 2: Schreibe den fehlschlagenden Komponenten-Test**

Erstelle `tests/article-attribution.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("ArticleAttribution component", () => {
  it("exists and references the organization name without inventing a person", () => {
    const componentPath = join(process.cwd(), "src/components/sections/ArticleAttribution.astro");
    const content = readFileSync(componentPath, "utf-8");

    expect(content).toContain("HSB Hexagon Säurebau GmbH");
    // Must not invent an individual author name — organization-level attribution only.
    expect(content).not.toMatch(/von\s+[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+/);
  });
});
```

- [ ] **Step 3: Test ausführen, Fehlschlag bestätigen**

Run: `npx vitest run tests/article-attribution.test.ts`
Expected: FAIL mit "ENOENT: no such file or directory" (Komponente existiert noch nicht).

- [ ] **Step 4: Komponente erstellen**

Erstelle `src/components/sections/ArticleAttribution.astro`:

```astro
---
import { site } from "../../data/site";

interface Props {
  readTime: string;
  category: string;
}

const { readTime, category } = Astro.props;
---

<div class="flex flex-wrap items-center gap-3 border-y border-hsb-mist/60 py-4 text-sm text-hsb-steel">
  <span class="font-medium text-hsb-ink">HSB Hexagon Säurebau GmbH</span>
  <span aria-hidden="true">·</span>
  <span>Fachbeitrag {category}</span>
  <span aria-hidden="true">·</span>
  <span>{readTime} Lesezeit</span>
  <span aria-hidden="true">·</span>
  <a href={`${site.domain}/referenzen/`} class="underline decoration-hsb-steel/40 underline-offset-4 hover:decoration-hsb-ink">
    Referenzprojekte ansehen
  </a>
</div>
```

- [ ] **Step 5: Test erneut ausführen, Erfolg bestätigen**

Run: `npx vitest run tests/article-attribution.test.ts`
Expected: PASS.

- [ ] **Step 6: Komponente in `wissen/[slug].astro` einbinden**

In `src/pages/wissen/[slug].astro`, ändere den Import-Block (aktuell Zeile 1-6):

```astro
---
import CTASection from "../../components/sections/CTASection.astro";
import PageHero from "../../components/sections/PageHero.astro";
import ArticleAttribution from "../../components/sections/ArticleAttribution.astro";
import BaseLayout from "../../layouts/BaseLayout.astro";
import { getArticles, getIndustries, getServices } from "../../lib/content";
import { buildArticleJsonLd, buildBreadcrumbJsonLd } from "../../lib/schema";
```

Füge die Komponente direkt nach `<PageHero .../>` und vor `<article class="section">` ein:

```astro
  <PageHero eyebrow={article.category} title={article.h1} text={article.description} ctaLabel="Werksbegehung anfragen" />
  <div class="container max-w-3xl">
    <ArticleAttribution readTime={article.readTime} category={article.category} />
  </div>
  <article class="section">
```

- [ ] **Step 7: Astro-Build-Check ausführen**

Run: `npm run check`
Expected: 0 Fehler.

- [ ] **Step 8: Vollen Build ausführen und eine Artikelseite stichprobenartig prüfen**

Run: `npm run build`
Expected: Build erfolgreich, 40 Seiten (wie zuvor, keine neue Seite in diesem Task).

Run: `grep -o "HSB Hexagon Säurebau GmbH" dist/wissen/warum-industrieboeden-in-molkereien-versagen/index.html | head -1`
Expected: Ausgabe zeigt den String — bestätigt, dass die Attribution-Box im gebauten HTML landet.

- [ ] **Step 9: Commit**

```bash
git add src/components/sections/ArticleAttribution.astro src/pages/wissen/\[slug\].astro tests/article-attribution.test.ts
git commit -m "feat(seo): add visible organization attribution to knowledge articles"
```

---

### Task 3: GSC-Sitemap-Build-Konsistenz-Check

**Files:**
- Create: `scripts/check-sitemap-consistency.mjs`
- Modify: `package.json` (neues npm-Script)
- Test: manueller Lauf (kein Vitest-Test — dieses Skript läuft gegen den `dist/`-Ordner, der erst nach `npm run build` existiert; siehe Step 4)

**Interfaces:**
- Konsumiert: nichts aus dem Quellcode direkt — liest `dist/` (Build-Output) und vergleicht mit den URLs aus `dist/sitemap.xml` (bereits durch `src/pages/sitemap.xml.ts` generiert).
- Produziert: `npm run check:sitemap` — ein Exit-Code-0/1-Skript, das in CI oder manuell nutzbar ist. Keine anderen Tasks hängen davon ab.

**Kontext:** `src/pages/sitemap.xml.ts` generiert die Sitemap aus `getAllPublicPages()` (`src/lib/content.ts:88-160`). Ein Abgleich der Sitemap gegen sich selbst wäre zirkulär und sinnlos. Dieser Check vergleicht stattdessen die in der Sitemap gelisteten Pfade gegen die tatsächlich im `dist/`-Ordner vorhandenen `index.html`-Dateien — das deckt auf, wenn ein Pfad in der Sitemap steht, aber die Seite beim Build nicht erzeugt wurde (oder umgekehrt).

- [ ] **Step 1: Build ausführen, um eine echte `dist/sitemap.xml` zu haben**

Run: `npm run build`
Expected: Build erfolgreich, `dist/sitemap.xml` existiert.

- [ ] **Step 2: Skript schreiben**

Erstelle `scripts/check-sitemap-consistency.mjs`:

```javascript
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const distDir = join(process.cwd(), "dist");
const sitemapPath = join(distDir, "sitemap.xml");

if (!existsSync(sitemapPath)) {
  console.error(`FEHLER: ${sitemapPath} existiert nicht. Zuerst "npm run build" ausführen.`);
  process.exit(1);
}

const sitemapXml = readFileSync(sitemapPath, "utf-8");
const locMatches = [...sitemapXml.matchAll(/<loc>(.*?)<\/loc>/g)];

if (locMatches.length === 0) {
  console.error("FEHLER: Keine <loc>-Einträge in der Sitemap gefunden.");
  process.exit(1);
}

const missing = [];

for (const match of locMatches) {
  const url = new URL(match[1]);
  const pathname = url.pathname;
  const expectedFile = pathname.endsWith("/")
    ? join(distDir, pathname, "index.html")
    : join(distDir, pathname);

  if (!existsSync(expectedFile)) {
    missing.push({ pathname, expectedFile });
  }
}

if (missing.length > 0) {
  console.error(`FEHLER: ${missing.length} Sitemap-URL(s) haben keine entsprechende gebaute Datei:`);
  for (const item of missing) {
    console.error(`  - ${item.pathname} -> erwartet: ${item.expectedFile}`);
  }
  process.exit(1);
}

console.log(`OK: Alle ${locMatches.length} Sitemap-URLs haben eine entsprechende gebaute Datei.`);
process.exit(0);
```

- [ ] **Step 3: `package.json` um das Skript ergänzen**

Füge in `package.json` im `"scripts"`-Block (nach der bestehenden `"deploy:dry-run"`-Zeile) hinzu:

```json
    "check:sitemap": "node scripts/check-sitemap-consistency.mjs"
```

- [ ] **Step 4: Skript gegen den echten Build laufen lassen (manueller Test)**

Run: `npm run check:sitemap`
Expected: `OK: Alle N Sitemap-URLs haben eine entsprechende gebaute Datei.` mit Exit-Code 0 — bestätigt, dass der aktuelle main-Stand konsistent ist (kein bekannter Fehler, aber der Check selbst muss grün laufen, um zu beweisen, dass er funktioniert).

- [ ] **Step 5: Negativtest — Skript mit absichtlich fehlender Datei prüfen**

Run:
```bash
mv dist/karriere/index.html dist/karriere/index.html.bak
npm run check:sitemap
```
Expected: Exit-Code 1, Fehlermeldung nennt `/karriere/` als fehlend.

Run (Aufräumen):
```bash
mv dist/karriere/index.html.bak dist/karriere/index.html
npm run check:sitemap
```
Expected: wieder Exit-Code 0 — bestätigt, dass der Negativtest echt war und nicht durch einen Bug im Skript selbst kam.

- [ ] **Step 6: Commit**

```bash
git add scripts/check-sitemap-consistency.mjs package.json
git commit -m "feat(seo): add sitemap-to-build consistency check script"
```

---

### Task 4: Neuer Wissensartikel — Rutschhemmklassen R9 bis R13

**Files:**
- Modify: `src/data/articles.ts` (neuer Artikel-Eintrag am Ende des Arrays)
- Modify: `src/data/industries.ts:39-43` (Lebensmittelindustrie `relatedArticles`)
- Modify: `src/data/industries.ts` (Molkerei `relatedArticles`, Zeile in Molkerei-Objekt)
- Modify: `src/data/industries.ts` (Brauerei `relatedArticles`)
- Test: `tests/content-cluster.test.ts` (neu, deckt Task 4-6 ab)

**Interfaces:**
- Konsumiert: `articleSchema` aus `src/lib/types.ts:71-93` (Pflichtfelder: `slug`, `title`, `seoTitle` min. 20 Zeichen, `description` min. 70 Zeichen, `h1` min. 10 Zeichen, `category`, `readTime`, `intro` min. 50 Zeichen, `sections` min. 3 Einträge mit `title`/`body` min. 20 Zeichen, `relatedServices`, `relatedIndustries`).
- Produziert: Artikel-Slug `rutschhemmklassen-r9-bis-r13-industrieboden`, den Task 7 (falls vorhanden) in Verlinkungen referenzieren kann.

**Kontext:** Recherchebeleg (siehe Design-Spec Block 2): R12/R13 V4/V6-Rutschhemmklassen sind ein wiederkehrender, konkreter Fachbegriff bei Ausschreibungen für Industrieböden in Nassbereichen. Der Artikel folgt exakt dem Muster des bestehenden Artikels "Warum Industrieböden in Molkereien versagen" (8 Abschnitte, technisch, endet mit CTA-Abschnitt).

- [ ] **Step 1: Schreibe den fehlschlagenden Test für alle drei neuen Artikel (Tasks 4-6 gemeinsam)**

Erstelle `tests/content-cluster.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { articles } from "../src/data/articles";
import { industries } from "../src/data/industries";

const newArticleSlugs = [
  "rutschhemmklassen-r9-bis-r13-industrieboden",
  "hohlkehle-sockelausbildung-industrieboden",
  "whg-abdichtung-industrieboden-pflicht",
];

describe("content cluster expansion", () => {
  it("adds exactly three new articles with valid slugs", () => {
    for (const slug of newArticleSlugs) {
      const article = articles.find((a) => a.slug === slug);
      expect(article, `expected article with slug "${slug}" to exist`).toBeDefined();
    }
  });

  it("every new article has at least 3 sections and a non-empty intro", () => {
    for (const slug of newArticleSlugs) {
      const article = articles.find((a) => a.slug === slug)!;
      expect(article.sections.length).toBeGreaterThanOrEqual(3);
      expect(article.intro.length).toBeGreaterThanOrEqual(50);
    }
  });

  it("every new article links back to at least one existing industry via relatedIndustries", () => {
    const industrySlugs = new Set(industries.map((i) => i.slug));
    for (const slug of newArticleSlugs) {
      const article = articles.find((a) => a.slug === slug)!;
      expect(article.relatedIndustries.length).toBeGreaterThan(0);
      for (const industrySlug of article.relatedIndustries) {
        expect(industrySlugs.has(industrySlug), `industry "${industrySlug}" referenced by "${slug}" must exist`).toBe(true);
      }
    }
  });

  it("R9-R13 article does not claim HACCP certification exists for floors (HACCP is a process standard, not a floor certificate)", () => {
    const article = articles.find((a) => a.slug === "rutschhemmklassen-r9-bis-r13-industrieboden")!;
    const fullText = article.intro + article.sections.map((s) => s.body ?? "").join(" ");
    expect(fullText).not.toMatch(/HACCP-zertifiziert/i);
  });

  it("at least two industries reference the new articles in relatedArticles, strengthening the content cluster", () => {
    const referencingIndustries = industries.filter((i) =>
      i.relatedArticles.some((slug) => newArticleSlugs.includes(slug)),
    );
    expect(referencingIndustries.length).toBeGreaterThanOrEqual(2);
  });
});
```

- [ ] **Step 2: Test ausführen, Fehlschlag bestätigen**

Run: `npx vitest run tests/content-cluster.test.ts`
Expected: FAIL bei "adds exactly three new articles" (keiner der drei Slugs existiert noch).

- [ ] **Step 3: Artikel zu `src/data/articles.ts` hinzufügen**

Füge am Ende des `articles`-Arrays in `src/data/articles.ts` (vor der schließenden `];`) hinzu:

```typescript
  {
    slug: "rutschhemmklassen-r9-bis-r13-industrieboden",
    title: "Rutschhemmklassen R9 bis R13 für Industrieböden",
    seoTitle: "Rutschhemmklassen R9-R13 Industrieboden erklärt | HSB Wissen",
    description:
      "Welche Rutschhemmklasse (R9 bis R13, mit V4/V6-Verdrängungsraum) für welchen Produktionsbereich vorgeschrieben ist und wie die Klassifizierung praktisch geprüft wird.",
    h1: "Rutschhemmklassen R9 bis R13: Welche Klasse für welchen Bereich?",
    category: "Technik",
    readTime: "8 Minuten",
    intro:
      "Die Rutschhemmklasse eines Industriebodens ist keine freie Wahl, sondern ergibt sich aus der Belastung des jeweiligen Arbeitsbereichs. Wer in Ausschreibungen oder Lastenheften auf R9, R12 oder R13 stößt, ohne die Systematik zu kennen, riskiert eine Fehlplanung, die erst bei der Abnahme auffällt.",
    sections: [
      {
        title: "Was die Rutschhemmklasse tatsächlich misst",
        body: "Die Rutschhemmklasse nach DIN 51130 beschreibt den Neigungswinkel, bei dem eine Testperson auf einer geölten schiefen Ebene noch sicheren Halt hat. Je höher die Klasse (R9 bis R13), desto größer der gemessene Neigungswinkel und desto rutschsicherer die Oberfläche unter Ölbelastung. Für Nassbereiche mit Wasser statt Öl gilt zusätzlich die Bewertungsgruppe A bis C nach DIN 51097.",
      },
      {
        title: "R9 bis R11: Trockene und leicht feuchte Bereiche",
        body: "R9 ist die niedrigste praxisrelevante Klasse und reicht für überwiegend trockene Lagerbereiche. R10 und R11 werden für Bereiche mit gelegentlicher Nässe oder leichten Verunreinigungen verwendet, etwa Zugangswege oder Nebenräume ohne permanente Nassbelastung. In produktionskritischen Kernbereichen reichen diese Klassen in der Regel nicht aus.",
      },
      {
        title: "R12 und R13: Produktions- und Nassbereiche",
        body: "R12 ist die häufigste geforderte Klasse für Produktionsbereiche mit regelmäßiger Nässe, Fett oder Reinigungsmitteln — etwa in der Lebensmittelverarbeitung oder bei Brauereien. R13 wird für besonders anspruchsvolle Bereiche mit dauerhaft hoher Nassbelastung und Fettanfall verlangt, etwa in Großküchen oder bei bestimmten Fleischverarbeitungsprozessen.",
      },
      {
        title: "Die Verdrängungsraum-Klassen V4 und V6",
        body: "Zusätzlich zur Rutschhemmklasse wird bei Nassbereichen ein Verdrängungsraum gefordert, der Flüssigkeit von der Standfläche wegleitet. V4 entspricht mindestens 4 Liter Verdrängungsraum pro Quadratmeter, V6 mindestens 6 Liter. Ein hoher Rutschhemmwert ohne ausreichenden Verdrängungsraum kann in der Praxis trotzdem zu Pfützenbildung und Rutschgefahr führen — beide Werte müssen zusammen betrachtet werden.",
      },
      {
        title: "Typischer Fehler: Eine Klasse für die ganze Fläche",
        body: "Ein häufiger Planungsfehler ist, eine einzige Rutschhemmklasse für eine gesamte Produktionshalle festzulegen, obwohl einzelne Bereiche unterschiedlich belastet werden. Der Bereich direkt an einer Reinigungsstation braucht typischerweise eine höhere Klasse als ein trockener Lagerbereich im selben Gebäude. Eine bereichsweise Klassifizierung vermeidet unnötige Mehrkosten in gering belasteten Zonen und schließt Sicherheitslücken in Hochrisikozonen.",
      },
      {
        title: "Wie die Klasse in der Praxis geprüft wird",
        body: "Die Prüfung erfolgt im Labor durch ein akkreditiertes Prüfinstitut nach dem in der jeweiligen Norm festgelegten Verfahren, nicht durch eine Sichtprüfung auf der Baustelle. Für ein Bauvorhaben bedeutet das: Das gewählte Bodensystem muss ein gültiges Prüfzertifikat für die geforderte Klasse besitzen — die Rutschhemmung ist eine Materialeigenschaft des gesamten Systems, nicht nur der obersten Schicht.",
      },
      {
        title: "Was bei nachträglicher Sanierung zu beachten ist",
        body: "Bei einer Sanierung eines bestehenden Bodens muss die geforderte Rutschhemmklasse neu erreicht werden, unabhängig davon, welche Klasse der Altbelag ursprünglich hatte. Verschleiß, wiederholte Reinigung oder mechanische Beanspruchung können die Rutschhemmung eines Altbelags über die Jahre verringern — eine reine optische Auffrischung ohne Systemwechsel löst dieses Problem nicht.",
      },
      {
        title: "Klassifizierung für Ihren Produktionsbereich klären",
        body: "Welche Rutschhemmklasse für welchen konkreten Bereich Ihres Betriebs zutrifft, hängt vom Belastungsprofil vor Ort ab. HSB bewertet Nutzung, Reinigungsroutine und Nassbelastung jedes Bereichs einzeln und legt die Systemwahl entsprechend fest, statt eine Standardklasse pauschal anzusetzen.",
      },
    ],
    relatedServices: ["keramische-industrieboeden", "pu-beton-industrieboden"],
    relatedIndustries: ["lebensmittelindustrie", "molkerei", "brauerei-getraenkeindustrie"],
  },
```

**Wichtig:** Bevor dieser Schritt final ist, den exakten `slug`-Wert der Brauerei-Industrie in `src/data/industries.ts` verifizieren (das Titel-Feld war `"Brauerei und Getränkeindustrie"` — den tatsächlichen `slug`-Wert aus der Datei lesen, nicht raten, und in `relatedIndustries` oben entsprechend eintragen).

- [ ] **Step 4: `relatedArticles` in den drei betroffenen Branchen ergänzen**

In `src/data/industries.ts`:

Bei der Lebensmittelindustrie (`relatedArticles`, aktuell Zeilen 39-43), füge den neuen Slug hinzu:
```typescript
    relatedArticles: [
      "pu-beton-oder-keramischer-industrieboden",
      "saeurefeste-fliesen-industrieboden",
      "entwaesserung-gefaelle-produktionsbereiche",
      "rutschhemmklassen-r9-bis-r13-industrieboden",
    ],
```

Bei Molkerei und Brauerei: das jeweilige `relatedArticles`-Array im Objekt suchen (per `grep -n "relatedArticles" src/data/industries.ts`, um die exakten Zeilennummern zu bestätigen) und denselben Slug ergänzen.

- [ ] **Step 5: Test erneut ausführen (nur den R9-R13-Teil)**

Run: `npx vitest run tests/content-cluster.test.ts -t "rutschhemmklassen"`
Expected: noch teilweise FAIL (die anderen zwei Artikel-Slugs fehlen noch — das ist erwartet, wird in Task 5/6 behoben).

- [ ] **Step 6: Astro-Build-Check**

Run: `npm run check`
Expected: 0 Fehler.

- [ ] **Step 7: Commit**

```bash
git add src/data/articles.ts src/data/industries.ts tests/content-cluster.test.ts
git commit -m "feat(content): add R9-R13 slip resistance class article"
```

---

### Task 5: Neuer Wissensartikel — Hohlkehle und Sockelausbildung

**Files:**
- Modify: `src/data/articles.ts` (neuer Artikel-Eintrag)
- Modify: `src/data/industries.ts` (mind. zwei Branchen mit Nassbereich, `relatedArticles`)

**Interfaces:**
- Konsumiert: identisch zu Task 4 (`articleSchema`).
- Produziert: Artikel-Slug `hohlkehle-sockelausbildung-industrieboden`.

**Kontext:** Recherchebeleg: Hohlkehlen-/Sockelausbildung wurde in der Konkurrenzrecherche als kritischer, oft unterschätzter Schwachpunkt genannt (Übergang Boden/Wand als mechanisch verwundbare Stelle, siehe Design-Spec).

- [ ] **Step 1: Artikel zu `src/data/articles.ts` hinzufügen**

Füge nach dem in Task 4 erstellten Artikel hinzu:

```typescript
  {
    slug: "hohlkehle-sockelausbildung-industrieboden",
    title: "Hohlkehle und Sockelausbildung im Industrieboden",
    seoTitle: "Hohlkehle & Sockel im Industrieboden: Detail entscheidet | HSB",
    description:
      "Warum die Hohlkehle am Wand-Boden-Übergang über die Standzeit eines Industriebodens entscheidet und welche Ausführungsfehler zu wiederkehrenden Schäden führen.",
    h1: "Hohlkehle und Sockelausbildung: Das unterschätzte Detail",
    category: "Technik",
    readTime: "7 Minuten",
    intro:
      "Der Übergang zwischen Boden und Wand — die Hohlkehle — wird in der Planung oft als Nebensache behandelt, ist aber in der Praxis eine der häufigsten Schadensursachen in Nassbereichen. Eine fehlerhafte Hohlkehle unterläuft die gesamte Abdichtungsleistung des Bodensystems.",
    sections: [
      {
        title: "Warum die Hohlkehle mechanisch die verwundbarste Stelle ist",
        body: "Am Wand-Boden-Übergang treffen zwei unterschiedliche Bauteile mit unterschiedlichem Bewegungsverhalten aufeinander. Ohne eine gerundete, kraftschlüssig ausgebildete Hohlkehle entsteht hier eine scharfe Kante, an der sich mechanische Spannungen konzentrieren — genau dort, wo Reinigungsgeräte, Hubwagen und Wasserstrahl am häufigsten auftreffen.",
      },
      {
        title: "Der typische Schadensverlauf bei fehlerhafter Ausführung",
        body: "Reißt die Abdichtung an der Hohlkehle auch nur minimal ein, wandert Feuchtigkeit hinter die Wandbekleidung oder unter den Bodenbelag. Von außen ist der Schaden zunächst unsichtbar; sichtbar wird er erst, wenn sich Fliesen lösen oder Putz an der Wand aufquillt — zu diesem Zeitpunkt ist die Durchfeuchtung meist bereits weit fortgeschritten.",
      },
      {
        title: "Materialanforderungen an die Hohlkehle",
        body: "Die Hohlkehle muss aus demselben oder einem systemkompatiblen Material wie die Hauptabdichtung bestehen, mit einem definierten Mindestradius (praxisüblich 3-5 cm), damit Reinigungsflüssigkeit ablaufen kann statt sich in einer scharfen Kante zu sammeln. Eine nachträglich aufgesetzte Silikonfuge ersetzt keine fachgerechte Hohlkehle — sie hält der mechanischen und chemischen Dauerbelastung in Produktionsbereichen nicht stand.",
      },
      {
        title: "Sockelhöhe und Stoßschutz",
        body: "Die Sockelausbildung sollte über die reine Abdichtung hinaus eine mechanisch belastbare Höhe erreichen, insbesondere in Bereichen mit Hubwagen- oder Gabelstaplerverkehr. Ein zu niedriger oder ungeschützter Sockel wird regelmäßig angefahren, wodurch die Abdichtung an genau dieser Stelle vorzeitig beschädigt wird — ein Schadensbild, das sich ohne baulichen Stoßschutz wiederholt einstellt.",
      },
      {
        title: "Prüfpunkte bei der Bauabnahme",
        body: "Bei der Abnahme sollte die Hohlkehle auf durchgehende Ausführung ohne Unterbrechung geprüft werden, insbesondere an Ecken, Rohrdurchführungen und Türlaibungen — Stellen, an denen die Ausführung erfahrungsgemäß am häufigsten unvollständig bleibt. Eine lückenlose fotografische Dokumentation der Hohlkehle vor der Inbetriebnahme erleichtert spätere Gewährleistungsfragen erheblich.",
      },
      {
        title: "Hohlkehlen-Ausführung für Ihren Bodenaufbau prüfen lassen",
        body: "Ob eine bestehende Hohlkehle noch funktionsfähig ist oder bereits Schwachstellen zeigt, lässt sich meist erst bei genauer Prüfung vor Ort feststellen. HSB bewertet den Zustand der Detailanschlüsse als festen Bestandteil jeder Bodenanalyse, nicht als nachgelagerten Punkt.",
      },
    ],
    relatedServices: ["industrieboden-saeureschutz", "keramische-industrieboeden"],
    relatedIndustries: ["lebensmittelindustrie", "brauerei-getraenkeindustrie"],
  },
```

**Wichtig:** exakten `slug`-Wert der Brauerei-Branche in `src/data/industries.ts` verifizieren, bevor `relatedIndustries` final eingetragen wird (siehe Hinweis in Task 4, Step 3).

- [ ] **Step 2: Test ausführen**

Run: `npx vitest run tests/content-cluster.test.ts -t "hohlkehle"`
Expected: teilweise PASS für diesen Artikel-Slug (der dritte Slug aus Task 6 fehlt noch).

- [ ] **Step 3: `relatedArticles` in Lebensmittelindustrie und Brauerei ergänzen**

Analog zu Task 4, Step 4 — den neuen Slug `hohlkehle-sockelausbildung-industrieboden` in beiden Branchen-Objekten zum `relatedArticles`-Array hinzufügen.

- [ ] **Step 4: Astro-Build-Check**

Run: `npm run check`
Expected: 0 Fehler.

- [ ] **Step 5: Commit**

```bash
git add src/data/articles.ts src/data/industries.ts
git commit -m "feat(content): add hohlkehle/sockel detail article"
```

---

### Task 6: Neuer Wissensartikel — WHG-Abdichtung: Wann ist sie Pflicht

**Files:**
- Modify: `src/data/articles.ts` (neuer Artikel-Eintrag)
- Modify: `src/data/industries.ts` (Chemieindustrie, Pharmaindustrie `relatedArticles`)

**Interfaces:**
- Konsumiert: identisch zu Task 4/5.
- Produziert: Artikel-Slug `whg-abdichtung-industrieboden-pflicht`.

**Kontext:** WHG (Wasserhaushaltsgesetz) ist bereits im Content der Chemieindustrie-Seite präsent, aber ohne eigenständigen, tiefergehenden Artikel. Rechtlicher Anlass zur Suche macht das zu einem eigenständigen Cluster-Thema.

- [ ] **Step 1: Artikel zu `src/data/articles.ts` hinzufügen**

```typescript
  {
    slug: "whg-abdichtung-industrieboden-pflicht",
    title: "WHG-Abdichtung für Industrieböden — wann ist sie Pflicht",
    seoTitle: "WHG-Abdichtung Industrieboden: Pflicht oder Kür? | HSB Wissen",
    description:
      "Wann eine WHG-konforme Bodenabdichtung nach Wasserhaushaltsgesetz für Ihren Produktionsbereich rechtlich vorgeschrieben ist und was bei der Systemwahl zu beachten ist.",
    h1: "WHG-Abdichtung für Industrieböden: Wann ist sie Pflicht?",
    category: "Recht & Technik",
    readTime: "8 Minuten",
    intro:
      "Das Wasserhaushaltsgesetz (WHG) verpflichtet Betreiber bestimmter Anlagen zum Schutz von Boden und Grundwasser vor wassergefährdenden Stoffen. Für Industrieböden bedeutet das: In bestimmten Bereichen ist eine flüssigkeitsdichte, geprüfte Abdichtung keine optionale Zusatzleistung, sondern eine rechtliche Anforderung mit Nachweispflicht.",
    sections: [
      {
        title: "Was das WHG für Bodenflächen verlangt",
        body: "Das WHG und die zugehörige Anlagenverordnung (AwSV) verpflichten Betreiber von Anlagen zum Umgang mit wassergefährdenden Stoffen dazu, dass keine solchen Stoffe in Boden oder Grundwasser gelangen können. Für den Boden bedeutet das eine flüssigkeitsundurchlässige, beständige und rissüberbrückende Abdichtung, die dem jeweiligen Gefährdungspotenzial standhält.",
      },
      {
        title: "Wann die Pflicht konkret greift",
        body: "Maßgeblich ist nicht die Branche als solche, sondern ob am jeweiligen Standort mit wassergefährdenden Stoffen umgegangen wird — etwa Lagerung, Abfüllung oder Verarbeitung von Chemikalien, Reinigungsmitteln in relevanter Menge oder bestimmten Betriebsstoffen. Die konkrete Einstufung und die daraus folgenden Anforderungen ergeben sich aus der Gefährdungsstufe der jeweiligen Anlage nach AwSV, die im Einzelfall behördlich oder durch einen Sachverständigen zu klären ist.",
      },
      {
        title: "Prüfnachweis statt Vertrauen auf die Optik",
        body: "Eine WHG-konforme Abdichtung muss durch einen bauaufsichtlich anerkannten Nachweis (z. B. eine allgemeine bauaufsichtliche Zulassung oder Prüfzeugnis) belegt sein, nicht durch eine augenscheinlich dichte Oberfläche. Optisch unauffällige Böden können bei genauerer Prüfung Undichtigkeiten an Fugen, Durchdringungen oder Rand-anschlüssen aufweisen, die für die WHG-Konformität entscheidend sind.",
      },
      {
        title: "Typische Schwachstellen bei Bestandsflächen",
        body: "Bei nachträglich geprüften Bestandsflächen zeigen sich Schwachstellen meist an denselben Stellen: Fugenübergänge, Rohrdurchführungen, Anschlüsse an Aufkantungen und Übergänge zu angrenzenden, nicht WHG-pflichtigen Bereichen. Eine punktuelle Nachbesserung ohne Systemprüfung schließt oft nur die sichtbare Stelle, nicht die eigentliche Undichtigkeitsursache.",
      },
      {
        title: "Dokumentationspflicht und Wiederkehrende Prüfung",
        body: "Je nach Gefährdungsstufe der Anlage sind wiederkehrende Prüfungen durch Sachverständigenorganisationen vorgeschrieben. Eine lückenlose Dokumentation der ursprünglichen Ausführung — verwendete Materialien, Prüfzeugnisse, Ausführungsfotos — erleichtert diese wiederkehrenden Prüfungen erheblich und vermeidet, dass bei jeder Prüfung erneut Grundlagenfragen geklärt werden müssen.",
      },
      {
        title: "Einstufung und Systemwahl für Ihren Standort klären",
        body: "Ob und in welchem Umfang eine WHG-konforme Abdichtung für einen konkreten Bereich erforderlich ist, hängt von der individuellen Anlagen- und Gefährdungssituation ab und ist keine pauschale Aussage. HSB bewertet die Anforderungen je Produktionsbereich gemeinsam mit den vorhandenen Nachweisen und legt die Systemwahl entsprechend fest.",
      },
    ],
    relatedServices: ["industrieboden-saeureschutz", "whg-abdichtung-industrieboden"],
    relatedIndustries: ["chemieindustrie", "pharmaindustrie"],
  },
```

**Wichtig:** exakte `slug`-Werte für Chemieindustrie und Pharmaindustrie in `src/data/industries.ts` sowie den exakten Service-Slug für WHG-Abdichtung in `src/data/services.ts` verifizieren, bevor `relatedServices`/`relatedIndustries` final eingetragen werden — nicht aus dem Plan-Text übernehmen, falls die tatsächlichen Slugs abweichen.

- [ ] **Step 2: Vollständigen Content-Cluster-Test ausführen**

Run: `npx vitest run tests/content-cluster.test.ts`
Expected: PASS (alle fünf Tests grün — alle drei Artikel existieren jetzt).

- [ ] **Step 3: `relatedArticles` in Chemieindustrie und Pharmaindustrie ergänzen**

Analog zu Task 4/5 — neuen Slug `whg-abdichtung-industrieboden-pflicht` in beiden Branchen-Objekten ergänzen.

- [ ] **Step 4: Vollständigen Testlauf und Build ausführen**

Run: `npm run check && npx vitest run tests/content-cluster.test.ts tests/content-meta.test.ts tests/article-attribution.test.ts && npm run build`
Expected: alle Checks grün, Build zeigt 43 Seiten (40 bestehende + 3 neue Wissensartikel).

- [ ] **Step 5: Sitemap-Konsistenz-Check gegen den neuen Stand laufen lassen**

Run: `npm run check:sitemap`
Expected: `OK: Alle 43 Sitemap-URLs haben eine entsprechende gebaute Datei.`

- [ ] **Step 6: Commit**

```bash
git add src/data/articles.ts src/data/industries.ts
git commit -m "feat(content): add WHG containment article, complete cluster expansion"
```

---

### Task 7: Owner-Checkliste aktualisieren (Doku, kein Code)

**Files:**
- Modify: `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`

**Interfaces:**
- Konsumiert: nichts.
- Produziert: nichts — reine Dokumentationskorrektur, keine anderen Tasks hängen davon ab.

**Kontext:** Die bestehende Datei hat Stand 15.07. und spricht von einem "noch nicht gemergten" Consent-Cutover — das ist mittlerweile überholt (GA4-Consent-Gate ist seit heute produktiv live, siehe `src/lib/analytics.ts`). Die Datei muss den korrigierten Stand zeigen, sonst verlässt sich ein zukünftiger Leser auf einen falschen Status.

- [ ] **Step 1: Aktuellen Inhalt lesen**

Lies `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md` komplett (aktuell 27 Zeilen).

- [ ] **Step 2: Status-Zeile und "Nachweisbarer Code-Stand"-Abschnitt korrigieren**

Ändere die Zeile:
```
Status: `ga4-basic-consent-cutover-in-pr; external-owner-verification-open`
Stand: 2026-07-15
```
zu:
```
Status: `ga4-basic-consent-cutover-live; external-owner-verification-open`
Stand: 2026-08-03
```

Ändere im Abschnitt "Nachweisbarer Code-Stand" den Satz:
```
- Die GA4 Measurement ID ist im Quellcode vorhanden, aber die neue Basic-Consent-
  Implementierung ist noch nicht in `main` oder Produktion gemergt.
```
zu:
```
- Die GA4 Measurement ID ist im Quellcode vorhanden. Die Basic-Consent-
  Implementierung ist in `main` gemergt und per Production-Deploy (2026-08-03)
  live; verifiziert per `curl -sI https://www.hsb-boden.de` (siehe Security-Header
  im Response, `src/lib/analytics.ts` Consent-Gate).
```

Die "Externe Owner-Gates"-Liste bleibt inhaltlich unverändert (DebugView-Prüfung, Key-Event-Markierung, GSC-Property-Prüfung sind weiterhin offen — nur der Code-Status wird korrigiert, nicht die Owner-Aufgaben).

- [ ] **Step 3: Commit**

```bash
git add docs/analytics/GA4_GTM_GSC_MAX_READINESS.md
git commit -m "docs: correct GA4 consent cutover status to reflect live deploy"
```

---

## Self-Review (durchgeführt)

**Spec-Abdeckung:** Block 1 Punkt 1 (Meta-Title-Audit) → Task 1. Block 1 Punkt 2 (Autor-Feld) → Task 2 (JSON-LD-Feld war bereits vorhanden, sichtbare Box ist der tatsächlich fehlende Teil). Block 1 Punkt 3 (Sitemap-Check) → Task 3. Block 1 Punkt 4 (Owner-Checkliste) → Task 7. Block 2 (3 Artikel) → Task 4, 5, 6. Block 3 bleibt bewusst außerhalb dieses Plans (Owner-Gates, siehe Spec).

**Placeholder-Scan:** Keine TBD/TODO-Marker. Alle Code-Blöcke sind vollständig ausformuliert, keine "ähnlich wie oben"-Verweise.

**Bekannte Unsicherheit, die der Implementierer selbst auflösen muss:** Die exakten `slug`-Werte für Brauerei/Chemieindustrie/Pharmaindustrie in `industries.ts` sowie der WHG-Service-Slug in `services.ts` wurden im Plan nicht durch einen abschließenden `grep` verifiziert (nur der Titel "Brauerei und Getränkeindustrie" ist bekannt, der Slug wurde plausibel als `brauerei-getraenkeindustrie` angenommen). Jeder Task, der einen dieser Slugs referenziert, enthält einen expliziten Hinweis, den echten Wert vor dem Eintragen zu verifizieren — dies ist bewusst kein Platzhalter, sondern eine Anweisung an den Implementierer, mit einem Tool nachzuschauen statt zu raten.
