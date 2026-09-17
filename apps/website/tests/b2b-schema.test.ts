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
