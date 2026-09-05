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


const supportedLanguagesByCode = supportedLanguages.reduce((acc, lang) => {
  acc[lang.code] = lang;
  return acc;
}, {} as Record<LanguageCode, (typeof supportedLanguages)[number]>);

const fallbackOrder: LanguageCode[] = ["en", "de", "tr", "pl", "fr", "nl"];

export function resolveSuggestedLanguages(locale: string | undefined) {
  const normalized = (locale ?? "").toLowerCase();
  const primary = normalized.split("-")[0] as LanguageCode;
  const direct = supportedLanguagesByCode[primary];
  const order = direct ? [direct.code, ...fallbackOrder.filter((code) => code !== direct.code)] : fallbackOrder;
  const result = [];
  for (let i = 0; i < order.length; i++) {
    const lang = supportedLanguagesByCode[order[i]];
    if (lang) result.push(lang);
  }
  return result;
}
