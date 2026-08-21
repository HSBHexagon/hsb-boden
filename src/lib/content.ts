import { articles } from "../data/articles";
import { clientLocations } from "../data/clientLocations";
import { industries } from "../data/industries";
import { jobs } from "../data/jobs";
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
export function getLogoCloudEntries() {
  // Bewusst nur gegen die Referenzen deduplizieren, die hier tatsaechlich ein
  // Logo rendern: eine Referenz ohne Logo-Freigabe darf ein separat
  // freigegebenes Standort-Logo nicht stillschweigend unterdruecken.
  const referencesWithLogo = getPublicReferences().filter(
    (reference) => reference.logo,
  );
  const renderedReferenceIds = new Set(
    referencesWithLogo.map((reference) => reference.id),
  );

  const referenceEntries = referencesWithLogo.map((reference) => ({
    name: reference.displayName,
    logo: reference.logo as string,
    meta: "Referenzprojekt",
  }));

  const locationEntries = clientLocations
    .filter((location) => "logo" in location)
    .filter(
      (location) =>
        !("referenceId" in location) ||
        !renderedReferenceIds.has(location.referenceId),
    )
    .map((location) => ({
      name: location.name,
      logo: location.logo,
      meta: location.branche,
    }));

  return [...referenceEntries, ...locationEntries];
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
    {
      h1: "Industrieböden und Säureschutzsysteme für produktionskritische Bereiche",
      seoTitle:
        "Industrieböden & Säureschutz für Produktion | HSB Hexagon Säurebau",
      description:
        "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion. Jetzt kostenlose Ersteinschätzung anfordern.",
      canonicalPath: "/",
    },
    {
      h1: "Leistungen für Industrieböden und Säureschutz",
      seoTitle:
        "Leistungen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
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
      seoTitle:
        "Referenzen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Ausgewählte Referenzen für Industrieböden, Säureschutz, Keramik, Entwässerung und Sanierung.",
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
      h1: "Ein klarer Projektablauf für produktionskritische Bodenflächen",
      seoTitle: "Projektablauf für Industrieböden und Säureschutz | HSB",
      description:
        "Vom Belastungsprofil bis zur Abnahme: So strukturiert HSB Analyse, Systemauslegung, Untergrundvorbereitung, Einbau und Dokumentation von Industriebodenprojekten.",
      canonicalPath: "/projektablauf/",
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
    ...jobs.map((job) => ({
      h1: job.title,
      seoTitle: job.seoTitle,
      description: job.shortDescription,
      canonicalPath: `/karriere/${job.slug}/`,
    })),
    // Rechtsseiten: gebaut, indexierbar und im Footer verlinkt — sie gehören
    // deshalb in die Sitemap. Titel und Beschreibung müssen mit den Werten in
    // src/pages/impressum/ bzw. src/pages/datenschutz/ übereinstimmen.
    {
      h1: "Impressum",
      seoTitle: "Impressum | HSB Hexagon Säurebau GmbH",
      description:
        "Impressum und Anbieterkennzeichnung der HSB Hexagon Säurebau GmbH, Benzstraße 6, 48599 Gronau.",
      canonicalPath: "/impressum/",
    },
    {
      h1: "Datenschutzinformation",
      seoTitle: "Datenschutz | HSB Hexagon Säurebau GmbH",
      description:
        "Datenschutzinformation der HSB Hexagon Säurebau GmbH nach DSGVO: Verarbeitung personenbezogener Daten, Rechtsgrundlagen, Speicherdauer, Löschung und Ihre Betroffenenrechte.",
      canonicalPath: "/datenschutz/",
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
    {
      h1: "Industrieboden-Spezialist in Norddeutschland",
      seoTitle: "Industrieboden Hamburg | Keramische Böden & Säureschutz Nord",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Hamburg, Schleswig-Holstein und Norddeutschland.",
      canonicalPath: "/standorte/hamburg/",
    },
    {
      h1: "Industrieboden-Spezialist in Bayern",
      seoTitle: "Industrieboden Bayern | Böden & Säureschutz München",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Bayern. Projekte in München, Nürnberg, Augsburg, Regensburg und ganz Bayern.",
      canonicalPath: "/standorte/bayern/",
    },
    {
      h1: "Industrieboden-Spezialist in Nordrhein-Westfalen",
      seoTitle: "Industrieboden NRW | Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in NRW. Projekte in Köln, Düsseldorf, Dortmund, Essen und ganz Nordrhein-Westfalen.",
      canonicalPath: "/standorte/nrw/",
    },
    {
      h1: "Industrieboden-Spezialist in Rheinland-Pfalz",
      seoTitle: "Industrieboden Rheinland-Pfalz | Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Rheinland-Pfalz. Projekte in Mainz, Koblenz, Trier und der gesamten Region.",
      canonicalPath: "/standorte/rheinland-pfalz/",
    },
    {
      h1: "Industrieboden-Spezialist in Baden-Württemberg",
      seoTitle: "Industrieboden Baden-Württemberg | Böden & Säureschutz",
      description:
        "HSB Hexagon – Ihr Spezialist für keramische Industrieböden, Säureschutzsysteme und Entwässerung in Baden-Württemberg. Projekte in Stuttgart, Karlsruhe, Freiburg und der gesamten Region.",
      canonicalPath: "/standorte/baden-wuerttemberg/",
    },
  ];
}
