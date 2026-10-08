import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { articles } from "../src/data/articles";
import { getAllPublicPages } from "../src/lib/content";

describe("Fachartikel: Nachweise, modulare Daten und interne SEO-Pfade", () => {
  it("verliert beim Aufteilen der Inhaltsdateien keine Artikel", () => {
    expect(articles).toHaveLength(12);
    const slugs = articles.map((a) => a.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
    const publicPaths = new Set(getAllPublicPages().map((x) => x.canonicalPath));
    for (const slug of slugs) expect(publicPaths.has(`/wissen/${slug}/`), slug).toBe(true);
  });

  it("hält beide TypeScript-Datenmodule unter der vereinbarten 500-Zeilen-Grenze", () => {
    for (const file of ["articles.ts", "articles-supplemental.ts"]) {
      const source = readFileSync(join(process.cwd(), "src/data", file), "utf8");
      expect(source.split("\n").length, file).toBeLessThan(500);
    }
  });

  it("kennzeichnet unbelegte Beispiele ausdrücklich als hypothetische Szenarien", () => {
    const scenarios = articles.flatMap((a) => a.sections.filter((s) => s.title.startsWith("Planungsszenario")));
    expect(scenarios).toHaveLength(3);
    for (const example of scenarios) {
      expect(example.body).toContain("kein bestätigtes Referenzprojekt");
    }
  });

  it("enthält in den überarbeiteten Schwerpunktartikeln keine pauschalen Garantien", () => {
    const coreSlugs = [
      "pu-beton-oder-keramischer-industrieboden",
      "warum-industrieboeden-in-molkereien-versagen",
      "saeurefeste-fliesen-industrieboden",
      "entwaesserung-gefaelle-produktionsbereiche",
      "sanierung-ohne-produktionsstillstand",
    ];
    const covered = articles.filter((a) => coreSlugs.includes(a.slug));
    expect(covered).toHaveLength(coreSlugs.length);
    const text = covered.flatMap((a) => a.sections.map((section) => section.body)).join(" ");
    expect(text).not.toContain("pH-Werten von 0 bis 14");
    expect(text).not.toContain("100%ige Füllung");
    expect(text).not.toContain("PMMA-Harze sind beispielsweise bereits 60 Minuten");
    expect(text).not.toContain("vollständigen Schutz");
  });
});
