export const site = {
  name: "HSB Hexagon Säurebau GmbH",
  shortName: "HSB",
  domain: "https://www.hsb-boden.de",
  email: "info@hsb-boden.de",
  phone: "+49 (0)2562 9463030",
  description:
    "Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung und Sanierung für Lebensmittel-, Getränke-, Pharma- und Chemieproduktion.",
  defaultTitle: "Industrieböden & Säureschutz für Industrie | HSB Hexagon",
  defaultDescription:
    "Ingenieurbau für Industrieböden: Rüttelkeramik, Säureschutz, PU-Beton und WHG-/AwSV-relevante Abdichtung für Lebensmittel-, Pharma- und Chemieproduktion.",
  ctaLabel: "Ersteinschätzung anfordern",
  ctaTarget: "/kontakt/",
  // Lead-Zustellung läuft serverseitig über /api/lead (kein Secret im Bundle).
  // false = Online-Versand inaktiv -> Formular zeigt direkten Kontaktweg statt PII zu leaken.
  // Wird serverseitig über PUBLIC_LEAD_FORM_ENABLED="true" im Production-Deploy aktiviert,
  // sobald LEAD_WEBHOOK_CONFIG / LEAD_WEBHOOK_URL und RATE_LIMIT_KV autorisiert sind.
  hasLeadEndpoint: import.meta.env.PUBLIC_LEAD_FORM_ENABLED === "true",
  // Foto der Schadstelle auf der Start-/Reparaturseite: /api/repair-photo verschickt Bilder
  // per SMTP an info@hsb-boden.de (keine dauerhafte Ablage). Aktivierung über PUBLIC_REPAIR_PHOTO_ENABLED="true".
  hasRepairPhotoUpload: import.meta.env.PUBLIC_REPAIR_PHOTO_ENABLED === "true",
};
