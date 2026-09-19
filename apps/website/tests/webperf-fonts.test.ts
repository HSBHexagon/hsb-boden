import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Font & Critical Resource Performance", () => {
  const seoHeadPath = resolve(__dirname, "../src/components/seo/SEOHead.astro");
  const content = readFileSync(seoHeadPath, "utf-8");

  it("should not contain render-blocking external Google Fonts css links", () => {
    expect(content).not.toMatch(/<link[^>]+rel=["']stylesheet["'][^>]+fonts\.googleapis\.com/);
  });

  it("should streamline head hints and not preconnect to external analytics domains directly", () => {
    // Edge-Proxy übernimmt Analytics serverseitig; keine Drittanbieter-Preconnects im Head nötig
    expect(content).not.toContain("https://region1.analytics.google.com");
    expect(content).not.toContain("https://region1.google-analytics.com");
    expect(content).not.toContain("https://www.googletagmanager.com");
  });

  it("should preserve Cloudflare insights performance prefetch", () => {
    expect(content).toContain("https://static.cloudflareinsights.com");
  });
});
