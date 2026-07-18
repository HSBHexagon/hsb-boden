import { describe, expect, it } from "vitest";
import { buildBreadcrumbJsonLd, buildOrganizationJsonLd, buildServiceJsonLd, buildLocalBusinessJsonLd, buildFaqJsonLd } from "../src/lib/schema";

describe("json-ld generation", () => {
  it("returns valid organization json-ld without unsupported partner claims", () => {
    const graph = buildOrganizationJsonLd();

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@type"]).toBe("Organization");
    expect(JSON.stringify(graph)).not.toContain("zertifizierter Partner");
  });

  it("returns valid local business json-ld", () => {
    const graph = buildLocalBusinessJsonLd();

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@type"]).toBe("LocalBusiness");
    expect(graph.name).toBe("HSB Hexagon Säurebau GmbH");
    expect(graph.priceRange).toBe("$$$");
    expect(graph.areaServed).toContain("Deutschland");
    // Also verify some basic structure for telephone/url depending on configuration
    expect(graph).toHaveProperty("url");
    expect(graph).toHaveProperty("telephone");
  });

  it("builds service json-ld with organization provider", () => {
    const graph = buildServiceJsonLd({
      name: "Industrieboden-Säureschutz",
      description: "Säurebeständige Bodensysteme für die Industrie.",
      path: "/leistungen/industrieboden-saeureschutz/",
    });

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@type"]).toBe("Service");
    expect(graph.provider["@type"]).toBe("Organization");
    expect(graph.url).toContain("/leistungen/industrieboden-saeureschutz/");
  });

  it("builds breadcrumb json-ld for nested pages", () => {
    const graph = buildBreadcrumbJsonLd([
      { name: "Start", path: "/" },
      { name: "Leistungen", path: "/leistungen/" },
      { name: "Säureschutz", path: "/leistungen/industrieboden-saeureschutz/" },
    ]);

    expect(graph.itemListElement).toHaveLength(3);
    expect(graph.itemListElement[2].position).toBe(3);
  });

  it("builds faq json-ld for multiple faqs", () => {
    const graph = buildFaqJsonLd([
      { question: "Q1", answer: "A1" },
      { question: "Q2", answer: "A2" },
    ]);

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph?.["@type"]).toBe("FAQPage");
    expect(graph?.mainEntity).toHaveLength(2);
    expect(graph?.mainEntity[0]["@type"]).toBe("Question");
    expect(graph?.mainEntity[0].name).toBe("Q1");
    expect(graph?.mainEntity[0].acceptedAnswer["@type"]).toBe("Answer");
    expect(graph?.mainEntity[0].acceptedAnswer.text).toBe("A1");
  });

  it("returns null for empty faqs array", () => {
    const graph = buildFaqJsonLd([]);
    expect(graph).toBeNull();
  });
});
