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

const languageMap = new Map(supportedLanguages.map((language) => [language.code, language]));

export function resolveSuggestedLanguages(locale: string | undefined) {
  const normalized = (locale ?? "").toLowerCase();
  const primary = normalized.split("-")[0] as LanguageCode;
  const direct = languageMap.get(primary);

  const result: Array<(typeof supportedLanguages)[number]> = [];
  if (direct) {
    result.push(direct);
  }

  for (let i = 0; i < fallbackOrder.length; i++) {
    const code = fallbackOrder[i];
    if (code !== primary) {
      const language = languageMap.get(code);
      if (language) {
        result.push(language);
      }
    }
  }

  return result;
}
