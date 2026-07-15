import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(join(process.cwd(), path), "utf8");
}

describe("SEO, accessibility and performance guardrails", () => {
  it("keeps Search Console verification in one global source", () => {
    const layout = source("src/layouts/BaseLayout.astro");
    const seoHead = source("src/components/seo/SEOHead.astro");

    expect(layout).not.toContain('name="google-site-verification"');
    expect(seoHead.match(/name="google-site-verification"/g)).toHaveLength(1);
  });

  it("publishes complete social preview metadata", () => {
    const seoHead = source("src/components/seo/SEOHead.astro");

    expect(seoHead).toContain('property="og:image:alt"');
    expect(seoHead).toContain('name="twitter:title"');
    expect(seoHead).toContain('name="twitter:description"');
    expect(seoHead).toContain('name="twitter:image"');
    expect(seoHead).toContain('name="twitter:image:alt"');
  });

  it("uses a valid central business phone in the reusable CTA", () => {
    const cta = source("src/components/sections/CTASection.astro");

    expect(cta).toContain('import { site } from "../../data/site"');
    expect(cta).toContain('site.phone.replace("(0)", "")');
    expect(cta).toContain("tel:${phoneHref}");
    expect(cta).not.toContain("tel:+4925629463030");
  });

  it("keeps the homepage LCP image explicitly prioritized and dimensioned", () => {
    const homepage = source("src/pages/index.astro");
    const heroStart = homepage.indexOf('src="/media/hsb/current/industrieboden-baustelle.webp"');
    const heroEnd = homepage.indexOf("/>", heroStart);
    const heroImage = homepage.slice(heroStart, heroEnd);

    expect(heroStart).toBeGreaterThan(-1);
    expect(heroImage).toContain('fetchpriority="high"');
    expect(heroImage).toContain('loading="eager"');
    expect(heroImage).toContain('width="1024"');
    expect(heroImage).toContain('height="768"');
    expect(heroImage).toContain('alt="Keramischer Industrieboden');
  });
});
