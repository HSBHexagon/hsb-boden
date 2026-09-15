import { site } from "../data/site";
import { absoluteUrl } from "./seo";

export function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
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
    ],
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
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
    },
  };
}

export function buildLocalBusinessJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    additionalType: "https://schema.org/SpecialtyContractor",
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
    geo: {
      "@type": "GeoCoordinates",
      latitude: "52.2125",
      longitude: "7.0253",
    },
    telephone: site.phone,
    email: site.email,
    priceRange: "$$$",
    currenciesAccepted: "EUR",
    paymentAccepted: "Invoice, Bank Transfer",
    openingHoursSpecification: [
      {
        "@type": "OpeningHoursSpecification",
        dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        opens: "07:00",
        closes: "18:00",
      },
    ],
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
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.name,
    description: service.description,
    url: absoluteUrl(service.path),
    serviceType: service.name,
    areaServed: ["Deutschland", "Österreich", "Schweiz", "Europa"],
    provider: {
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
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
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
    },
  };
}
