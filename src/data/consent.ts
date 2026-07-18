export type ConsentCategoryId = "essential" | "analytics" | "marketing";

export const consentCategories: Array<{
  id: ConsentCategoryId;
  label: string;
  description: string;
  required: boolean;
}> = [
  {
    id: "essential",
    label: "Essenzielle Cookies",
    description: "Notwendig für Sicherheit, Seitenauslieferung, Formularschutz und die Speicherung Ihrer Cookie-Auswahl.",
    required: true,
  },
  {
    id: "analytics",
    label: "Analyse",
    description: "Hilft HSB zu verstehen, welche Seiten und Themen Interessenten nutzen. Wird erst nach Einwilligung aktiviert.",
    required: false,
  },
  {
    id: "marketing",
    label: "Marketing",
    description: "Reserviert für spätere Kampagnenmessung, Flyer-QR-Codes und Remarketing. In V1 standardmäßig deaktiviert.",
    required: false,
  },
];

export function getRequiredConsentCategories() {
  return consentCategories.reduce<ConsentCategoryId[]>((acc, category) => {
    if (category.required) {
      acc.push(category.id);
    }
    return acc;
  }, []);
}
