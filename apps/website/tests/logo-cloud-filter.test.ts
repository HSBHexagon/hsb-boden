import { describe, expect, it } from "vitest";
import { getLogoCloudEntries } from "../src/lib/content";

describe("LogoCloud Branchenfilter", () => {
  it("stellt bei 'molkerei' Gropper und Meggle an den Anfang", () => {
    const names = getLogoCloudEntries("molkerei").slice(0, 2).map((entry) => entry.name);
    expect(names).toEqual(expect.arrayContaining(["Molkerei Gropper GmbH & Co. KG", "Meggle"]));
  });

  it("stellt bei 'lebensmittelindustrie' Südzucker an den Anfang", () => {
    expect(getLogoCloudEntries("lebensmittelindustrie")[0].name).toBe("Südzucker AG");
  });

  it("zieht bei 'chemieindustrie' Concept Color vor und Südzucker über Systemaffinität nach vorn", () => {
    const names = getLogoCloudEntries("chemieindustrie").map((entry) => entry.name);
    expect(names[0]).toBe("Concept Color GmbH");
    expect(names.indexOf("Südzucker AG")).toBeLessThan(names.indexOf("Peterstaler Mineralquellen GmbH"));
  });

  it("ändert ohne Filter weder Menge noch Reihenfolge", () => {
    const unfiltered = getLogoCloudEntries();
    const filtered = getLogoCloudEntries("molkerei");
    expect(filtered).toHaveLength(unfiltered.length);
    expect(new Set(filtered.map((e) => e.logo))).toEqual(new Set(unfiltered.map((e) => e.logo)));
  });

  it("leitet Proof-Tags ausschließlich aus den dokumentierten Systemen ab", () => {
    const entries = getLogoCloudEntries();
    const suedzucker = entries.find((entry) => entry.name === "Südzucker AG");
    const gropper = entries.find((entry) => entry.name === "Molkerei Gropper GmbH & Co. KG");
    const kyritzer = entries.find((entry) => entry.logo === "/logos/kyritzer-fruchtsaefte.png");
    expect(suedzucker?.proofTag).toBe("Säureschutz & WHG § 62 Abdichtung");
    expect(gropper?.proofTag).toBe("Rüttelkeramik & Entwässerung");
    expect(kyritzer?.proofTag).toBe("Kundenstandort Getränke");
    for (const entry of entries) expect(entry.proofTag.length).toBeGreaterThan(0);
  });

  it("stellt Gaffel genau einmal im bestehenden Brauerei-Logo-Raster dar", () => {
    const entries = getLogoCloudEntries("brauerei-getraenkeindustrie");
    const matches = entries.filter((entry) => entry.name === "Gaffel Privatbrauerei");
    expect(matches).toHaveLength(1);
    expect(matches[0]).toMatchObject({
      logo: "/logos/gaffel.svg",
      meta: "Brauerei",
      proofTag: "Kundenstandort Brauerei",
      industry: "brauerei-getraenkeindustrie",
    });
    expect(entries.indexOf(matches[0])).toBeLessThan(entries.findIndex((entry) => entry.name === "Concept Color GmbH"));
  });

  it("zeigt MAGNUS, Rolinck und Glossner je einmal im vorhandenen Logo-Raster", () => {
    const entries = getLogoCloudEntries();
    for (const [name, logo, industry] of [
      ["MAGNUS Mineralbrunnen GmbH & Co. KG", "/logos/magnus.png", "brauerei-getraenkeindustrie"],
      ["Rolinck Privatbrauerei", "/logos/rolinck.svg", "brauerei-getraenkeindustrie"],
      ["Neumarkter Glossnerbräu", "/logos/glossnerbraeu.png", "brauerei-getraenkeindustrie"],
    ]) {
      const matches = entries.filter((entry) => entry.name === name);
      expect(matches).toHaveLength(1);
      expect(matches[0].logo).toBe(logo);
      expect(matches[0].industry).toBe(industry);
      expect(matches[0].systems).toEqual([]);
      expect(matches[0].proofTag).toMatch(/^Kundenstandort /);
    }
  });

  it("erfindet keinen Eintrag für Kunden ohne Logo-Freigabe", () => {
    const names = getLogoCloudEntries("brauerei-getraenkeindustrie").map((entry) => entry.name);
    expect(names).not.toContain("Krombacher Brauerei GmbH & Co. KG");
  });
});
