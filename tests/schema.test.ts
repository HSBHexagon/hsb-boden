import { describe, expect, it } from "vitest";
import { buildBreadcrumbJsonLd, buildOrganizationJsonLd, buildServiceJsonLd } from "../src/lib/schema";

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
});
