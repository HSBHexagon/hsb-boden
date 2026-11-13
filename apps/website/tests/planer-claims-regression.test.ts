// @vitest-environment node
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const pages = [
  "planer/index.astro",
  "wissen/ruettelkeramik-agi-s-40/index.astro",
  "wissen/fugen-forensik/index.astro",
  "wissen/fugen-forensik/fuge-ausgewaschen.astro",
  "wissen/fugen-forensik/fliesen-hohl.astro",
  "wissen/fugen-forensik/thermoschock-schaeden.astro",
  "wissen/fugen-forensik/rinnenkante-gerissen.astro",
  "wissen/fugen-forensik/hohlkehle-undicht.astro",
];
function page(path: string): string {
  return readFileSync(new URL("../src/pages/" + path, import.meta.url), "utf8");
}

describe("Planer- und Fachwissen-Texte ohne Scheinnachweise", () => {
  for (const path of pages) {
    it(path + ": kein sichtbarer MOCK_DATA-Platzhalter", () => {
      expect(page(path)).not.toContain("MOCK_DATA");
    });
  }

  it("verspricht keine pauschale 100%-Hohlstellenfreiheit", () => {
    const combined = pages.map(page).join("\n");
    expect(combined).not.toMatch(/100\s*%\s*(?:hohlraumfrei|Vollbettung)/i);
    expect(combined).not.toMatch(/garantiert\s+hohlraumfreie/i);
  });

  it("weist die Prüfung objektspezifischer Kennwerte im LV ausdrücklich aus", () => {
    const planer = page("planer/index.astro");
    expect(planer).toContain("Produktdatenblatt");
    expect(planer).toContain("nachgewiesenen Leistungsbereich");
  });
});
