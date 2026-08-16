import { describe, expect, it } from "vitest";
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
    expect(resolveSuggestedLanguages("es-ES").map((language) => language.code).slice(0, 2)).toEqual([
      "en",
      "de",
    ]);
  });

});
