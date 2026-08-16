import { describe, expect, it } from "vitest";
import { consentCategories, getRequiredConsentCategories } from "../src/data/consent";

describe("localized consent", () => {
  it("keeps essential cookies as the only mandatory category", () => {
    expect(consentCategories.map((category) => category.id)).toEqual([
      "essential",
      "analytics",
      "marketing",
    ]);
    expect(getRequiredConsentCategories()).toEqual(["essential"]);
  });
});
