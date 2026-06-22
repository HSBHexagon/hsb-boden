import { describe, expect, it } from "vitest";
import { leadEndpointSchema } from "../src/lib/leadSchema";

describe("leadEndpointSchema", () => {
  const validPayload = {
    firstName: "Max",
    lastName: "Mustermann",
    company: "Muster Produktion GmbH",
    email: "max@example.com",
    phone: "+49 123 456789",
    industry: "molkerei",
    projectType: "sanierung",
    areaSize: "450",
    liveOperation: "ja",
    loads: ["Säuren/Laugen", "Hochdruckreinigung"],
    message: "Bitte Belastungsprofil prüfen, Fugen sind beschädigt.",
    privacyConsent: true,
    source: "website",
    legalBasis: "inquiry",
  };

  it("accepts a complete, valid lead payload", () => {
    const result = leadEndpointSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("rejects when privacyConsent is not true", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, privacyConsent: false });
    expect(result.success).toBe(false);
  });

  it("rejects when loads is empty", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, loads: [] });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("rejects message shorter than 10 characters", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, message: "zu kurz" });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown projectType value", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, projectType: "abriss" });
    expect(result.success).toBe(false);
  });

  it("rejects a filled honeypot field", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, honeypot: "spam-bot-filled-this" });
    expect(result.success).toBe(false);
  });

  it("accepts an absent honeypot field", () => {
    const result = leadEndpointSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("strips unknown fields instead of accepting them", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, injectedField: "drop-me" });
    expect(result.success).toBe(true);
    if (result.success) {
      expect("injectedField" in result.data).toBe(false);
    }
  });

  it("accepts optional access_key and utm fields when present", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      access_key: "abc123",
      utm_source: "google",
      utm_medium: "cpc",
      utm_campaign: "leistungen",
    });
    expect(result.success).toBe(true);
  });
});
