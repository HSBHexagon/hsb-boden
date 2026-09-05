import { describe, expect, it } from "vitest";
import {
  publicationStatusSchema,
  qualificationSchema,
  teamProfileDraftSchema,
  caseStudyMetricSchema,
  caseStudyQuoteSchema,
  caseStudyImageSchema,

  caseStudyDraftSchema,
  getPublishableTeamProfiles,
  getPublishableCaseStudies,
  type TeamProfileDraft,
  type CaseStudyDraft
} from "../src/lib/trust";

describe("Trust Data Schemas", () => {
  describe("publicationStatusSchema", () => {
    it("accepts valid statuses", () => {
      expect(publicationStatusSchema.parse("draft")).toBe("draft");
      expect(publicationStatusSchema.parse("verified")).toBe("verified");
      expect(publicationStatusSchema.parse("approved")).toBe("approved");
    });

    it("rejects invalid statuses", () => {
      expect(() => publicationStatusSchema.parse("invalid")).toThrow();
      expect(() => publicationStatusSchema.parse("")).toThrow();
    });
  });

  describe("qualificationSchema", () => {
    it("accepts valid qualification", () => {
      expect(qualificationSchema.parse({
        label: "B.Sc. Computer Science",
        evidenceRef: "internal://evidence/1",
      })).toEqual({
        label: "B.Sc. Computer Science",
        evidenceRef: "internal://evidence/1",
      });
    });

    it("rejects invalid qualification", () => {
      expect(() => qualificationSchema.parse({ label: "A", evidenceRef: "ref" })).toThrow(); // label min 3
      expect(() => qualificationSchema.parse({ label: "Valid", evidenceRef: "" })).toThrow(); // evidenceRef min 1
      expect(() => qualificationSchema.parse({ label: "Valid" })).toThrow(); // missing evidenceRef
    });
  });

  describe("teamProfileDraftSchema", () => {
    const validProfile = {
      id: "prof-1",
      status: "draft",
      name: "John Doe",
      role: "Engineer",
      shortBio: "This is a sufficiently long bio for the profile.",
      image: "/images/john.jpg",
      imageRightsRef: "ref-1",
      evidenceRefs: ["ref-2"],
      publicationConsentRef: "ref-3",
      qualifications: [{ label: "Degree", evidenceRef: "ref-4" }],
    };

    it("accepts a valid team profile draft", () => {
      expect(teamProfileDraftSchema.parse(validProfile)).toEqual(validProfile);
    });

    it("rejects team profile with missing required fields", () => {
      const { name, ...missingName } = validProfile;
      expect(() => teamProfileDraftSchema.parse(missingName)).toThrow();
    });

    it("rejects short fields", () => {
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, id: "ab" })).toThrow();
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, name: "A" })).toThrow();
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, role: "A" })).toThrow();
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, shortBio: "Short" })).toThrow(); // min 20
    });

    it("rejects invalid image path", () => {
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, image: "images/john.jpg" })).toThrow(); // must start with /
    });
  });

  describe("caseStudyMetricSchema", () => {
    it("accepts valid metric", () => {
      expect(caseStudyMetricSchema.parse({ label: "ROI", value: "200%", evidenceRef: "ref" })).toBeTruthy();
    });
    it("rejects invalid metric", () => {
      expect(() => caseStudyMetricSchema.parse({ label: "R", value: "200%", evidenceRef: "ref" })).toThrow(); // min 2
      expect(() => caseStudyMetricSchema.parse({ label: "ROI", value: "", evidenceRef: "ref" })).toThrow(); // min 1
    });
  });

  describe("caseStudyQuoteSchema", () => {
    it("accepts valid quote", () => {
      expect(caseStudyQuoteSchema.parse({ text: "Great!", source: "Client", evidenceRef: "ref" })).toBeTruthy();
    });
    it("rejects invalid quote", () => {
      expect(() => caseStudyQuoteSchema.parse({ text: "Bad", source: "Client", evidenceRef: "ref" })).toThrow(); // min 5
      expect(() => caseStudyQuoteSchema.parse({ text: "Great!", source: "C", evidenceRef: "ref" })).toThrow(); // min 2
    });
  });

  describe("caseStudyImageSchema", () => {
    it("accepts valid image", () => {
      expect(caseStudyImageSchema.parse({ src: "/img.jpg", alt: "A nice image", rightsRef: "ref" })).toBeTruthy();
    });
    it("rejects invalid image", () => {
      expect(() => caseStudyImageSchema.parse({ src: "img.jpg", alt: "A nice image", rightsRef: "ref" })).toThrow(); // startsWith /
      expect(() => caseStudyImageSchema.parse({ src: "/img.jpg", alt: "Short", rightsRef: "ref" })).toThrow(); // min 10
    });
  });

  describe("caseStudyDraftSchema", () => {
    const validCaseStudy = {
      id: "case-1",
      status: "draft",
      industry: "Tech",
      challenge: "This was a huge challenge.",
      solution: "This is the solution.",
      outcome: "This is the outcome.",
      evidenceRefs: ["ref-1"],
      approvals: {}
    };

    it("accepts a valid case study draft", () => {
      expect(caseStudyDraftSchema.parse(validCaseStudy)).toEqual(validCaseStudy);
    });

    it("rejects with missing required fields", () => {
      const { industry, ...missing } = validCaseStudy;
      expect(() => caseStudyDraftSchema.parse(missing)).toThrow();
    });

    it("rejects short string fields", () => {
      expect(() => caseStudyDraftSchema.parse({ ...validCaseStudy, challenge: "Short" })).toThrow(); // min 10
    });
  });
});

describe("Filtering Functions", () => {
  const baseProfile: TeamProfileDraft = {
    id: "prof-1",
    status: "approved",
    name: "John Doe",
    role: "Engineer",
    shortBio: "This is a sufficiently long bio for the profile.",
    evidenceRefs: ["ref-1"],
    publicationConsentRef: "ref-2",
    qualifications: [],
  };

  describe("getPublishableTeamProfiles", () => {
    it("filters out profiles that fail schema validation (e.g. missing required fields)", () => {
      const invalidProfile = { ...baseProfile, name: "A" }; // Invalid length
      // Need to cast to any to pass invalid data
      const results = getPublishableTeamProfiles([baseProfile, invalidProfile as any]);
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("prof-1");
    });
  });

  const baseCaseStudy: CaseStudyDraft = {
    id: "case-1",
    status: "approved",
    industry: "Tech",
    challenge: "This was a huge challenge.",
    solution: "This is the solution.",
    outcome: "This is the outcome.",
    evidenceRefs: ["ref-1"],
    publicationApprovalRef: "ref-2",
    approvals: {}
  };

  describe("getPublishableCaseStudies", () => {
    it("filters out case studies that fail schema validation", () => {
      const invalidCaseStudy = { ...baseCaseStudy, industry: "A" }; // Invalid length
      const results = getPublishableCaseStudies([baseCaseStudy, invalidCaseStudy as any]);
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("case-1");
    });
  });
});
