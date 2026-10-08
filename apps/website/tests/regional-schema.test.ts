import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { buildRegionalServiceJsonLd } from "../src/lib/schema";
import { site } from "../src/data/site";

const regions = [
  "baden-wuerttemberg", "bayern", "hamburg", "hessen",
  "niedersachsen", "nrw", "rheinland-pfalz", "sachsen-anhalt", "thueringen",
];

describe("regionale Landingpages: wahrheitsgetreue strukturierte Daten", () => {
  it("kennzeichnet ein Leistungsgebiet und keine zusätzliche Niederlassung", () => {
    const graph = buildRegionalServiceJsonLd("Nordrhein-Westfalen", "/standorte/nrw/");
    expect(graph["@type"]).toBe("Service");
    expect(graph.areaServed).toBe("Nordrhein-Westfalen");
    expect(graph.url).toBe(`${site.domain}/standorte/nrw/`);
    expect(graph.provider["@type"]).toBe("Organization");
    expect(graph.provider.name).toBe(site.name);
    expect(graph.provider.telephone).toBe(site.phone);
    expect(JSON.stringify(graph)).not.toContain("+49-2234-9876543");
    expect(JSON.stringify(graph)).not.toContain("LocalBusiness");
  });

  it.each(regions)("%s bindet die zentrale Service-Auszeichnung ein", (slug) => {
    const source = readFileSync(
      join(process.cwd(), "src/pages/standorte", slug, "index.astro"),
      "utf8",
    );
    expect(source).toContain("buildRegionalServiceJsonLd");
    expect(source).toContain(`path="/standorte/${slug}/"`);
    expect(source).toContain("jsonLd={[buildRegionalServiceJsonLd(");
    expect(source).not.toContain("Hexagon Säurebau GmbH");
    expect(source).not.toContain("+49-2234-9876543");
    expect(source).not.toContain('type="application/ld+json"');
  });
});
