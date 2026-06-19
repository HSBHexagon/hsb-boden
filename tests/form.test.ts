import { describe, expect, it } from "vitest";
import { leadFormSchema } from "../src/lib/validation";

describe("lead form validation", () => {
  const validPayload = {
    firstName: "Max",
    lastName: "Mustermann",
    company: "Muster Produktion GmbH",
    email: "max@example.com",
    phone: "+49 123 456789",
    industry: "molkerei",
    projectType: "sanierung",
    areaSize: "450",
    currentFloor: "Keramik mit Fugenschäden",
    loads: ["Säuren/Laugen", "Hochdruckreinigung"],
    liveOperation: "ja",
    timeframe: "Q3 2026",
    message: "Bitte Belastungsprofil prüfen.",
    privacyConsent: true,
  };

  it("accepts a complete qualified B2B inquiry", () => {
    const result = leadFormSchema.safeParse(validPayload);

    expect(result.success).toBe(true);
  });

  it("blocks submissions without privacy consent", () => {
    const result = leadFormSchema.safeParse({
      ...validPayload,
      privacyConsent: false,
    });

    expect(result.success).toBe(false);
  });

});
