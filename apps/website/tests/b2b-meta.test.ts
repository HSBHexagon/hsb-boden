import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { getAllPublicPages, getArticles, getIndustries, getServices } from "../src/lib/content";
import { site } from "../src/data/site";
import { homepageFaqs } from "../src/data/homepageFaqs";

const HANDWERKER_PATTERNS = [/€\s*\/?\s*m²/i, /pro m²/i, /Quadratmeterpreis/i, /qm-Preis/i, /deutlich günstiger/i, /billig/i, /preiswert/i];

// Site-weite Sperrliste für Fließtext und Komponenten-Copy: Preisversprechen und
// generische Handwerker-Floskeln, die der B2B-Ingenieurbau-Positionierung
// widersprechen. "pro Quadratmeter" bleibt als technische Einheit (Verdrängungsraum
// V4/V6 in l/m²) erlaubt und wird deshalb bewusst nicht gesperrt.
const SITE_WIDE_PATTERNS = [
  ...HANDWERKER_PATTERNS,
  /Festpreis/i,
  /kostenlos/i,
  /unverbindlich/i,
  /Meisterbetrieb/i,
  /Handwerker/i,
  /Kostenvoranschlag/i,
];

function collectAstroFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const fullPath = join(directory, entry);
    if (statSync(fullPath).isDirectory()) return collectAstroFiles(fullPath);
    return entry.endsWith(".astro") ? [fullPath] : [];
  });
}

describe("B2B-Positionierung der Metadaten", () => {
  it("nennt in Titles und Descriptions keine Quadratmeterpreise oder Handwerker-Floskeln", () => {
    const blobs = [
      ...getAllPublicPages().flatMap((page) => [page.seoTitle, page.description, page.h1]),
      ...getIndustries().flatMap((industry) => [industry.seoTitle, industry.description]),
      ...getServices().flatMap((service) => [service.seoTitle, service.description, ...service.faqs.map((faq) => faq.answer)]),
      ...homepageFaqs.flatMap((faq) => [faq.question, faq.answer]),
    ];
    for (const blob of blobs) for (const pattern of SITE_WIDE_PATTERNS) expect(blob).not.toMatch(pattern);
  });

  it("hält Wissensartikel frei von Preisversprechen und Handwerker-Floskeln", () => {
    const blobs = getArticles()
      .flatMap((article) => [
        article.title,
        article.intro,
        ...article.sections.flatMap((section) => [section.title, section.body]),
      ])
      .filter((blob): blob is string => typeof blob === "string");
    expect(blobs.length).toBeGreaterThan(0);
    for (const blob of blobs) {
      for (const pattern of SITE_WIDE_PATTERNS) expect(blob, blob.slice(0, 80)).not.toMatch(pattern);
    }
  });

  it("hält die sichtbare Copy aller Seiten und Komponenten frei von Handwerker-Floskeln", () => {
    const files = [
      ...collectAstroFiles(join(process.cwd(), "src/pages")),
      ...collectAstroFiles(join(process.cwd(), "src/components")),
      ...collectAstroFiles(join(process.cwd(), "src/layouts")),
    ];
    expect(files.length).toBeGreaterThan(0);
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      for (const pattern of SITE_WIDE_PATTERNS) expect(source, file).not.toMatch(pattern);
    }
  });

  it("hält neue statische Titles unter 60 und Descriptions unter 160 Zeichen", () => {
    const targets = ["/", "/leistungen/", "/kontakt/", "/beanspruchungs-check/"];
    for (const page of getAllPublicPages().filter((item) => targets.includes(item.canonicalPath))) {
      expect(page.seoTitle.length, page.canonicalPath).toBeLessThanOrEqual(60);
      expect(page.description.length, page.canonicalPath).toBeLessThanOrEqual(160);
    }
    expect(site.defaultTitle.length).toBeLessThanOrEqual(60);
    expect(site.defaultDescription.length).toBeLessThanOrEqual(160);
  });

  it("positioniert die Startseite auf Ingenieurbau, Rüttelkeramik und Säureschutz", () => {
    expect(site.defaultTitle).toMatch(/Ingenieurbau/);
    expect(site.defaultTitle).toMatch(/Rüttelkeramik/);
    expect(site.defaultTitle).toMatch(/Säureschutz/);
    expect(getAllPublicPages()[0].seoTitle).toBe(site.defaultTitle);
  });

  it("hält Kontaktseite und Content-Registry auf demselben Title", () => {
    const source = readFileSync(join(process.cwd(), "src/pages/kontakt/index.astro"), "utf8");
    const registry = getAllPublicPages().find((page) => page.canonicalPath === "/kontakt/");
    expect(registry).toBeDefined();
    expect(source).toContain(`title="${registry?.seoTitle}"`);
  });
});
