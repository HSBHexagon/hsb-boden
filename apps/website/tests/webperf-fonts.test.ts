import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Font & Critical Resource Performance", () => {
  const seoHead = readFileSync(resolve(__dirname, "../src/components/seo/SEOHead.astro"), "utf-8");
  const globalCss = readFileSync(resolve(__dirname, "../src/styles/global.css"), "utf-8");
  const baseLayout = readFileSync(resolve(__dirname, "../src/layouts/BaseLayout.astro"), "utf-8");
  const astroConfig = readFileSync(resolve(__dirname, "../astro.config.mjs"), "utf-8");
  const languageSuggest = readFileSync(resolve(__dirname, "../src/components/layout/LanguageSuggest.astro"), "utf-8");

  it("does not load external Google Fonts stylesheets", () => {
    expect(seoHead).not.toMatch(/<link[^>]+rel=["']stylesheet["'][^>]+fonts\.googleapis\.com/);
  });

  it("does not preconnect to third-party analytics endpoints before consent", () => {
    expect(seoHead).not.toContain("https://region1.analytics.google.com");
    expect(seoHead).not.toContain("https://region1.google-analytics.com");
    expect(seoHead).not.toContain("https://www.googletagmanager.com");
    expect(seoHead).not.toContain("https://static.cloudflareinsights.com");
  });

  it("uses Astro's variable Fontsource provider with optimized fallbacks", () => {
    expect(astroConfig).toContain("fontProviders.fontsource()");
    expect(astroConfig).toContain('weights: ["100 900"]');
    expect(astroConfig).toContain('cssVariable: "--font-outfit"');
    expect(globalCss).not.toContain('@fontsource/outfit/');
    expect(globalCss).toContain("font-family: var(--font-outfit)");
  });

  it("preloads the configured variable font from the shared layout", () => {
    expect(baseLayout).toContain('import { Font } from "astro:assets"');
    expect(baseLayout).toContain('<Font cssVariable="--font-outfit" preload />');
  });

  it("keeps the client-language suggestion out of document flow", () => {
    expect(languageSuggest).toMatch(/class="[^"]*fixed[^"]*hidden[^"]*"/);
    expect(languageSuggest).toContain("top-[84px]");
  });
});
