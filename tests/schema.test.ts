import { describe, expect, it } from "vitest";
import { buildBreadcrumbJsonLd, buildOrganizationJsonLd, buildServiceJsonLd, buildFaqJsonLd } from "../src/lib/schema";

describe("json-ld generation", () => {
  it("returns valid organization json-ld without unsupported partner claims", () => {
    const graph = buildOrganizationJsonLd();

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@type"]).toBe("Organization");
    expect(JSON.stringify(graph)).not.toContain("zertifizierter Partner");
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

  it("builds faq json-ld mapping input questions and answers", () => {
    const faqs = [
      { question: "Was ist ein Säureschutz?", answer: "Ein Schutz vor Säuren." },
      { question: "Wie lange hält das?", answer: "Sehr lange." },
    ];
    const graph = buildFaqJsonLd(faqs);

    expect(() => JSON.stringify(graph)).not.toThrow();
    expect(graph["@context"]).toBe("https://schema.org");
    expect(graph["@type"]).toBe("FAQPage");
    expect(graph.mainEntity).toHaveLength(2);
    expect(graph.mainEntity[0]["@type"]).toBe("Question");
    expect(graph.mainEntity[0].name).toBe("Was ist ein Säureschutz?");
    expect(graph.mainEntity[0].acceptedAnswer["@type"]).toBe("Answer");
    expect(graph.mainEntity[0].acceptedAnswer.text).toBe("Ein Schutz vor Säuren.");
    expect(graph.mainEntity[1].name).toBe("Wie lange hält das?");
    expect(graph.mainEntity[1].acceptedAnswer.text).toBe("Sehr lange.");
  });
});
