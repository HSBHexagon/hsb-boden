import { site } from "../data/site";
import { absoluteUrl } from "./seo";

export function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "HSB Hexagon Säurebau GmbH",
    alternateName: "HSB",
    url: site.domain,
    address: {
      "@type": "PostalAddress",
      streetAddress: "Benzstraße 6",
      postalCode: "48599",
      addressLocality: "Gronau",
      addressCountry: "DE",
    },
    email: site.email,
    telephone: site.phone,
    description: site.description,
    areaServed: "Deutschland",
    knowsAbout: [
      "Industrieböden",
      "Säureschutz",
      "Keramische Industrieböden",
      "PU-Beton",
      "Epoxidharz",
      "Entwässerung",
      "Bodensanierung",
    ],
  };
}

export function buildLocalBusinessJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    name: "HSB Hexagon Säurebau GmbH",
    url: site.domain,
    address: {
      "@type": "PostalAddress",
      streetAddress: "Benzstraße 6",
      postalCode: "48599",
      addressLocality: "Gronau",
      addressCountry: "DE",
    },
    telephone: site.phone,
    email: site.email,
    priceRange: "$$$",
    areaServed: ["Deutschland", "DACH"],
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
    areaServed: ["Deutschland", "DACH"],
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
