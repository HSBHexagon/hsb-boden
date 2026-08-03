import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(join(process.cwd(), path), "utf8");
}

describe("PowerAgent audit guardrails", () => {
  it("does not publish private Notion backups into the public repository", () => {
    expect(existsSync(join(process.cwd(), ".github/workflows/notion-nightly-backup.yml"))).toBe(false);
  });

  it("pins every third-party GitHub Action to an immutable commit", () => {
    const workflows = [
      source(".github/workflows/notion-deploy-sync.yml"),
      source(".github/workflows/notion-issue-sync.yml"),
    ];

    for (const workflow of workflows) {
      expect(workflow).not.toMatch(/^\s*uses:\s*[^\s]+@v\d+/m);
      expect(workflow).toContain("@notionhq/client@4.0.2");
      expect(workflow).toContain("--ignore-scripts");
    }
  });

  it("keeps Search Console verification in one global source and publishes complete social metadata", () => {
    const layout = source("src/layouts/BaseLayout.astro");
    const seoHead = source("src/components/seo/SEOHead.astro");

    expect(layout).not.toContain('name="google-site-verification"');
    expect(seoHead.match(/name="google-site-verification"/g)).toHaveLength(1);
    expect(seoHead).toContain('property="og:image:alt"');
    expect(seoHead).toContain('name="twitter:title"');
    expect(seoHead).toContain('name="twitter:description"');
    expect(seoHead).toContain('name="twitter:image"');
    expect(seoHead).toContain('name="twitter:image:alt"');
  });

  it("does not emit unverifiable sitemap freshness or ignored ranking hints", () => {
    const sitemap = source("src/pages/sitemap.xml.ts");

    expect(sitemap).not.toContain("<lastmod>");
    expect(sitemap).not.toContain("<changefreq>");
    expect(sitemap).not.toContain("<priority>");
  });

  it("prevents Cloudflare preview domains from being indexed", () => {
    const headers = source("public/_headers");

    expect(headers).toContain("https://hsb-boden.pages.dev/*");
    expect(headers).toContain("https://:version.hsb-boden.pages.dev/*");
    expect(headers).toContain("X-Robots-Tag: noindex, nofollow");
  });

  it("builds phone links from the canonical business number without the German trunk zero", () => {
    const leadForm = source("src/components/forms/LeadForm.astro");
    const cta = source("src/components/sections/CTASection.astro");

    expect(leadForm).toContain('site.phone.replace("(0)", "")');
    expect(cta).toContain('import { site } from "../../data/site"');
    expect(cta).toContain('site.phone.replace("(0)", "")');
    expect(cta).not.toContain("tel:+4925629463030");
  });
});
