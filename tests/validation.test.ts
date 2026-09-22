import { describe, it, expect } from "vitest";
import { leadFormSchema, serializeLeadPayload } from "../src/lib/validation";

describe("Validation and Serialization", () => {
  const validPayload = {
    firstName: "John",
    lastName: "Doe",
    company: "Acme Corp",
    email: "john.doe@example.com",
    phone: "12345",
    industry: "Manufacturing",
    projectType: "New Construction",
    areaSize: "500 sqm",
    currentFloor: "Concrete",
    loads: ["Säuren/Laugen", "Fette/Öle"],
    liveOperation: "Yes",
    timeframe: "Q3 2024",
    message: "We need a new floor.",
    privacyConsent: true as const,
  };

  describe("leadFormSchema", () => {
    it("should successfully parse a valid payload", () => {
      const parsed = leadFormSchema.safeParse(validPayload);
      expect(parsed.success).toBe(true);
    });

    it("should require firstName to be at least 2 characters", () => {
      const payload = { ...validPayload, firstName: "A" };
      const parsed = leadFormSchema.safeParse(payload);
      expect(parsed.success).toBe(false);
    });

    it("should require a valid email address", () => {
      const payload = { ...validPayload, email: "invalid-email" };
      const parsed = leadFormSchema.safeParse(payload);
      expect(parsed.success).toBe(false);
    });

    it("should require privacyConsent to be literal true", () => {

      const payload = { ...validPayload, privacyConsent: false };
      const parsed = leadFormSchema.safeParse(payload);
      expect(parsed.success).toBe(false);
    });

    it("should require loads array to have at least 1 item", () => {
      const payload = { ...validPayload, loads: [] };
      const parsed = leadFormSchema.safeParse(payload);
      expect(parsed.success).toBe(false);
    });

    it("should allow optional fields to be missing", () => {
      const { areaSize, currentFloor, timeframe, ...minimalPayload } = validPayload;
      const parsed = leadFormSchema.safeParse(minimalPayload);
      expect(parsed.success).toBe(true);
    });
  });

  describe("serializeLeadPayload", () => {
    it("should successfully serialize a valid payload with all fields", () => {
      const serialized = serializeLeadPayload(validPayload);
      expect(serialized).toEqual({
        source: "website",
        legalBasis: "inquiry",
        optOutStatus: "not_applicable",
        firstName: validPayload.firstName,
        lastName: validPayload.lastName,
        company: validPayload.company,
        email: validPayload.email,
        phone: validPayload.phone,
        industry: validPayload.industry,
        projectType: validPayload.projectType,
        areaSize: validPayload.areaSize,
        currentFloor: validPayload.currentFloor,
        systemInterest: "Säuren/Laugen, Fette/Öle",
        liveOperation: validPayload.liveOperation,
        timeframe: validPayload.timeframe,
        message: validPayload.message,
      });
    });

    it("should successfully serialize a valid payload with missing optional fields", () => {
      const { areaSize, currentFloor, timeframe, ...minimalPayload } = validPayload;
      const serialized = serializeLeadPayload(minimalPayload);
      expect(serialized).toEqual({
        source: "website",
        legalBasis: "inquiry",
        optOutStatus: "not_applicable",
        firstName: minimalPayload.firstName,
        lastName: minimalPayload.lastName,
        company: minimalPayload.company,
        email: minimalPayload.email,
        phone: minimalPayload.phone,
        industry: minimalPayload.industry,
        projectType: minimalPayload.projectType,
        areaSize: "",
        currentFloor: "",
        systemInterest: "Säuren/Laugen, Fette/Öle",
        liveOperation: minimalPayload.liveOperation,
        timeframe: "",
        message: minimalPayload.message,
      });
    });

    it("should throw an error if the payload is invalid", () => {
      const invalidPayload = { ...validPayload, email: "invalid-email" };
      expect(() => serializeLeadPayload(invalidPayload)).toThrow();
    });
  });
});
