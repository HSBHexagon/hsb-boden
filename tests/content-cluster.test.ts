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
      article!.intro + article!.sections.map((s) => s.body ?? "").join(" ");
    expect(fullText).not.toMatch(/HACCP-zertifiziert/i);
  });

  it("has the ESD/explosion protection article with required sections", () => {
    const article = articles.find(
      (a) => a.slug === "esd-ableitfaehigkeit-explosionsschutz-industrieboden",
    );
    expect(article).toBeDefined();
    expect(article!.sections.length).toBeGreaterThanOrEqual(6);
    expect(article!.relatedIndustries).toContain("chemieindustrie");
  });
});
