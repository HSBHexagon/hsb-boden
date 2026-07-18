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

export function resolveSuggestedLanguages(locale: string | undefined) {
  const normalized = (locale ?? "").toLowerCase();
  const primary = normalized.split("-")[0] as LanguageCode;
  const direct = supportedLanguages.find((language) => language.code === primary);
  const order = direct ? [direct.code, ...fallbackOrder.filter((code) => code !== direct.code)] : fallbackOrder;
  // Using reduce avoids the intermediate array allocation of map -> filter
  // Note: While flatMap was considered, micro-benchmarks showed it was slower
  // than the original map+filter in V8 due to many small array allocations.
  return order.reduce<typeof supportedLanguages>((acc, code) => {
    const language = supportedLanguages.find((lang) => lang.code === code);
    if (language) acc.push(language);
    return acc;
  }, []);
}
