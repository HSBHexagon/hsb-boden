import { describe, expect, it } from "vitest";
import { consentCategories, getRequiredConsentCategories } from "../src/data/consent";
import { resolveSuggestedLanguages, supportedLanguages } from "../src/data/localization";

describe("localized consent and language experience", () => {
  it("offers more than Turkish and English for international visitors", () => {
    expect(supportedLanguages.map((language) => language.code)).toEqual([
      "de",
      "en",
      "tr",
      "pl",
      "fr",
      "nl",
      "es",
    ]);
  });

  it("suggests Turkish first for Turkish browser locales, then English and German", () => {
    expect(resolveSuggestedLanguages("tr-TR").map((language) => language.code).slice(0, 3)).toEqual([
      "tr",
      "en",
      "de",
    ]);
  });

  it("falls back to English and German for unsupported browser locales", () => {
    expect(resolveSuggestedLanguages("pt-BR").map((language) => language.code).slice(0, 2)).toEqual([
      "en",
      "de",
    ]);
  });

  it.each(["es-ES", "es-MX", "es-AR"])("suggests Spanish first for %s without duplicates", (locale) => {
    const codes = resolveSuggestedLanguages(locale).map((language) => language.code);
    expect(codes.slice(0, 3)).toEqual(["es", "en", "de"]);
    expect(new Set(codes).size).toBe(codes.length);
  });

  it("keeps essential cookies as the only mandatory category", () => {
    expect(consentCategories.map((category) => category.id)).toEqual([
      "essential",
      "analytics",
      "marketing",
    ]);
    expect(getRequiredConsentCategories()).toEqual(["essential"]);
  });
});
