import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { GET } from "../src/pages/sitemap.xml";

describe("conversion thank-you page indexability", () => {
  it("does not publish the thank-you URL in the XML sitemap", async () => {
    const response = await GET();
    const xml = await response.text();

    expect(xml).not.toContain("/danke-projektanfrage/");
  });

  it("marks the thank-you page noindex while keeping links followable", () => {
    const source = readFileSync(
      join(process.cwd(), "src/pages/danke-projektanfrage.astro"),
      "utf8",
    );

    expect(source).toContain('robots="noindex, follow"');
  });
});
