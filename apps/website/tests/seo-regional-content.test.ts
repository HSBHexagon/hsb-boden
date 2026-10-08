import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { regionalGuides } from "../src/data/regionalGuides";
import { getArticles, getIndustries, getServices } from "../src/lib/content";

const expectedSlugs = [
  "baden-wuerttemberg", "bayern", "hamburg", "hessen", "niedersachsen",
  "nrw", "rheinland-pfalz", "sachsen-anhalt", "thueringen",
];

describe("regional content engineering guardrails", () => {
  it("covers all nine intended regions exactly once", () => {
    expect(Object.keys(regionalGuides).sort()).toEqual(expectedSlugs.sort());
  });

  it("uses differentiated engineering guidance, not geographic doorway boilerplate", () => {
    const summaries = new Set<string>();
    const focalTopics = new Set<string>();
    for (const guide of Object.values(regionalGuides)) {
      expect(guide.summary.length).toBeGreaterThan(150);
      expect(guide.focus.length).toBeGreaterThan(35);
      expect(guide.diagnosticQuestions).toHaveLength(3);
      expect(new Set(guide.diagnosticQuestions).size).toBe(3);
      expect(guide.diagnosticQuestions.every((question) => question.length >= 58)).toBe(true);
      expect(guide.summary).not.toMatch(/kurze Wege|schnelle Reaktionszeiten|bereits realisiert|Standort in (?!Gronau)/i);
      summaries.add(guide.summary);
      focalTopics.add(guide.focus);
    }
    expect(summaries.size).toBe(9);
    expect(focalTopics.size).toBe(9);
  });

  it("links only to existing industry, service and knowledge URLs", () => {
    const services = new Set(getServices().map((x) => x.slug));
    const industries = new Set(getIndustries().map((x) => x.slug));
    const articles = new Set(getArticles().map((x) => x.slug));
    for (const [slug, guide] of Object.entries(regionalGuides)) {
      for (const linked of guide.serviceSlugs) expect(services.has(linked), `${slug} / ${linked}`).toBe(true);
      for (const linked of guide.industrySlugs) expect(industries.has(linked), `${slug} / ${linked}`).toBe(true);
      expect(articles.has(guide.articleSlug), `${slug} / ${guide.articleSlug}`).toBe(true);
    }
  });

  it.each(expectedSlugs)("%s delegates substantive text to the regional guidance", (slug) => {
    const file = readFileSync(join(process.cwd(), "src/pages/standorte", slug, "index.astro"), "utf8");
    expect(file).toContain(`<RegionalDecisionGuide slug="${slug}" />`);
    expect(file).toContain(`path="/standorte/${slug}/"`);
    expect(file).toContain("buildBreadcrumbJsonLd");
    expect(file).not.toMatch(/Regionale Präsenz|Kurze Wege|Schnelle Reaktionszeiten/);
  });

  it("does not invent regional offices or publish unapproved regional customer claims", () => {
    const component = readFileSync(join(process.cwd(), "src/components/sections/RegionalDecisionGuide.astro"), "utf8");
    expect(component).toContain("Unternehmenssitz in Gronau");
    expect(component).toContain("getServices");
    expect(component).toContain("getIndustries");
    expect(component).toContain("getArticles");
    expect(component).not.toContain("LocalBusiness");
  });
});
