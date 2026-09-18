// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import { resolveStressSystem } from "../src/data/stressMatrix";
import {
  STRESS_CHECK_STORAGE_KEY,
  buildLeadPrefill,
  clearStressCheckHandoff,
  loadStressCheckHandoff,
  saveStressCheckHandoff,
} from "../src/lib/stressCheckHandoff";
import { loadOptions } from "../src/lib/validation";

const input = {
  medium: "milchsaeure-molke",
  tempRange: "thermoschock-85",
  mechanicalLoad: "gabelstapler-3-5t",
  timeWindow: "revision-7-14d",
} as const;

beforeEach(() => sessionStorage.clear());

describe("Beanspruchungs-Check → Audit-Formular", () => {
  it("bildet nur Belastungen ab, die das Formular kennt", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    for (const load of prefill.loads) expect(loadOptions).toContain(load);
    expect(prefill.loads).toEqual(expect.arrayContaining(["Säuren/Laugen", "Temperaturwechsel", "Staplerverkehr"]));
  });

  it("leitet Projektart und laufenden Betrieb aus dem Sanierungsfenster ab", () => {
    expect(buildLeadPrefill(input, resolveStressSystem(input)).projectType).toBe("sanierung");
    expect(buildLeadPrefill(input, resolveStressSystem(input)).liveOperation).toBe("ja");
    const neubau = { ...input, timeWindow: "neubau" } as const;
    expect(buildLeadPrefill(neubau, resolveStressSystem(neubau)).projectType).toBe("neubau");
    expect(buildLeadPrefill(neubau, resolveStressSystem(neubau)).liveOperation).toBe("nein");
  });

  it("erzeugt eine technische Nachricht mit allen vier Parametern und dem System", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    expect(prefill.message).toContain("Milchsäure / Molke");
    expect(prefill.message).toContain("Thermoschock / CIP-Reinigung bis 85 °C");
    expect(prefill.message).toContain("Gabelstapler 3–5 t");
    expect(prefill.message).toContain("Revisionsstillstand (7–14 Tage)");
    expect(prefill.message).toContain("AGI S 40 Vibro-Rüttelkeramik mit Kunstharzfuge");
    expect(prefill.message.length).toBeLessThanOrEqual(2000);
  });

  it("überlebt den Seitenwechsel per sessionStorage und lehnt manipulierte Daten ab", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    saveStressCheckHandoff(sessionStorage, prefill);
    expect(loadStressCheckHandoff(sessionStorage)).toEqual(prefill);

    sessionStorage.setItem(STRESS_CHECK_STORAGE_KEY, JSON.stringify({ ...prefill, loads: ["<img>"] }));
    expect(loadStressCheckHandoff(sessionStorage)).toBeUndefined();

    clearStressCheckHandoff(sessionStorage);
    expect(sessionStorage.getItem(STRESS_CHECK_STORAGE_KEY)).toBeNull();
  });
});
