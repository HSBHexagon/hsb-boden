import { describe, expect, it } from "vitest";
import { getAllPublicPages } from "../src/lib/content";

describe("getAllPublicPages: Standortseiten", () => {
  it("includes all existing /standorte/* location pages", () => {
    const pages = getAllPublicPages();
    const paths = pages.map((p) => p.canonicalPath);

    expect(paths).toContain("/standorte/hamburg/");
    expect(paths).toContain("/standorte/bayern/");
    expect(paths).toContain("/standorte/nrw/");
  });

  it("every standorte entry has a non-empty seoTitle and description", () => {
    const pages = getAllPublicPages();
    const standortePages = pages.filter((p) =>
      p.canonicalPath.startsWith("/standorte/"),
    );

    expect(standortePages.length).toBeGreaterThanOrEqual(3);
    for (const page of standortePages) {
      expect(page.seoTitle.length).toBeGreaterThan(10);
      expect(page.description.length).toBeGreaterThan(20);
    }
  });
});
