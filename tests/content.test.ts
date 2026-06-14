import { describe, expect, it } from "vitest";
import {
  getAllPublicPages,
  getPublicReferences,
  validateSiteContent,
} from "../src/lib/content";
import { services } from "../src/data/services";
import { industries } from "../src/data/industries";
import { articles } from "../src/data/articles";

describe("site content contract", () => {
  it("validates the complete dateibasiert content model", () => {
    const result = validateSiteContent();

    expect(result.success).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("generates SEO-ready public pages with one h1, title, description, and canonical URL", () => {
    const pages = getAllPublicPages();

    expect(pages.length).toBeGreaterThanOrEqual(22);
    for (const page of pages) {
      expect(page.h1).toBeTruthy();
      expect(page.seoTitle.length).toBeGreaterThan(20);
      expect(page.description.length).toBeGreaterThan(70);
      expect(page.canonicalPath.startsWith("/")).toBe(true);
      expect(page.canonicalPath.endsWith("/")).toBe(true);
    }
  });

  it("never exposes exact locations or logos for unapproved references", () => {
    const references = getPublicReferences();

    expect(references.length).toBeGreaterThan(0);
    for (const reference of references) {
      if (reference.approvalStatus !== "approved") {
        expect(reference.displayName).toBe(reference.anonymousName);
        expect(reference.logo).toBeUndefined();
        expect(reference.canShowExactLocation).toBe(false);
      }
    }
  });
});

describe("content hardening (Phase 1)", () => {
  it("säureschutz nennt WHG und Vinylester im Systemtext", () => {
    const s = services.find((x) => x.slug === "industrieboden-saeureschutz")!;
    expect(s.systemSolution).toMatch(/WHG/);
    expect(s.systemSolution).toMatch(/Vinylester/);
    expect(s.technicalRequirements).toContain("WHG-Konformität");
  });

  it("keramik nennt Rüttelverlegetechnik und DIN EN 14411", () => {
    const s = services.find((x) => x.slug === "keramische-industrieboeden")!;
    expect(s.systemSolution).toMatch(/Rüttelverlege/);
    expect(s.secondaryKeywords.some((k) => /14411/.test(k))).toBe(true);
  });

  it("chemie nennt WHG-Paragrafen und ESD", () => {
    const c = industries.find((x) => x.slug === "chemieindustrie")!;
    const blob = JSON.stringify(c);
    expect(blob).toMatch(/§\s?62/);
    expect(blob).toMatch(/ESD/);
  });

  it("pharma nennt ISO 14644 und GMP/FDA", () => {
    const p = industries.find((x) => x.slug === "pharmaindustrie")!;
    const blob = JSON.stringify(p);
    expect(blob).toMatch(/14644/);
    expect(blob).toMatch(/GMP/);
  });

  it("artikel-sections sind objekte mit title", () => {
    for (const a of articles)
      for (const s of a.sections) expect(typeof s.title).toBe("string");
  });

  it("molkerei-artikel nennt Epoxidharz gegen Milchsäure", () => {
    const a = articles.find((x) => x.slug === "warum-industrieboeden-in-molkereien-versagen")!;
    expect(JSON.stringify(a.sections)).toMatch(/Epoxidharz/);
  });
});
