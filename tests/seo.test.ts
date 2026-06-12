import { describe, expect, it } from "vitest";
import { absoluteUrl, canonical, pageTitle } from "../src/lib/seo";
import { site } from "../src/data/site";

describe("seo functions", () => {
  describe("absoluteUrl", () => {
    it("should return the path unchanged if it starts with http", () => {
      expect(absoluteUrl("https://example.com/path")).toBe("https://example.com/path");
      expect(absoluteUrl("http://example.com/path")).toBe("http://example.com/path");
    });

    it("should prepend the site domain to a relative path", () => {
      expect(absoluteUrl("/my-page")).toBe(`${site.domain}/my-page`);
    });

    it("should prepend a slash if the relative path doesn't start with one", () => {
      expect(absoluteUrl("my-page")).toBe(`${site.domain}/my-page`);
    });

    it("should default to / if no path is provided", () => {
      expect(absoluteUrl()).toBe(`${site.domain}/`);
    });
  });

  describe("canonical", () => {
    it("should append a trailing slash and return the absolute URL", () => {
      expect(canonical("/my-page")).toBe(`${site.domain}/my-page/`);
      expect(canonical("my-page")).toBe(`${site.domain}/my-page/`);
    });

    it("should not append an extra trailing slash if it already has one", () => {
      expect(canonical("/my-page/")).toBe(`${site.domain}/my-page/`);
      expect(canonical("my-page/")).toBe(`${site.domain}/my-page/`);
    });

    it("should handle the root path", () => {
        expect(canonical("/")).toBe(`${site.domain}/`);
    });
  });

  describe("pageTitle", () => {
    it("should return the provided title if it exists", () => {
      expect(pageTitle("My Custom Title")).toBe("My Custom Title");
    });

    it("should return the default title if no title is provided", () => {
      expect(pageTitle()).toBe(site.defaultTitle);
    });
  });
});
