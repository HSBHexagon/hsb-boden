import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
}

describe("project flow navigation", () => {
  it("publishes a dedicated project flow page with five visible phases", () => {
    const pageUrl = new URL("../src/pages/projektablauf/index.astro", import.meta.url);
    expect(existsSync(pageUrl)).toBe(true);

    const page = readFileSync(pageUrl, "utf8");
    expect(page).toContain('path="/projektablauf/"');
    expect(page).toContain("Analyse vor Ort");
    expect(page).toContain("Systemauslegung");
    expect(page).toContain("Untergrundvorbereitung");
    expect(page).toContain("Einbau und Ausführung");
    expect(page).toContain("Abnahme und Dokumentation");
  });

  it("uses the dedicated route in navigation and from the homepage process section", () => {
    const navigation = source("src/data/navigation.ts");
    const homepage = source("src/pages/index.astro");

    expect(navigation).toContain('{ label: "Projektablauf", href: "/projektablauf/" }');
    expect(navigation).not.toContain('href: "/#projektablauf"');
    expect(homepage).toContain('href="/projektablauf/"');
    expect(homepage).toContain("Projektablauf im Detail");
  });

  it("builds header telephone links from the central site data", () => {
    const header = source("src/components/layout/Header.astro");

    expect(header).toContain('import { site } from "../../data/site"');
    expect(header).toContain("const phoneHref = site.phone.replace");
    expect(header).toContain("tel:${phoneHref}");
    expect(header).toContain("site.phone");
  });
});
