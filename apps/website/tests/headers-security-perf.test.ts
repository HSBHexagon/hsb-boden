import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Cloudflare Pages Headers Audit", () => {
  const headersPath = resolve(__dirname, "../public/_headers");
  const content = readFileSync(headersPath, "utf-8");

  it("should declare 1-year immutable cache for _astro assets", () => {
    expect(content).toContain("/_astro/*");
    expect(content).toContain("Cache-Control: public, max-age=31536000, immutable");
  });

  it("should have strict HSTS with preload and subdomains", () => {
    expect(content).toContain("Strict-Transport-Security: max-age=31536000; includeSubDomains; preload");
  });

  it("should configure proper cache for brand and media directories", () => {
    expect(content).toContain("/brand/*");
    expect(content).toContain("stale-while-revalidate=");
  });

  it("should enforce noindex on staging pages.dev subdomains", () => {
    expect(content).toContain("X-Robots-Tag: noindex, nofollow");
  });
});
