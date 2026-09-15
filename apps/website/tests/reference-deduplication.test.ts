import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import {
  getLogoCloudEntries,
  getPublicReferences,
  getSupplementalClientLocations,
} from "../src/lib/content";
import { clientLocations } from "../src/data/clientLocations";
import { references } from "../src/data/references";

function collectAstroFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) return collectAstroFiles(full);
    return entry.name.endsWith(".astro") ? [full] : [];
  });
}

// Regression: Meggle und Biovegan waren sowohl freigegebene Referenz als auch
// Kundenstandort und erschienen dadurch doppelt — im LogoCloud der Startseite,
// als doppelter Kartenmarker und in der Liste "Weitere Kundenstandorte".
// Die Zuordnung laeuft ueber die kanonische referenceId, nicht ueber Namensvergleich.

describe("LogoCloud-Deduplizierung", () => {
  it("zeigt jeden Kunden genau einmal", () => {
    const names = getLogoCloudEntries().map((entry) => entry.name);

    expect(names.length).toBeGreaterThan(0);
    expect(new Set(names).size).toBe(names.length);
  });

  it("zeigt jedes Logo-Asset genau einmal", () => {
    const logos = getLogoCloudEntries().map((entry) => entry.logo);

    expect(new Set(logos).size).toBe(logos.length);
  });

  it("gibt der freigegebenen Referenz Vorrang vor dem Kundenstandort", () => {
    const entries = getLogoCloudEntries();

    for (const logo of ["/logos/meggle.svg", "/logos/biovegan.svg"]) {
      const matches = entries.filter((entry) => entry.logo === logo);
      expect(matches).toHaveLength(1);
      expect(matches[0].meta).toBe("Referenzprojekt");
    }
  });

  it("behaelt Kundenstandort-Logos ohne Referenz-Gegenstueck", () => {
    const logos = getLogoCloudEntries().map((entry) => entry.logo);

    expect(logos).toContain("/logos/kyritzer-fruchtsaefte.png");
  });
});

describe("Ergaenzende Kundenstandorte", () => {
  it("listet keinen Standort, der bereits als oeffentliche Referenz erscheint", () => {
    const publicReferenceIds = new Set(
      getPublicReferences().map((reference) => reference.id),
    );

    for (const location of getSupplementalClientLocations()) {
      const referenceId =
        "referenceId" in location ? location.referenceId : undefined;
      expect(publicReferenceIds.has(referenceId as string)).toBe(false);
    }
  });

  it("entfernt genau die doppelten Standorte und behaelt alle anderen", () => {
    const names = getSupplementalClientLocations().map(
      (location) => location.name,
    );

    expect(names).not.toContain("Meggle");
    expect(names).not.toContain("Biovegan GmbH");
    expect(names).toContain("Kyritzer Fruchtsäfte");
    expect(names).toHaveLength(clientLocations.length - 2);
  });
});

describe("Kartenkomponenten nutzen die deduplizierte Quelle", () => {
  it("uebergibt der ReferenceMap nirgends die ungefilterten clientLocations", () => {
    const astroFiles = collectAstroFiles(join(process.cwd(), "src"));
    const mapConsumers = astroFiles.filter((file) =>
      readFileSync(file, "utf8").includes("<ReferenceMap"),
    );

    expect(mapConsumers.length).toBeGreaterThan(0);
    for (const file of mapConsumers) {
      const source = readFileSync(file, "utf8");
      expect(
        /clients=\{\s*clientLocations\s*\}/.test(source),
        `${file} uebergibt die ungefilterte Standortliste an ReferenceMap`,
      ).toBe(false);
    }
  });
});

describe("Freigabe-Guard fuer Kundenstandorte", () => {
  // Schuetzt die ID-Zuordnung: wer einen Standort ergaenzt, der dieselbe Firma
  // wie eine Referenz meint, muss die referenceId setzen — sonst schlaegt der
  // Test fehl, statt dass das Duplikat still auf die Startseite geht.
  const normalize = (value: string) =>
    value
      .toLowerCase()
      .replace(/\b(gmbh|ag|kg|co|eg|mbh|und|&)\b/g, "")
      .replace(/[^a-z0-9]/g, "");

  it("verlangt eine referenceId, wenn ein Standort ein Referenz-Logo wiederverwendet", () => {
    const referenceLogos = new Set(
      references.flatMap((reference) =>
        reference.logo ? [reference.logo] : [],
      ),
    );

    for (const location of clientLocations) {
      if (!("logo" in location)) continue;
      if (!referenceLogos.has(location.logo)) continue;

      expect(
        "referenceId" in location,
        `Kundenstandort "${location.name}" nutzt das Referenz-Logo ${location.logo} ohne referenceId`,
      ).toBe(true);
    }
  });

  it("verlangt eine referenceId, wenn ein Standort denselben Firmennamen wie eine Referenz traegt", () => {
    const referenceNames = new Map(
      references.map((reference) => [
        normalize(reference.publicName),
        reference.id,
      ]),
    );

    for (const location of clientLocations) {
      const matchedId = referenceNames.get(normalize(location.name));
      if (!matchedId) continue;

      expect(
        "referenceId" in location,
        `Kundenstandort "${location.name}" entspricht Referenz "${matchedId}" ohne referenceId`,
      ).toBe(true);
    }
  });

  it("zeigt jede referenceId auf eine real existierende Referenz", () => {
    const knownIds = new Set(references.map((reference) => reference.id));

    for (const location of clientLocations) {
      if (!("referenceId" in location)) continue;

      expect(
        knownIds.has(location.referenceId),
        `Kundenstandort "${location.name}" verweist auf unbekannte Referenz "${location.referenceId}"`,
      ).toBe(true);
    }
  });
});
