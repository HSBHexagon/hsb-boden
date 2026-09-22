import { describe, expect, it } from "vitest";
import {
  publicationStatusSchema,
  qualificationSchema,
  teamProfileDraftSchema,
  caseStudyMetricSchema,
  caseStudyQuoteSchema,
  caseStudyImageSchema,
  caseStudyApprovalsSchema,
  caseStudyDraftSchema,
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
      expect(qualificationSchema.parse({ label: "Certified Expert", evidenceRef: "ref-123" })).toEqual({
        label: "Certified Expert",
        evidenceRef: "ref-123",
      });
    });

    it("rejects invalid qualification", () => {
      expect(() => qualificationSchema.parse({ label: "Ce", evidenceRef: "ref-123" })).toThrow(); // label too short
      expect(() => qualificationSchema.parse({ label: "Certified Expert", evidenceRef: "" })).toThrow(); // empty evidenceRef
      expect(() => qualificationSchema.parse({ label: "Certified Expert" })).toThrow(); // missing evidenceRef
    });
  });

  describe("teamProfileDraftSchema", () => {
    const validProfile = {
      id: "profile-123",
      status: "approved",
      name: "John Doe",
      role: "Software Engineer",
      shortBio: "Experienced software engineer with a passion for testing.",
      image: "/images/john.jpg",
      imageRightsRef: "ref-img-123",
      evidenceRefs: ["ref-evidence-1", "ref-evidence-2"],
      publicationConsentRef: "ref-consent-123",
      qualifications: [{ label: "BSc Computer Science", evidenceRef: "ref-bsc" }],
    };

    it("accepts valid full profile", () => {
      expect(teamProfileDraftSchema.parse(validProfile)).toEqual(validProfile);
    });

    it("accepts valid profile with missing optional fields", () => {
      const minimalProfile = {
        id: "profile-123",
        status: "draft",
        name: "John Doe",
        role: "Engineer",
        shortBio: "Short bio that is at least 20 chars long.",
        evidenceRefs: [],
        qualifications: [],
      };
      expect(teamProfileDraftSchema.parse(minimalProfile)).toEqual(minimalProfile);
    });

    it("rejects invalid fields", () => {
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, name: "J" })).toThrow(); // name too short
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, shortBio: "Too short" })).toThrow(); // shortBio too short
      expect(() => teamProfileDraftSchema.parse({ ...validProfile, image: "images/john.jpg" })).toThrow(); // image not starting with /
    });
  });

  describe("caseStudyMetricSchema", () => {
    it("accepts valid metric", () => {
      expect(caseStudyMetricSchema.parse({ label: "Revenue", value: "+20%", evidenceRef: "ref-123" })).toEqual({
        label: "Revenue",
        value: "+20%",
        evidenceRef: "ref-123",
      });
    });

    it("rejects invalid metric", () => {
      expect(() => caseStudyMetricSchema.parse({ label: "R", value: "+20%", evidenceRef: "ref-123" })).toThrow();
      expect(() => caseStudyMetricSchema.parse({ label: "Revenue", value: "", evidenceRef: "ref-123" })).toThrow();
    });
  });

  describe("caseStudyQuoteSchema", () => {
    it("accepts valid quote", () => {
      expect(caseStudyQuoteSchema.parse({ text: "Great work!", source: "Jane Doe", evidenceRef: "ref-123" })).toEqual({
        text: "Great work!",
        source: "Jane Doe",
        evidenceRef: "ref-123",
      });
    });

    it("rejects invalid quote", () => {
      expect(() => caseStudyQuoteSchema.parse({ text: "Bad", source: "Jane Doe", evidenceRef: "ref-123" })).toThrow();
      expect(() => caseStudyQuoteSchema.parse({ text: "Great work!", source: "J", evidenceRef: "ref-123" })).toThrow();
    });
  });

  describe("caseStudyImageSchema", () => {
    it("accepts valid image", () => {
      expect(caseStudyImageSchema.parse({ src: "/images/case1.jpg", alt: "A great case study image", rightsRef: "ref-123" })).toEqual({
        src: "/images/case1.jpg",
        alt: "A great case study image",
        rightsRef: "ref-123",
      });
    });

    it("rejects invalid image", () => {
      expect(() => caseStudyImageSchema.parse({ src: "images/case1.jpg", alt: "A great case study image", rightsRef: "ref-123" })).toThrow(); // src missing /
      expect(() => caseStudyImageSchema.parse({ src: "/images/case1.jpg", alt: "Short alt", rightsRef: "ref-123" })).toThrow(); // alt too short
    });
  });

  describe("caseStudyApprovalsSchema", () => {
    it("accepts all optional fields", () => {
      const approvals = {
        customerName: "ref-1",
        exactLocation: "ref-2",
        logo: "ref-3",
        metrics: "ref-4",
        quote: "ref-5",
        images: "ref-6",
      };
      expect(caseStudyApprovalsSchema.parse(approvals)).toEqual(approvals);
    });

    it("accepts empty object", () => {
      expect(caseStudyApprovalsSchema.parse({})).toEqual({});
    });
  });

  describe("caseStudyDraftSchema", () => {
    const validDraft = {
      id: "case-123",
      status: "approved",
      industry: "Technology",
      challenge: "A significant challenge we faced.",
      solution: "A brilliant solution we implemented.",
      outcome: "A successful outcome achieved.",
      evidenceRefs: ["ref-1"],
      publicationApprovalRef: "ref-2",
      customerName: "Acme Corp",
      exactLocation: "New York, NY",
      logo: "/logos/acme.png",
      metrics: [{ label: "Growth", value: "10x", evidenceRef: "ref-3" }],
      quote: { text: "Best team ever.", source: "CEO", evidenceRef: "ref-4" },
      images: [{ src: "/images/pic1.jpg", alt: "Team photo in the office", rightsRef: "ref-5" }],
      approvals: {
        customerName: "ref-app-1",
      },
    };

    it("accepts valid full draft", () => {
      expect(caseStudyDraftSchema.parse(validDraft)).toEqual(validDraft);
    });

    it("accepts minimal valid draft", () => {
      const minimalDraft = {
        id: "case-123",
        status: "draft",
        industry: "Tech",
        challenge: "A challenge",
        solution: "A solution",
        outcome: "An outcome",
        evidenceRefs: [],
        approvals: {},
      };
      expect(caseStudyDraftSchema.parse(minimalDraft)).toEqual(minimalDraft);
    });

    it("rejects invalid fields", () => {
      expect(() => caseStudyDraftSchema.parse({ ...validDraft, industry: "IT" })).toThrow(); // industry too short
      expect(() => caseStudyDraftSchema.parse({ ...validDraft, challenge: "Short" })).toThrow(); // challenge too short
    });
  });
});
