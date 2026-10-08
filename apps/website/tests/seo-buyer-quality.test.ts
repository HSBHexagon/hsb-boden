import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { technicalDecisionGuides } from "../src/data/technicalDecisionGuides";
import { getAllPublicPages } from "../src/lib/content";
import { regionalGuides } from "../src/data/regionalGuides";

const regions = Object.keys(regionalGuides);
const sectors = ["molkerei", "brauerei-getraenkeindustrie", "chemieindustrie"];
const services = ["keramische-industrieboeden", "pu-beton-industrieboden", "whg-abdichtung-industrieboden"];

describe("SEO intent and internal-link regression", () => {
  it("aligns rendered region descriptions with the sitemap content registry", () => {
    for (const slug of regions) {
      const src = readFileSync(join(process.cwd(), "src/pages/standorte", slug, "index.astro"), "utf8");
      const desc = src.match(/\bdescription="([^"]+)"/)?.[1];
      const registered = getAllPublicPages().find((x) => x.canonicalPath === `/standorte/${slug}/`);
      expect(registered, slug).toBeDefined();
      expect(registered?.description, slug).toBe(desc);
      expect(src).toContain("buildRegionalServiceJsonLd");
      expect(src).toContain("buildBreadcrumbJsonLd");
      expect(src).not.toContain("LocalBusiness");
    }
  });

  it("adds a relevant buyer checklist to the existing service and industry routes", () => {
    const servicePage = readFileSync(join(process.cwd(), "src/pages/leistungen/[slug].astro"), "utf8");
    const industryPage = readFileSync(join(process.cwd(), "src/pages/branchen/[slug].astro"), "utf8");
    expect(servicePage).toContain("<TechnicalDecisionGuide slug={service.slug} />");
    expect(industryPage).toContain("<TechnicalDecisionGuide slug={industry.slug} />");
  });

  it("includes evidence-safe, distinct checklists and valid related URLs for priority pages", () => {
    const knownPaths = new Set(getAllPublicPages().map((p) => p.canonicalPath));
    expect(Object.keys(technicalDecisionGuides).sort()).toEqual([...sectors, ...services].sort());
    for (const [slug, guide] of Object.entries(technicalDecisionGuides)) {
      expect(guide.requiredInputs).toHaveLength(3);
      expect(new Set(guide.requiredInputs).size).toBe(3);
      expect(guide.intro.length, slug).toBeGreaterThan(90);
      expect(guide.decisionRule.length, slug).toBeGreaterThan(90);
      expect(knownPaths.has(guide.relatedUrl), `${slug}: ${guide.relatedUrl}`).toBe(true);
      expect(JSON.stringify(guide)).not.toMatch(/garantiert|100%|immer (?:beständig|sicher)/i);
    }
  });

  it("keeps noindex or conversion-only pages outside the XML sitemap", () => {
    const page = getAllPublicPages().find((x) => x.canonicalPath === "/danke-projektanfrage/");
    expect(page).toBeDefined();
    const xmlSource = readFileSync(join(process.cwd(), "src/pages/sitemap.xml.ts"), "utf8");
    expect(xmlSource).toContain('page.canonicalPath !== "/danke-projektanfrage/"');
  });
});
