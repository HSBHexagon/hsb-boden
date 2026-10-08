import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { site } from "../src/data/site";
import { industries } from "../src/data/industries";
import { services } from "../src/data/services";
import { homeAlternates, languages } from "../src/lib/i18n";
import { getAllPublicPages } from "../src/lib/content";

const lookup = (slug: string) => {
  const result = [...services, ...industries].find((entry) => entry.slug === slug);
  if (!result) throw new Error(`Missing content slug: ${slug}`);
  return result;
};

describe("SEO release: specific search intent without unsupported promises", () => {
  it("uses industrial flooring in the homepage title", () => {
    expect(site.defaultTitle).toMatch(/Industrieböden/);
    expect(site.defaultTitle).toContain("Säureschutz");
  });

  it.each([
    ["molkerei", "Industrieboden Molkerei"],
    ["brauerei-getraenkeindustrie", "Industrieboden Brauerei"],
    ["chemieindustrie", "Industrieboden Chemieindustrie"],
    ["lebensmittelindustrie", "Industrieboden Lebensmittelindustrie"],
    ["whg-abdichtung-industrieboden", "WHG-Bodenabdichtung"],
    ["industrieboden-saeureschutz", "Säureschutz"],
    ["bodensanierung-laufender-betrieb", "Industrieboden sanieren"],
  ])("targets %s with clear buyer intent", (slug, phrase) => {
    expect(lookup(slug).seoTitle).toContain(phrase);
  });

  it("avoids unsupported all-media, all-duration and no-stop guarantees", () => {
    const chemical = services.find((entry) => entry.slug === "industrieboden-saeureschutz")!;
    const renewal = services.find((entry) => entry.slug === "bodensanierung-laufender-betrieb")!;
    const blob = JSON.stringify({ chemical, renewal });
    expect(blob).not.toMatch(/pH-Bereiche von 0[–-]14|> 20 Jahre|ohne Stillstand|Staubfreie Untergrundbearbeitung|garantiert/);
    expect(chemical.systemSolution).toContain("Medienliste");
    expect(renewal.systemSolution).toContain("Herstellerfreigaben");
  });

  it("keeps site catalog titles unique and short enough to audit", () => {
    const titles = getAllPublicPages().map((page) => page.seoTitle);
    expect(new Set(titles).size).toBe(titles.length);
    for (const title of titles) expect(title.length).toBeLessThan(90);
  });
});

describe("hreflang points only to existing equivalent language pages", () => {
  it("keeps language homepages reciprocal and does not invent translated industry pages", () => {
    const langHomes = new Set(languages.map((lang) => lang.href));
    expect(homeAlternates).toHaveLength(langHomes.size);
    expect(homeAlternates.every((alt) => langHomes.has(alt.path))).toBe(true);

    const industry = readFileSync(join(process.cwd(), "src/pages/branchen/[slug].astro"), "utf8");
    const service = readFileSync(join(process.cwd(), "src/pages/leistungen/[slug].astro"), "utf8");
    expect(industry).not.toContain("homeAlternates");
    expect(service).not.toContain("homeAlternates");
    const international = readFileSync(join(process.cwd(), "src/components/sections/InternationalLanding.astro"), "utf8");
    expect(international).toContain("alternates={homeAlternates}");
  });
});
