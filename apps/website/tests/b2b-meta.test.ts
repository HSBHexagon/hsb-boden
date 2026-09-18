import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { getAllPublicPages, getIndustries, getServices } from "../src/lib/content";
import { site } from "../src/data/site";
import { homepageFaqs } from "../src/data/homepageFaqs";

const HANDWERKER_PATTERNS = [/€\s*\/?\s*m²/i, /pro m²/i, /Quadratmeterpreis/i, /qm-Preis/i, /deutlich günstiger/i, /billig/i, /preiswert/i];

describe("B2B-Positionierung der Metadaten", () => {
  it("nennt in Titles und Descriptions keine Quadratmeterpreise oder Handwerker-Floskeln", () => {
    const blobs = [
      ...getAllPublicPages().flatMap((page) => [page.seoTitle, page.description, page.h1]),
      ...getIndustries().flatMap((industry) => [industry.seoTitle, industry.description]),
      ...getServices().flatMap((service) => [service.seoTitle, service.description, ...service.faqs.map((faq) => faq.answer)]),
      ...homepageFaqs.flatMap((faq) => [faq.question, faq.answer]),
    ];
    for (const blob of blobs) for (const pattern of HANDWERKER_PATTERNS) expect(blob).not.toMatch(pattern);
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
