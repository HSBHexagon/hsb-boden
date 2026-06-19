export const site = {
  name: "HSB Hexagon Säurebau GmbH",
  shortName: "HSB",
  domain: "https://hsb-boden.de",
  email: "info@hsb-boden.de",
  phone: "+49 (0)2562 9463030",
  description:
    "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion.",
  defaultTitle: "Industrieböden & Säureschutz für Produktion | HSB Hexagon Säurebau",
  defaultDescription:
    "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion. Jetzt kostenlose Ersteinschätzung anfordern.",
  ctaLabel: "Ersteinschätzung anfordern",
  ctaTarget: "/kontakt/",
  // Check if lead endpoint is configured
  hasLeadEndpoint: import.meta.env.PUBLIC_LEAD_ENDPOINT !== undefined && import.meta.env.PUBLIC_LEAD_ENDPOINT !== "",
};
