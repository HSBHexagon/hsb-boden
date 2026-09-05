export type LanguageCode = "de" | "en" | "tr" | "pl" | "fr" | "nl";

export const supportedLanguages: Array<{
  code: LanguageCode;
  label: string;
  nativeLabel: string;
  shortHint: string;
}> = [
  { code: "de", label: "Deutsch", nativeLabel: "Deutsch", shortHint: "Originale Fachseite" },
  { code: "en", label: "English", nativeLabel: "English", shortHint: "International project inquiry" },
  { code: "tr", label: "Turkish", nativeLabel: "Türkçe", shortHint: "Türkiye'den ziyaretçiler için" },
  { code: "pl", label: "Polish", nativeLabel: "Polski", shortHint: "Dla odwiedzających z Polski" },
  { code: "fr", label: "French", nativeLabel: "Français", shortHint: "Pour les visiteurs francophones" },
  { code: "nl", label: "Dutch", nativeLabel: "Nederlands", shortHint: "Voor bezoekers uit Nederland" },
];

const fallbackOrder: LanguageCode[] = ["en", "de", "tr", "pl", "fr", "nl"];

const supportedLanguagesByCode = supportedLanguages.reduce(
  (acc, lang) => {
    acc[lang.code] = lang;
    return acc;
  },
  Object.create(null) as Record<LanguageCode, (typeof supportedLanguages)[number]>
);

export function resolveSuggestedLanguages(locale: string | undefined) {
  const normalized = (locale ?? "").toLowerCase();
  const primary = normalized.split("-")[0] as LanguageCode;
  const direct = supportedLanguagesByCode[primary];

  if (!direct) {
    return fallbackOrder
      .map((code) => supportedLanguagesByCode[code])
      .filter((language): language is (typeof supportedLanguages)[number] => Boolean(language));
  }

  const result = [direct];
  for (const code of fallbackOrder) {
    if (code !== direct.code) {
      const language = supportedLanguagesByCode[code];
      if (language) {
        result.push(language);
      }
    }
  }
  return result;
}
