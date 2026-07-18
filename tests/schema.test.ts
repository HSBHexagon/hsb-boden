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

  it("builds faq json-ld correctly", () => {
    // Should return null for empty array
    expect(buildFaqJsonLd([])).toBeNull();

    // Should return valid schema for non-empty array
    const faqs = [
      { question: "What is the meaning of life?", answer: "42" },
      { question: "Is this a test?", answer: "Yes, it is." },
    ];
    const graph = buildFaqJsonLd(faqs);

    expect(graph).not.toBeNull();
    expect(graph!["@type"]).toBe("FAQPage");
    expect(graph!.mainEntity).toHaveLength(2);

    const firstQuestion = graph!.mainEntity[0];
    expect(firstQuestion["@type"]).toBe("Question");
    expect(firstQuestion.name).toBe("What is the meaning of life?");
    expect(firstQuestion.acceptedAnswer["@type"]).toBe("Answer");
    expect(firstQuestion.acceptedAnswer.text).toBe("42");
  });
});
