import { articles } from "../data/articles";
import { industries } from "../data/industries";
import { references } from "../data/references";
import { services } from "../data/services";
import { landing } from "./i18n";

export type Service = (typeof services)[number];
export type Industry = (typeof industries)[number];
export type Article = (typeof articles)[number];
export type ReferenceRecord = (typeof references)[number];

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
    ...Object.entries(landing).map(([lang, content]) => ({
      h1: content.hero.h1,
      seoTitle: content.meta.seoTitle,
      description: content.meta.description,
      canonicalPath: `/${lang}/`,
    })),
  ];
}
