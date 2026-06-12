import { describe, expect, it } from "vitest";
import { absoluteUrl, canonical, pageTitle } from "../src/lib/seo";
import { site } from "../src/data/site";

describe("seo module", () => {
  describe("absoluteUrl", () => {
    it("returns the root URL when no path is provided", () => {
      expect(absoluteUrl()).toBe(`${site.domain}/`);
    });

    it("appends the domain to a path with a leading slash", () => {
      expect(absoluteUrl("/leistungen")).toBe(`${site.domain}/leistungen`);
    });

    it("adds a leading slash and appends the domain if the path lacks a leading slash", () => {
      expect(absoluteUrl("kontakt")).toBe(`${site.domain}/kontakt`);
    });

    it("returns the path as is if it starts with 'http'", () => {
      expect(absoluteUrl("https://example.com/external")).toBe("https://example.com/external");
      expect(absoluteUrl("http://example.com/external")).toBe("http://example.com/external");
    });
  });

  describe("canonical", () => {
    it("ensures a trailing slash and returns absolute URL", () => {
      expect(canonical("/leistungen")).toBe(`${site.domain}/leistungen/`);
    });

    it("preserves trailing slash if already present and returns absolute URL", () => {
      expect(canonical("/leistungen/")).toBe(`${site.domain}/leistungen/`);
    });
  });

  describe("pageTitle", () => {
    it("returns the provided title", () => {
      expect(pageTitle("Kontakt")).toBe("Kontakt");
    });

    it("falls back to default title if no title is provided", () => {
      expect(pageTitle()).toBe(site.defaultTitle);
    });
  });
});
