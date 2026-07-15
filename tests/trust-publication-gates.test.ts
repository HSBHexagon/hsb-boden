import { describe, expect, it } from "vitest";
import { caseStudyDrafts, teamProfileDrafts } from "../src/data/trustContent";
import {
  getPublishableCaseStudies,
  getPublishableTeamProfiles,
  type CaseStudyDraft,
  type TeamProfileDraft,
} from "../src/lib/trust";

const approvedTeamProfile: TeamProfileDraft = {
  id: "profile-1",
  status: "approved",
  name: "Freigegebene Person",
  role: "Freigegebene Funktion",
  shortBio: "Freigegebener Kurztext mit belegbarer fachlicher Einordnung.",
  evidenceRefs: ["internal://personnel/profile-1"],
  publicationConsentRef: "internal://consent/profile-1",
  qualifications: [
    { label: "Belegte Qualifikation", evidenceRef: "internal://qualification/profile-1" },
  ],
};

const approvedCaseStudy: CaseStudyDraft = {
  id: "case-1",
  status: "approved",
  industry: "Lebensmittelproduktion",
  challenge: "Freigegebene Ausgangssituation.",
  solution: "Freigegebene technische Lösung.",
  outcome: "Freigegebenes und belegtes Ergebnis.",
  evidenceRefs: ["internal://project/case-1"],
  publicationApprovalRef: "internal://approval/case-1",
  customerName: "Beispielkunde intern",
  exactLocation: "Beispielort intern",
  logo: "/logos/internal.svg",
  metrics: [{ label: "Fläche", value: "100 m²", evidenceRef: "internal://metric/case-1" }],
  quote: { text: "Freigegebenes Zitat", source: "Produktionsleitung", evidenceRef: "internal://quote/case-1" },
  images: [{ src: "/media/internal.webp", alt: "Freigegebenes Projektbild", rightsRef: "internal://rights/case-1" }],
  approvals: {
    customerName: false,
    exactLocation: false,
    logo: false,
    metrics: false,
    quote: false,
    images: false,
  },
};

describe("trust publication gates", () => {
  it("starts without invented team or case-study placeholders", () => {
    expect(teamProfileDrafts).toEqual([]);
    expect(caseStudyDrafts).toEqual([]);
  });

  it("publishes only approved team profiles with evidence and consent", () => {
    expect(
      getPublishableTeamProfiles([
        { ...approvedTeamProfile, id: "draft", status: "draft" },
        { ...approvedTeamProfile, id: "missing-consent", publicationConsentRef: undefined },
        approvedTeamProfile,
      ]),
    ).toEqual([approvedTeamProfile]);
  });

  it("publishes only approved case studies with project evidence and owner approval", () => {
    expect(
      getPublishableCaseStudies([
        { ...approvedCaseStudy, id: "draft", status: "draft" },
        { ...approvedCaseStudy, id: "missing-approval", publicationApprovalRef: undefined },
        approvedCaseStudy,
      ]),
    ).toHaveLength(1);
  });

  it("removes customer-identifying content without individual approvals", () => {
    const [published] = getPublishableCaseStudies([approvedCaseStudy]);

    expect(published.customerName).toBeUndefined();
    expect(published.exactLocation).toBeUndefined();
    expect(published.logo).toBeUndefined();
    expect(published.metrics).toEqual([]);
    expect(published.quote).toBeUndefined();
    expect(published.images).toEqual([]);
  });

  it("retains individually approved and evidenced content", () => {
    const [published] = getPublishableCaseStudies([
      {
        ...approvedCaseStudy,
        approvals: {
          customerName: true,
          exactLocation: true,
          logo: true,
          metrics: true,
          quote: true,
          images: true,
        },
      },
    ]);

    expect(published.customerName).toBe(approvedCaseStudy.customerName);
    expect(published.exactLocation).toBe(approvedCaseStudy.exactLocation);
    expect(published.logo).toBe(approvedCaseStudy.logo);
    expect(published.metrics).toHaveLength(1);
    expect(published.quote).toEqual(approvedCaseStudy.quote);
    expect(published.images).toEqual(approvedCaseStudy.images);
  });
});
