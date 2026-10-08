import { site } from "../data/site";
import { absoluteUrl } from "./seo";
import { organizationCredential, type NormId } from "../data/standards";

const BUSINESS_ID = `${site.domain}/#unternehmen`;

// Einziges Credential: Fachbetrieb nach § 62 WHG / AwSV (Owner-Bestätigung,
// PROJECT_TRUTH.md §3a). Ausführungsnormen sind Wissen, keine Zertifikate.
function buildCredentialJsonLd() {
  return [
    {
      "@type": "EducationalOccupationalCredential",
      credentialCategory: organizationCredential.credentialCategory,
      name: organizationCredential.name,
    },
  ];
}

const NORM_KNOWLEDGE = [
  "AGI S 40 Säureschutzbau (keramische Beläge)",
  "DIN EN 14411 Keramische Fliesen und Platten",
  "§ 62 WHG / AwSV Anlagen mit wassergefährdenden Stoffen",
];

export function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@id": BUSINESS_ID,
    "@type": "Organization",
    name: "HSB Hexagon Säurebau GmbH",
    alternateName: "HSB",
    url: site.domain,
    logo: `${site.domain}/brand/hsb-boden-logo.png`,
    image: `${site.domain}/brand/og-image.png`,
    address: {
      "@type": "PostalAddress",
      streetAddress: "Benzstraße 6",
      postalCode: "48599",
      addressLocality: "Gronau",
      addressRegion: "Nordrhein-Westfalen",
      addressCountry: "DE",
    },
    contactPoint: [
      {
        "@type": "ContactPoint",
        telephone: site.phone,
        contactType: "customer service",
        email: site.email,
        areaServed: ["DE", "AT", "CH", "NL", "BE", "LU", "PL", "FR"],
        availableLanguage: ["German", "English", "Dutch", "French", "Polish", "Turkish"],
      },
    ],
    email: site.email,
    telephone: site.phone,
    description: site.description,
    areaServed: ["Deutschland", "Österreich", "Schweiz", "Niederlande", "Belgien", "Luxemburg", "Polen", "Frankreich"],
    knowsAbout: [
      "Industrieböden",
      "Säureschutz",
      "Keramische Industrieböden",
      "PU-Beton",
      "Epoxidharz",
      "Entwässerung",
      "Bodensanierung",
      "WHG-Beschichtung",
      "HACCP-Böden",
      "Rüttelkeramik",
      ...NORM_KNOWLEDGE,
    ],
    hasCredential: buildCredentialJsonLd(),
  };
}

/** Ein regionales Leistungsgebiet ist keine separate Niederlassung. */
export function buildRegionalServiceJsonLd(region: string, path: string) {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: `Industrieböden und Säureschutz in ${region}`,
    description: `Keramische Industrieböden, Säureschutz und Bodensanierung für Produktionsbetriebe in ${region}.`,
    url: absoluteUrl(path),
    serviceType: ["Keramische Industrieböden", "Säureschutz", "Bodensanierung"],
    areaServed: region,
    provider: {
      "@id": BUSINESS_ID,
      "@type": "Organization",
      name: site.name,
      url: site.domain,
      telephone: site.phone,
    },
  };
}

// Liefert Google den gewuenschten Sitenamen fuer die Suchergebnisse.
// Bewusst ohne SearchAction: die Website hat keine eigene Suchfunktion.
export function buildWebSiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "HSB Hexagon Säurebau",
    alternateName: "HSB",
    url: site.domain,
    inLanguage: "de-DE",
    publisher: {
      "@id": BUSINESS_ID,
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
    },
  };
}

export function buildLocalBusinessJsonLd() {
  return {
    "@context": "https://schema.org",
    "@id": BUSINESS_ID,
    "@type": "LocalBusiness",
    name: "HSB Hexagon Säurebau GmbH",
    alternateName: "HSB",
    url: site.domain,
    logo: `${site.domain}/brand/hsb-boden-logo.png`,
    image: `${site.domain}/brand/og-image.png`,
    address: {
      "@type": "PostalAddress",
      streetAddress: "Benzstraße 6",
      postalCode: "48599",
      addressLocality: "Gronau",
      addressRegion: "Nordrhein-Westfalen",
      addressCountry: "DE",
    },
    telephone: site.phone,
    email: site.email,
    areaServed: ["Deutschland", "DACH", "Europa"],
  };
}

export function buildFaqJsonLd(
  faqs: Array<{ question: string; answer: string }>,
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

export function buildServiceJsonLd(service: {
  name: string;
  description: string;
  path: string;
  standards?: NormId[];
}) {
  const additionalProperty = service.standards?.length
    ? service.standards.map((standard) => ({
        "@type": "PropertyValue",
        name: "Ausführungsgrundlage",
        value: standard,
      }))
    : undefined;

  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.name,
    description: service.description,
    url: absoluteUrl(service.path),
    serviceType: service.name,
    areaServed: ["Deutschland", "Österreich", "Schweiz", "Europa"],
    ...(additionalProperty ? { additionalProperty } : {}),
    provider: {
      "@id": BUSINESS_ID,
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
      hasCredential: buildCredentialJsonLd(),
      address: {
        "@type": "PostalAddress",
        streetAddress: "Benzstraße 6",
        postalCode: "48599",
        addressLocality: "Gronau",
        addressCountry: "DE",
      },
    },
  };
}

export function buildJobPostingJsonLd(job: {
  slug: string;
  title: string;
  description: string;
  employmentType: string;
  occupationalCategory: string;
  datePosted: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    title: job.title,
    description: job.description,
    identifier: {
      "@type": "PropertyValue",
      name: "HSB Hexagon Säurebau GmbH",
      value: job.slug,
    },
    datePosted: job.datePosted,
    employmentType: job.employmentType,
    occupationalCategory: job.occupationalCategory,
    hiringOrganization: {
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      sameAs: site.domain,
      url: site.domain,
    },
    jobLocation: {
      "@type": "Place",
      address: {
        "@type": "PostalAddress",
        streetAddress: "Benzstraße 6",
        postalCode: "48599",
        addressLocality: "Gronau",
        addressRegion: "Nordrhein-Westfalen",
        addressCountry: "DE",
      },
    },
  };
}

export function buildBreadcrumbJsonLd(
  items: Array<{ name: string; path: string }>,
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}

export function buildArticleJsonLd(article: {
  headline: string;
  description: string;
  path: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    headline: article.headline,
    description: article.description,
    mainEntityOfPage: absoluteUrl(article.path),
    author: {
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
    },
    publisher: {
      "@id": BUSINESS_ID,
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
    },
  };
}
