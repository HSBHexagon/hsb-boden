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
  customerName: z.boolean(),
  exactLocation: z.boolean(),
  logo: z.boolean(),
  metrics: z.boolean(),
  quote: z.boolean(),
  images: z.boolean(),
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

export function getPublishableTeamProfiles(items: TeamProfileDraft[]): TeamProfileDraft[] {
  return items.flatMap((item) => {
    const parsed = teamProfileDraftSchema.safeParse(item);
    if (!parsed.success) return [];

    const profile = parsed.data;
    if (
      profile.status !== "approved" ||
      profile.evidenceRefs.length === 0 ||
      !profile.publicationConsentRef
    ) {
      return [];
    }

    if (profile.image && !profile.imageRightsRef) {
      const { image: _image, ...withoutUnclearedImage } = profile;
      return [withoutUnclearedImage as TeamProfileDraft];
    }

    return [profile];
  });
}

export function getPublishableCaseStudies(items: CaseStudyDraft[]) {
  return items.flatMap((item) => {
    const parsed = caseStudyDraftSchema.safeParse(item);
    if (!parsed.success) return [];

    const study = parsed.data;
    if (
      study.status !== "approved" ||
      study.evidenceRefs.length === 0 ||
      !study.publicationApprovalRef
    ) {
      return [];
    }

    return [
      {
        ...study,
        customerName: study.approvals.customerName ? study.customerName : undefined,
        exactLocation: study.approvals.exactLocation ? study.exactLocation : undefined,
        logo: study.approvals.logo ? study.logo : undefined,
        metrics: study.approvals.metrics ? (study.metrics ?? []) : [],
        quote: study.approvals.quote ? study.quote : undefined,
        images: study.approvals.images ? (study.images ?? []) : [],
      },
    ];
  });
}
