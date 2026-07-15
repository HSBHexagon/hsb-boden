import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { getAllPublicPages } from "../src/lib/content";

function source(path: string) {
  return readFileSync(join(process.cwd(), path), "utf8");
}

describe("project flow navigation", () => {
  it("publishes a dedicated project flow page with five visible phases", () => {
    const pagePath = join(process.cwd(), "src/pages/projektablauf/index.astro");
    expect(existsSync(pagePath)).toBe(true);

    const page = readFileSync(pagePath, "utf8");
    expect(page).toContain('path="/projektablauf/"');
    expect(page).toContain("Analyse vor Ort");
    expect(page).toContain("Systemauslegung");
    expect(page).toContain("Untergrundvorbereitung");
    expect(page).toContain("Einbau und Ausführung");
    expect(page).toContain("Abnahme und Dokumentation");
  });

  it("registers the page in canonical content and navigation sources", () => {
    const navigation = source("src/data/navigation.ts");
    const homepage = source("src/pages/index.astro");
    const sitemap = source("src/pages/sitemap.xml.ts");
    const publicPage = getAllPublicPages().find((page) => page.canonicalPath === "/projektablauf/");

    expect(publicPage).toBeDefined();
    expect(publicPage?.seoTitle).toContain("Projektablauf");
    expect(navigation).toContain('{ label: "Projektablauf", href: "/projektablauf/" }');
    expect(navigation).not.toContain('href: "/#projektablauf"');
    expect(homepage).toContain('href="/projektablauf/"');
    expect(homepage).toContain("Projektablauf im Detail");
    expect(sitemap).toContain('"/projektablauf/"');
  });

  it("builds header telephone links from the central site data", () => {
    const header = source("src/components/layout/Header.astro");

    expect(header).toContain('import { site } from "../../data/site"');
    expect(header).toContain("const phoneHref = site.phone.replace");
    expect(header).toContain("tel:${phoneHref}");
    expect(header).toContain("site.phone");
  });
});
