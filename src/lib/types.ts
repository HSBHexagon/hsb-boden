import { z } from "zod";

export const faqSchema = z.object({
  question: z.string().min(10),
  answer: z.string().min(25),
});

export const serviceSchema = z.object({
  slug: z.string().min(3),
  title: z.string().min(3),
  seoTitle: z.string().min(20),
  description: z.string().min(70),
  h1: z.string().min(10),
  primaryKeyword: z.string().min(3),
  secondaryKeywords: z.array(z.string()).min(1),
  problem: z.string().min(40),
  applications: z.array(z.string()).min(1),
  technicalRequirements: z.array(z.string()).min(3),
  systemSolution: z.string().min(40),
  benefits: z.array(z.string()).min(3),
  decisionCriteria: z.array(z.string()).min(3),
  relatedIndustries: z.array(z.string()),
  relatedReferences: z.array(z.string()),
  relatedArticles: z.array(z.string()).default([]),
  faqs: z.array(faqSchema).min(1),
  ctaLabel: z.string().min(5),
  ctaTarget: z.string().startsWith("/"),
});

export const industrySchema = z.object({
  slug: z.string().min(3),
  title: z.string().min(3),
  seoTitle: z.string().min(20),
  description: z.string().min(70),
  h1: z.string().min(10),
  searchIntent: z.string().min(40),
  typicalProblems: z.array(z.string()).min(3),
  floorRequirements: z.array(z.string()).min(3),
  recommendedSystems: z.array(z.string()).min(1),
  proofPoints: z.array(z.string()).min(2),
  relatedServices: z.array(z.string()).min(1),
  relatedReferences: z.array(z.string()),
  relatedArticles: z.array(z.string()).default([]),
  faqs: z.array(faqSchema).min(1),
  ctaLabel: z.string().min(5),
});

export const referenceSchema = z.object({
  id: z.string().min(3),
  publicName: z.string().min(3),
  anonymousName: z.string().min(3),
  canShowLogo: z.boolean(),
  canShowExactLocation: z.boolean(),
  industry: z.string().min(3),
  city: z.string().min(2),
  region: z.string().min(2),
  country: z.string().min(2),
  lat: z.number(),
  lng: z.number(),
  systems: z.array(z.string()).min(1),
  projectType: z.string().min(3),
  challenge: z.string().min(20),
  solution: z.string().min(20),
  result: z.string().min(20),
  images: z.array(z.string()),
  logo: z.string().optional(),
  year: z.string().min(4),
  approvalStatus: z.enum(["approved", "anonymous", "internal"]),
});

export const articleSchema = z.object({
  slug: z.string().min(3),
  title: z.string().min(3),
  seoTitle: z.string().min(20),
  description: z.string().min(70),
  h1: z.string().min(10),
  category: z.string().min(3),
  readTime: z.string().min(3),
  intro: z.string().min(50),
  sections: z
    .array(
      z.object({
        title: z.string().min(3),
        body: z.string().min(20).optional(),
      }),
    )
    .min(3),
  relatedServices: z.array(z.string()).default([]),
  relatedIndustries: z.array(z.string()).default([]),
});

export type Service = z.infer<typeof serviceSchema>;
export type Industry = z.infer<typeof industrySchema>;
export type Article = z.infer<typeof articleSchema>;
export type ReferenceRecord = z.infer<typeof referenceSchema>;
