import { describe, expect, it } from "vitest";
import { absoluteUrl, canonical, pageTitle } from "../src/lib/seo";
import { site } from "../src/data/site";

describe("SEO utilities", () => {
  describe("pageTitle", () => {
    it("returns the provided title when given", () => {
      expect(pageTitle("My Custom Page")).toBe("My Custom Page");
    });

    it("returns an empty string if provided", () => {
      expect(pageTitle("")).toBe("");
    });

    it("returns the default site title when undefined is provided", () => {
      expect(pageTitle(undefined)).toBe(site.defaultTitle);
    });

    it("returns the default site title when no arguments are provided", () => {
      expect(pageTitle()).toBe(site.defaultTitle);
    });
  });

  describe("absoluteUrl", () => {
    it("returns the path itself if it already starts with http", () => {
      expect(absoluteUrl("https://example.com/page")).toBe("https://example.com/page");
    });

    it("prepends the site domain if it starts with /", () => {
      expect(absoluteUrl("/my-page")).toBe(`${site.domain}/my-page`);
    });

    it("prepends the site domain and adds a slash if it doesn't start with /", () => {
      expect(absoluteUrl("my-page")).toBe(`${site.domain}/my-page`);
    });

    it("returns just the site domain + / if no path is given", () => {
      expect(absoluteUrl()).toBe(`${site.domain}/`);
    });
  });

  describe("canonical", () => {
    it("appends a trailing slash if missing and returns absolute URL", () => {
      expect(canonical("/my-page")).toBe(`${site.domain}/my-page/`);
    });

    it("does not append another slash if it already has one and returns absolute URL", () => {
      expect(canonical("/my-page/")).toBe(`${site.domain}/my-page/`);
    });

    it("handles paths without a leading slash", () => {
      expect(canonical("my-page")).toBe(`${site.domain}/my-page/`);
    });
  });
});
