import { articles } from "../data/articles";
import { clientLocations } from "../data/clientLocations";
import { industries } from "../data/industries";
import { jobs } from "../data/jobs";
import { staticPublicPages } from "../data/publicPages";
import { references } from "../data/references";
import { services } from "../data/services";
import { landing } from "./i18n";
import {
  serviceSchema,
  industrySchema,
  referenceSchema,
  articleSchema,
  type Service,
} from "./types";

export function validateSiteContent() {
  const errors: string[] = [];
  for (const service of services) {
    const result = serviceSchema.safeParse(service);
    if (!result.success)
      errors.push(`service:${service.slug}:${result.error.message}`);
  }
  for (const industry of industries) {
    const result = industrySchema.safeParse(industry);
    if (!result.success)
      errors.push(`industry:${industry.slug}:${result.error.message}`);
  }
  for (const reference of references) {
    const result = referenceSchema.safeParse(reference);
    if (!result.success)
      errors.push(`reference:${reference.id}:${result.error.message}`);
  }
  for (const article of articles) {
    const result = articleSchema.safeParse(article);
    if (!result.success)
      errors.push(`article:${article.slug}:${result.error.message}`);
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

const servicesMap = new Map<string, Service>(
  services.map((s) => [s.slug, s as unknown as Service]),
);

export function getServiceBySlug(slug: string) {
  return servicesMap.get(slug);
}

export function getPublicReferences() {
  return references
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
        displayLocation: canShowExactLocation
          ? `${reference.city}, ${reference.region}`
          : reference.region,
        canShowExactLocation,
        logo: canShowLogo ? reference.logo : undefined,
      };
    });
}

// Dieselbe Firma kann freigegebene Referenz UND Kundenstandort sein. Beide
// Quellen zusammenzufuehren erzeugte auf der Startseite Duplikate (LogoCloud,
// Kartenmarker, Standortliste). Zugeordnet wird ueber die kanonische
// referenceId aus clientLocations, nicht ueber Namensvergleich; der Guard in
// tests/reference-deduplication.test.ts erzwingt, dass die ID gesetzt ist.

/**
 * Logos fuer den LogoCloud der Startseite. Die freigegebene Referenz hat
 * Vorrang vor dem Kundenstandort-Eintrag derselben Firma.
 */
export interface LogoCloudEntry {
  id: string;
  name: string;
  logo: string;
  meta: string;
  industry?: string;
  systems: string[];
  proofTag: string;
}

// Technische Kurzlabels je Leistungs-Slug. Proof-Tags entstehen nur aus den in
// references.ts dokumentierten Systemen — kein Freitext je Kunde.
const SYSTEM_PROOF_LABELS: Record<string, string> = {
  "industrieboden-saeureschutz": "Säureschutz",
  "whg-abdichtung-industrieboden": "WHG § 62 Abdichtung",
  "keramische-industrieboeden": "Rüttelkeramik",
  "entwaesserung-industrieboden": "Entwässerung",
  "pu-beton-industrieboden": "PU-Beton",
  "epoxidharz-bodenbeschichtung": "Epoxidharz-Beschichtung",
  "dehnungsfugen-rammschutz-industrieboden": "Dehnungsfugen & Rammschutz",
  "bodensanierung-laufender-betrieb": "Sanierung im Betrieb",
  "boden-reparatur-instandsetzung": "Reparatur & Instandsetzung",
};

// Freitext-Branche der Kundenstandorte -> kanonischer Branchen-Slug.
const LOCATION_BRANCHE_TO_INDUSTRY: Record<string, string> = {
  Molkerei: "molkerei",
  Brauerei: "brauerei-getraenkeindustrie",
  Getränke: "brauerei-getraenkeindustrie",
  Lebensmittel: "lebensmittelindustrie",
  Chemie: "chemieindustrie",
  Pharma: "pharmaindustrie",
};

function buildProofTag(systems: string[]): string {
  return systems
    .map((slug) => SYSTEM_PROOF_LABELS[slug])
    .filter((label): label is string => Boolean(label))
    .slice(0, 2)
    .join(" & ");
}

export function getLogoCloudEntries(industryFilter?: string): LogoCloudEntry[] {
  // Bewusst nur gegen die Referenzen deduplizieren, die hier tatsaechlich ein
  // Logo rendern: eine Referenz ohne Logo-Freigabe darf ein separat
  // freigegebenes Standort-Logo nicht stillschweigend unterdruecken.
  const referencesWithLogo = getPublicReferences().filter(
    (reference) => reference.logo,
  );
  const renderedReferenceIds = new Set(
    referencesWithLogo.map((reference) => reference.id),
  );

  const referenceEntries: LogoCloudEntry[] = referencesWithLogo.map((reference) => ({
    id: reference.id,
    name: reference.displayName,
    logo: reference.logo as string,
    meta: "Referenzprojekt",
    industry: reference.industry,
    systems: [...reference.systems],
    proofTag: buildProofTag([...reference.systems]),
  }));

  const locationEntries: LogoCloudEntry[] = clientLocations
    .filter((location) => "logo" in location)
    .filter(
      (location) =>
        !("referenceId" in location) ||
        !renderedReferenceIds.has(location.referenceId),
    )
    .map((location) => ({
      id: `standort-${location.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
      name: location.name,
      logo: location.logo,
      meta: location.branche,
      industry: LOCATION_BRANCHE_TO_INDUSTRY[location.branche],
      systems: [],
      proofTag: `Kundenstandort ${location.branche}`,
    }));

  const entries = [...referenceEntries, ...locationEntries];
  if (!industryFilter) return entries;

  // Rang 2: Branche identisch. Rang 1: mindestens ein System gehört zu den
  // empfohlenen Systemen der gefilterten Branche (z. B. Südzucker bei Chemie
  // über Säureschutz/WHG). Rang 0: Rest. Sortierung ist stabil.
  const industry = getIndustries().find((item) => item.slug === industryFilter);
  const affineSystems = new Set(industry?.recommendedSystems ?? []);
  const rank = (entry: LogoCloudEntry) => {
    if (entry.industry === industryFilter) return 2;
    if (entry.systems.some((slug) => affineSystems.has(slug))) return 1;
    return 0;
  };
  return entries
    .map((entry, index) => ({ entry, index, rank: rank(entry) }))
    .sort((a, b) => b.rank - a.rank || a.index - b.index)
    .map((item) => item.entry);
}

/**
 * Kundenstandorte ohne die Firmen, die bereits als oeffentliche Referenz
 * erscheinen — verhindert doppelte Kartenmarker und Doppelnennungen in der
 * Liste "Weitere Kundenstandorte".
 */
export function getSupplementalClientLocations() {
  const publicReferenceIds = new Set(
    getPublicReferences().map((reference) => reference.id),
  );

  return clientLocations.filter(
    (location) =>
      !("referenceId" in location) ||
      !publicReferenceIds.has(location.referenceId),
  );
}

export function getReferencesForSlugs(referenceIds: string[]) {
  const allowed = new Set(referenceIds);
  return getPublicReferences().filter((reference) => allowed.has(reference.id));
}

export function getAllPublicPages() {
  return [
    ...staticPublicPages,
    ...jobs.map((job) => ({
      h1: job.title,
      seoTitle: job.seoTitle,
      description: job.shortDescription,
      canonicalPath: `/karriere/${job.slug}/`,
    })),
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
