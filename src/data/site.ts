export const site = {
  name: "HSB Hexagon Säurebau GmbH",
  shortName: "HSB",
  domain: "https://www.hsb-boden.de",
  email: "info@hsb-boden.de",
  phone: "+49 (0)2562 9463030",
  description:
    "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion.",
  defaultTitle: "Industrieböden & Säureschutz für Produktion | HSB Hexagon Säurebau",
  defaultDescription:
    "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion. Jetzt kostenlose Ersteinschätzung anfordern.",
  ctaLabel: "Ersteinschätzung anfordern",
  ctaTarget: "/kontakt/",
  // Lead-Zustellung läuft serverseitig über /api/lead (kein Secret im Bundle).
  // false = Online-Versand inaktiv -> Formular zeigt direkten Kontaktweg statt PII zu leaken.
  // Wird erst auf "true" gesetzt, wenn LEAD_WEBHOOK_URL serverseitig konfiguriert ist.
  hasLeadEndpoint: import.meta.env.PUBLIC_LEAD_FORM_ENABLED === "true",
};
