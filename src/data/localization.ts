export type LanguageCode = "de" | "en" | "tr" | "pl" | "fr" | "nl";

export const supportedLanguages: Array<{
  code: LanguageCode;
  label: string;
  nativeLabel: string;
  shortHint: string;
}> = [
  {
    code: "de",
    label: "Deutsch",
    nativeLabel: "Deutsch",
    shortHint: "Originale Fachseite",
  },
  {
    code: "en",
    label: "English",
    nativeLabel: "English",
    shortHint: "International project inquiry",
  },
  {
    code: "tr",
    label: "Turkish",
    nativeLabel: "Türkçe",
    shortHint: "Türkiye'den ziyaretçiler için",
  },
  {
    code: "pl",
    label: "Polish",
    nativeLabel: "Polski",
    shortHint: "Dla odwiedzających z Polski",
  },
  {
    code: "fr",
    label: "French",
    nativeLabel: "Français",
    shortHint: "Pour les visiteurs francophones",
  },
  {
    code: "nl",
    label: "Dutch",
    nativeLabel: "Nederlands",
    shortHint: "Voor bezoekers uit Nederland",
  },
];

const fallbackOrder: LanguageCode[] = ["en", "de", "tr", "pl", "fr", "nl"];

type SupportedLanguage = (typeof supportedLanguages)[number];

// Pre-compute language lookup map for O(1) access
const languageMap = new Map<LanguageCode, SupportedLanguage>(
  supportedLanguages.map((l) => [l.code, l]),
);

// Pre-compute fallback array of full objects
const fallbackLanguages = fallbackOrder
  .map((code) => languageMap.get(code))
  .filter((l): l is SupportedLanguage => Boolean(l));

// Pre-compute permutations of the fallback list for each possible primary language
// Since we only have 6 supported languages, this uses minimal memory but gives O(1) execution
const languageOrderings = new Map<LanguageCode, SupportedLanguage[]>();
for (const lang of supportedLanguages) {
  languageOrderings.set(lang.code, [
    lang,
    ...fallbackLanguages.filter((l) => l.code !== lang.code),
  ]);
}

export function resolveSuggestedLanguages(locale: string | undefined) {
  if (!locale) return fallbackLanguages;

  // Fast check for exact match before string manipulations
  if (locale.length === 2) {
    const order = languageOrderings.get(locale as LanguageCode);
    if (order) return order;
  }

  let primary = locale;
  const splitIndex = locale.search(/[_-]/);
  if (splitIndex !== -1) {
    primary = locale.substring(0, splitIndex);
  }

  const order = languageOrderings.get(primary.toLowerCase() as LanguageCode);
  return order || fallbackLanguages;
}
