import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("ArticleAttribution component", () => {
  it("exists and references the organization name without inventing a person", () => {
    const componentPath = join(process.cwd(), "src/components/sections/ArticleAttribution.astro");
    const content = readFileSync(componentPath, "utf-8");

    expect(content).toContain("HSB Hexagon Säurebau GmbH");
    // Must not invent an individual author name — organization-level attribution only.
    expect(content).not.toMatch(/von\s+[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+/);
  });
});
