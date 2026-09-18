import { describe, expect, it } from "vitest";
import {
  STRESS_MECHANICAL,
  STRESS_MEDIA,
  STRESS_SYSTEMS,
  STRESS_TEMPERATURES,
  STRESS_TIME_WINDOWS,
  isStressCheckInput,
  resolveStressSystem,
} from "../src/data/stressMatrix";

describe("Beanspruchungs-Matrix", () => {
  it("liefert für jede der 180 Kombinationen deterministisch ein bekanntes System", () => {
    let combinations = 0;
    for (const medium of STRESS_MEDIA) {
      for (const temperature of STRESS_TEMPERATURES) {
        for (const mechanical of STRESS_MECHANICAL) {
          for (const timeWindow of STRESS_TIME_WINDOWS) {
            const input = {
              medium: medium.id,
              tempRange: temperature.id,
              mechanicalLoad: mechanical.id,
              timeWindow: timeWindow.id,
            };
            const first = resolveStressSystem(input);
            const second = resolveStressSystem(input);
            expect(first).toEqual(second);
            expect(STRESS_SYSTEMS[first.system.id]).toBe(first.system);
            expect(first.reasons.length).toBeGreaterThan(0);
            combinations += 1;
          }
        }
      }
    }
    expect(combinations).toBe(180);
  });

  it("Heißdampf > 100 °C erzwingt Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "fette-oele", tempRange: "heissdampf-100", mechanicalLoad: "handhubwagen", timeWindow: "wochenende-48h" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
    expect(result.windowNote).toBeDefined();
  });

  it("Schwerlast mit Vulkollanrollen erzwingt Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "cip-laugen", tempRange: "warmwasser-60", mechanicalLoad: "schwerlast-vulkollan", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
  });

  it("anorganische Säuren ohne Thermoschock führen zur WHG § 62 Fachbeschichtung", () => {
    const result = resolveStressSystem({ medium: "anorganische-saeuren", tempRange: "dauernass-kalt", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("whg-fachbeschichtung");
    expect(result.system.norms).toContain("WHG § 62");
  });

  it("anorganische Säuren mit Thermoschock führen zur Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "anorganische-saeuren", tempRange: "thermoschock-85", mechanicalLoad: "handhubwagen", timeWindow: "neubau" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
  });

  it("Wochenendfenster ohne Zwangskriterium führt zu PU-Beton", () => {
    const result = resolveStressSystem({ medium: "milchsaeure-molke", tempRange: "thermoschock-85", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "wochenende-48h" });
    expect(result.system.id).toBe("pu-beton-hochtemperatur");
  });

  it("Fette/Öle ohne Zwangskriterium führen zu PU-Beton", () => {
    const result = resolveStressSystem({ medium: "fette-oele", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" });
    expect(result.system.id).toBe("pu-beton-hochtemperatur");
  });

  it("organische Säuren und Laugen im Revisionsfenster führen zur Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "milchsaeure-molke", tempRange: "thermoschock-85", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
    expect(result.system.norms).toEqual(["AGI S 40", "DIN EN 14411"]);
  });

  it("Type-Guard akzeptiert nur bekannte IDs", () => {
    expect(isStressCheckInput({ medium: "fette-oele", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" })).toBe(true);
    expect(isStressCheckInput({ medium: "x", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" })).toBe(false);
    expect(isStressCheckInput(null)).toBe(false);
  });

  it("rendert keinen Herstellervergleich im öffentlichen Systemnamen", () => {
    for (const system of Object.values(STRESS_SYSTEMS)) {
      expect(system.name.toLowerCase()).not.toContain("kagetec");
      expect(system.description.toLowerCase()).not.toContain("kagetec");
    }
  });
});
