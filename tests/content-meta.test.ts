import { describe, expect, it } from "vitest";
import { industries } from "../src/data/industries";

describe("industry meta titles reflect documented compliance terms", () => {
  it("includes HACCP in the Lebensmittelindustrie seoTitle since HACCP is already a documented requirement for this industry", () => {
    const lebensmittel = industries.find((i) => i.slug === "lebensmittelindustrie");
    expect(lebensmittel).toBeDefined();
    expect(lebensmittel!.floorRequirements.some((r) => r.includes("HACCP"))).toBe(true);
    expect(lebensmittel!.seoTitle).toContain("HACCP");
  });

  it("every industry has a unique seoTitle (no duplicate content)", () => {
    const titles = industries.map((i) => i.seoTitle);
    const uniqueTitles = new Set(titles);
    expect(uniqueTitles.size).toBe(titles.length);
  });

  it("every industry seoTitle stays under 60 characters for SERP display", () => {
    for (const industry of industries) {
      expect(industry.seoTitle.length).toBeLessThanOrEqual(60);
    }
  });
});
