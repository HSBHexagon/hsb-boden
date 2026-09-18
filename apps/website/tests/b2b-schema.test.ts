import { describe, expect, it } from "vitest";
import {
  NORM_IDS,
  executionStandards,
  getStandardsForService,
  organizationCredential,
} from "../src/data/standards";

describe("Normen-Datenquelle", () => {
  it("kennt genau die drei B2B-Normen", () => {
    expect([...NORM_IDS]).toEqual(["AGI S 40", "DIN EN 14411", "WHG § 62"]);
    expect(executionStandards.map((s) => s.id)).toEqual([...NORM_IDS]);
  });

  it("ordnet Leistungen belegbare Ausführungsnormen zu", () => {
    expect(getStandardsForService("keramische-industrieboeden")).toEqual(["AGI S 40", "DIN EN 14411"]);
    expect(getStandardsForService("whg-abdichtung-industrieboden")).toEqual(["WHG § 62"]);
    expect(getStandardsForService("boden-reparatur-instandsetzung")).toEqual([]);
  });

  it("führt nur den owner-bestätigten WHG-Fachbetrieb als Credential", () => {
    expect(organizationCredential.name).toContain("§ 62 WHG");
    expect(organizationCredential.evidenceRef).toContain("PROJECT_TRUTH.md");
  });
});

import { buildOrganizationJsonLd, buildServiceJsonLd } from "../src/lib/schema";

describe("Schema.org-Normen", () => {
  it("führt Normen als Wissen und nur den WHG-Fachbetrieb als Credential", () => {
    const graph = buildOrganizationJsonLd();
    const blob = JSON.stringify(graph);
    expect(graph.knowsAbout).toEqual(expect.arrayContaining([
      "AGI S 40 Säureschutzbau (keramische Beläge)",
      "DIN EN 14411 Keramische Fliesen und Platten",
      "§ 62 WHG / AwSV Anlagen mit wassergefährdenden Stoffen",
    ]));
    expect(graph.hasCredential).toHaveLength(1);
    expect(graph.hasCredential[0].name).toBe("Fachbetrieb nach § 62 WHG / AwSV");
    expect(blob).not.toMatch(/"hasCredential":\[[^\]]*AGI S 40/);
    expect(blob).not.toMatch(/"hasCredential":\[[^\]]*DIN EN 14411/);
  });

  it("hängt Ausführungsnormen als additionalProperty an das Service-Schema", () => {
    const graph = buildServiceJsonLd({
      name: "Keramische Industrieböden",
      description: "Rüttelkeramik nach AGI S 40 für produktionskritische Bereiche.",
      path: "/leistungen/keramische-industrieboeden/",
      standards: ["AGI S 40", "DIN EN 14411"],
    });
    expect(graph.additionalProperty).toEqual([
      { "@type": "PropertyValue", name: "Ausführungsgrundlage", value: "AGI S 40" },
      { "@type": "PropertyValue", name: "Ausführungsgrundlage", value: "DIN EN 14411" },
    ]);
    expect(graph.provider.hasCredential[0].name).toBe("Fachbetrieb nach § 62 WHG / AwSV");
  });

  it("lässt Service-Schema ohne Normen unverändert schlank", () => {
    const graph = buildServiceJsonLd({ name: "Reparatur", description: "Instandsetzung.", path: "/leistungen/boden-reparatur-instandsetzung/" });
    expect(graph.additionalProperty).toBeUndefined();
  });
});
