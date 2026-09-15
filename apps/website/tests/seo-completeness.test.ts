import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { buildWebSiteJsonLd } from "../src/lib/schema";
import { getAllPublicPages } from "../src/lib/content";
import { site } from "../src/data/site";

describe("WebSite-Schema", () => {
  it("liefert ein valides WebSite-JSON-LD mit Site Name und kanonischer Domain", () => {
    const graph = buildWebSiteJsonLd();

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@type"]).toBe("WebSite");
    expect(graph["@context"]).toBe("https://schema.org");
    expect(graph.name).toBeTruthy();
    expect(graph.url).toBe(site.domain);
  });

  it("erfindet weder Bewertungen noch eine nicht vorhandene Suchfunktion", () => {
    const blob = JSON.stringify(buildWebSiteJsonLd());

    expect(blob).not.toContain("aggregateRating");
    expect(blob).not.toContain("SearchAction");
    expect(blob).not.toContain("review");
  });

  it("ist auf der Startseite eingebunden", () => {
    const source = readFileSync(
      join(process.cwd(), "src/pages/index.astro"),
      "utf8",
    );

    expect(source).toContain("buildWebSiteJsonLd");
    expect(source).toMatch(/jsonLd=\{\[[^\]]*buildWebSiteJsonLd\(\)/s);
  });
});

describe("Sitemap-Vollstaendigkeit", () => {
  // Die Rechtsseiten sind gebaut, indexierbar und im Footer verlinkt — sie
  // gehoeren damit in die Sitemap. Zuvor fehlten sie, weil getAllPublicPages()
  // nur die Content-Routen kannte.
  it("fuehrt Impressum und Datenschutz als oeffentliche Seiten", () => {
    const paths = getAllPublicPages().map((page) => page.canonicalPath);

    expect(paths).toContain("/impressum/");
    expect(paths).toContain("/datenschutz/");
  });

  it("haelt jede oeffentliche Route eindeutig", () => {
    const paths = getAllPublicPages().map((page) => page.canonicalPath);

    expect(new Set(paths).size).toBe(paths.length);
  });

  it("vergibt jeden SEO-Title genau einmal", () => {
    const titles = getAllPublicPages().map((page) => page.seoTitle);
    const duplicates = titles.filter(
      (title, index) => titles.indexOf(title) !== index,
    );

    expect(duplicates).toEqual([]);
  });
});
