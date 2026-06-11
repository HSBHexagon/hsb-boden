import { z } from "zod";
import { articles } from "../data/articles";
import { industries } from "../data/industries";
import { references } from "../data/references";
import { services } from "../data/services";

const faqSchema = z.object({
  question: z.string().min(10),
  answer: z.string().min(25),
});

const serviceSchema = z.object({
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
  faqs: z.array(faqSchema).min(1),
  ctaLabel: z.string().min(5),
  ctaTarget: z.string().startsWith("/"),
});

const industrySchema = z.object({
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
  faqs: z.array(faqSchema).min(1),
  ctaLabel: z.string().min(5),
});

const referenceSchema = z.object({
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

const articleSchema = z.object({
  slug: z.string().min(3),
  title: z.string().min(3),
  seoTitle: z.string().min(20),
  description: z.string().min(70),
  h1: z.string().min(10),
  category: z.string().min(3),
  readTime: z.string().min(3),
  intro: z.string().min(50),
  sections: z.array(z.object({
    title: z.string().min(10),
    content: z.string().min(50),
  })).min(3),
});

export type Service = (typeof services)[number];
export type Industry = (typeof industries)[number];
export type Article = (typeof articles)[number];
export type ReferenceRecord = (typeof references)[number];

export function validateSiteContent() {
  const errors: string[] = [];
  for (const service of services) {
    const result = serviceSchema.safeParse(service);
    if (!result.success) errors.push(`service:${service.slug}:${result.error.message}`);
  }
  for (const industry of industries) {
    const result = industrySchema.safeParse(industry);
    if (!result.success) errors.push(`industry:${industry.slug}:${result.error.message}`);
  }
  for (const reference of references) {
    const result = referenceSchema.safeParse(reference);
    if (!result.success) errors.push(`reference:${reference.id}:${result.error.message}`);
  }
  for (const article of articles) {
    const result = articleSchema.safeParse(article);
    if (!result.success) errors.push(`article:${article.slug}:${result.error.message}`);
  }

  return { success: errors.length === 0, errors };
}

export function getServices() {
  return services;
}

export function getIndustries() {
  return industries;
}

export function getArticles() {
  return articles;
}

export function getServiceBySlug(slug: string) {
  return services.find((service) => service.slug === slug);
}

export function getIndustryBySlug(slug: string) {
  return industries.find((industry) => industry.slug === slug);
}

export function getArticleBySlug(slug: string) {
  return articles.find((article) => article.slug === slug);
}

export function getReferenceById(id: string) {
  return references.find((reference) => reference.id === id);
}

export function getPublicReferences() {
  return (references as readonly ReferenceRecord[])
    .filter((reference) => {
      const approvalStatus: string = reference.approvalStatus;
      return approvalStatus !== "internal";
    })
    .map((reference) => {
      const approved = reference.approvalStatus === "approved";
      const canShowLogo = approved && reference.canShowLogo;
      const canShowExactLocation = approved && reference.canShowExactLocation;

      return {
        ...reference,
        displayName: approved ? reference.publicName : reference.anonymousName,
        displayLocation: canShowExactLocation ? `${reference.city}, ${reference.region}` : reference.region,
        canShowExactLocation,
        logo: canShowLogo ? reference.logo : undefined,
      };
    });
}

export function getReferencesForSlugs(referenceIds: string[]) {
  const allowed = new Set(referenceIds);
  return getPublicReferences().filter((reference) => allowed.has(reference.id));
}

export function getAllPublicPages() {
  return [
    {
      h1: "Industrieböden und Säureschutzsysteme für produktionskritische Bereiche",
      seoTitle: "Industrieböden & Säureschutz für Produktion | HSB Hexagon Säurebau",
      description:
        "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion. Jetzt kostenlose Ersteinschätzung anfordern.",
      canonicalPath: "/",
    },
    {
      h1: "Leistungen für Industrieböden und Säureschutz",
      seoTitle: "Leistungen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Keramische Industrieböden, Säureschutz, PU-Beton, Epoxidharz, Entwässerung, Abdichtung und Sanierung für produktionskritische Bereiche.",
      canonicalPath: "/leistungen/",
    },
    {
      h1: "Branchenspezifische Industrieböden",
      seoTitle: "Industrieböden nach Branche | HSB Hexagon Säurebau",
      description:
        "Industrieböden für Lebensmittelindustrie, Molkereien, Brauereien, Chemie, Pharma, Backwarenproduktion und Großküchen.",
      canonicalPath: "/branchen/",
    },
    {
      h1: "Referenzen aus produktionskritischen Bereichen",
      seoTitle: "Referenzen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Ausgewählte freigegebene und anonymisierte Referenzen für Industrieböden, Säureschutz, Keramik, Entwässerung und Sanierung.",
      canonicalPath: "/referenzen/",
    },
    {
      h1: "Wissen zu Industrieböden, Säureschutz und Sanierung",
      seoTitle: "Wissen zu Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Praxisnahes Wissen zu PU-Beton, keramischen Industrieböden, Molkereiböden, säurefesten Fliesen, Entwässerung und Sanierung.",
      canonicalPath: "/wissen/",
    },
    {
      h1: "Projektanfrage für Industrieböden",
      seoTitle: "Kontakt & Projektanfrage | HSB Hexagon Säurebau",
      description:
        "Kostenlose Ersteinschätzung anfordern: Anfrageformular für Industrieböden, Säureschutz, Sanierung, Entwässerung und Branchenlösungen.",
      canonicalPath: "/kontakt/",
    },
    {
      h1: "Danke für Ihre Projektanfrage",
      seoTitle: "Danke für Ihre Projektanfrage | HSB Hexagon Säurebau",
      description:
        "Ihre Anfrage wurde vorbereitet. HSB meldet sich zur technischen Bewertung von Industrieboden, Säureschutz oder Sanierung.",
      canonicalPath: "/danke-projektanfrage/",
    },
    {
      h1: "Karriere bei HSB Hexagon Säurebau",
      seoTitle: "Karriere bei HSB Hexagon Säurebau | Industrieboden-Projekte",
      description:
        "Karriere bei HSB: Arbeiten an anspruchsvollen Industrieböden, Säureschutzsystemen und Sanierungsprojekten in Produktionsbetrieben.",
      canonicalPath: "/karriere/",
    },
    ...services.map((service) => ({
      h1: service.h1,
      seoTitle: service.seoTitle,
      description: service.description,
      canonicalPath: `/leistungen/${service.slug}/`,
    })),
    ...industries.map((industry) => ({
      h1: industry.h1,
      seoTitle: industry.seoTitle,
      description: industry.description,
      canonicalPath: `/branchen/${industry.slug}/`,
    })),
    ...articles.map((article) => ({
      h1: article.h1,
      seoTitle: article.seoTitle,
      description: article.description,
      canonicalPath: `/wissen/${article.slug}/`,
    })),
  ];
}
