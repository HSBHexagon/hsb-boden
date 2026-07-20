import { z } from "zod";

export const publicationStatusSchema = z.enum(["draft", "verified", "approved"]);

const evidenceRefSchema = z.string().min(1);

export const qualificationSchema = z.object({
  label: z.string().min(3),
  evidenceRef: evidenceRefSchema,
});

export const teamProfileDraftSchema = z.object({
  id: z.string().min(3),
  status: publicationStatusSchema,
  name: z.string().min(2),
  role: z.string().min(2),
  shortBio: z.string().min(20),
  image: z.string().startsWith("/").optional(),
  imageRightsRef: evidenceRefSchema.optional(),
  evidenceRefs: z.array(evidenceRefSchema),
  publicationConsentRef: evidenceRefSchema.optional(),
  qualifications: z.array(qualificationSchema),
});

export const caseStudyMetricSchema = z.object({
  label: z.string().min(2),
  value: z.string().min(1),
  evidenceRef: evidenceRefSchema,
});

export const caseStudyQuoteSchema = z.object({
  text: z.string().min(5),
  source: z.string().min(2),
  evidenceRef: evidenceRefSchema,
});

export const caseStudyImageSchema = z.object({
  src: z.string().startsWith("/"),
  alt: z.string().min(10),
  rightsRef: evidenceRefSchema,
});

export const caseStudyApprovalsSchema = z.object({
  customerName: evidenceRefSchema.optional(),
  exactLocation: evidenceRefSchema.optional(),
  logo: evidenceRefSchema.optional(),
  metrics: evidenceRefSchema.optional(),
  quote: evidenceRefSchema.optional(),
  images: evidenceRefSchema.optional(),
});

export const caseStudyDraftSchema = z.object({
  id: z.string().min(3),
  status: publicationStatusSchema,
  industry: z.string().min(3),
  challenge: z.string().min(10),
  solution: z.string().min(10),
  outcome: z.string().min(10),
  evidenceRefs: z.array(evidenceRefSchema),
  publicationApprovalRef: evidenceRefSchema.optional(),
  customerName: z.string().min(2).optional(),
  exactLocation: z.string().min(2).optional(),
  logo: z.string().startsWith("/").optional(),
  metrics: z.array(caseStudyMetricSchema).optional(),
  quote: caseStudyQuoteSchema.optional(),
  images: z.array(caseStudyImageSchema).optional(),
  approvals: caseStudyApprovalsSchema,
});

export type PublicationStatus = z.infer<typeof publicationStatusSchema>;
export type TeamProfileDraft = z.infer<typeof teamProfileDraftSchema>;
export type CaseStudyDraft = z.infer<typeof caseStudyDraftSchema>;

export interface PublicTeamProfile {
  id: string;
  name: string;
  role: string;
  shortBio: string;
  image?: string;
  qualifications: Array<{ label: string }>;
}

export interface PublicCaseStudy {
  id: string;
  industry: string;
  challenge: string;
  solution: string;
  outcome: string;
  customerName?: string;
  exactLocation?: string;
  logo?: string;
  metrics: Array<{ label: string; value: string }>;
  quote?: { text: string; source: string };
  images: Array<{ src: string; alt: string }>;
}

// ⚡ Bolt Optimization: Replacing .flatMap() with .reduce() to avoid allocating intermediate arrays for every item
export function getPublishableTeamProfiles(items: TeamProfileDraft[]): PublicTeamProfile[] {
  return items.reduce<PublicTeamProfile[]>((acc, item) => {
    const parsed = teamProfileDraftSchema.safeParse(item);
    if (!parsed.success) return acc;

    const profile = parsed.data;
    if (
      profile.status !== "approved" ||
      profile.evidenceRefs.length === 0 ||
      !profile.publicationConsentRef
    ) {
      return acc;
    }

    acc.push({
      id: profile.id,
      name: profile.name,
      role: profile.role,
      shortBio: profile.shortBio,
      image: profile.image && profile.imageRightsRef ? profile.image : undefined,
      qualifications: profile.qualifications.map(({ label }) => ({ label })),
    });

    return acc;
  }, []);
}

// ⚡ Bolt Optimization: Replacing .flatMap() with .reduce() to avoid allocating intermediate arrays for every item
export function getPublishableCaseStudies(items: CaseStudyDraft[]): PublicCaseStudy[] {
  return items.reduce<PublicCaseStudy[]>((acc, item) => {
    const parsed = caseStudyDraftSchema.safeParse(item);
    if (!parsed.success) return acc;

    const study = parsed.data;
    if (
      study.status !== "approved" ||
      study.evidenceRefs.length === 0 ||
      !study.publicationApprovalRef
    ) {
      return acc;
    }

    acc.push({
      id: study.id,
      industry: study.industry,
      challenge: study.challenge,
      solution: study.solution,
      outcome: study.outcome,
      customerName: study.approvals.customerName ? study.customerName : undefined,
      exactLocation: study.approvals.exactLocation ? study.exactLocation : undefined,
      logo: study.approvals.logo ? study.logo : undefined,
      metrics: study.approvals.metrics
        ? (study.metrics ?? []).map(({ label, value }) => ({ label, value }))
        : [],
      quote: study.approvals.quote && study.quote
        ? { text: study.quote.text, source: study.quote.source }
        : undefined,
      images: study.approvals.images
        ? (study.images ?? []).map(({ src, alt }) => ({ src, alt }))
        : [],
    });

    return acc;
  }, []);
}
