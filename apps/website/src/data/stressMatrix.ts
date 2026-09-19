import type { NormId } from "./standards";

export interface StressOption<Id extends string> {
  id: Id;
  label: string;
  hint?: string;
}

export const STRESS_MEDIA = [
  { id: "milchsaeure-molke", label: "Milchsäure / Molke", hint: "Molkerei, Käserei, Milchverarbeitung" },
  { id: "fruchtsaeuren", label: "Fruchtsäuren", hint: "Getränke, Obst- und Gemüseverarbeitung" },
  { id: "cip-laugen", label: "CIP-Laugen (NaOH)", hint: "Reinigungskreisläufe, Abfüllung" },
  { id: "anorganische-saeuren", label: "Anorganische Säuren (pH 0–2)", hint: "Chemie, Beizerei, Auffangwannen" },
  { id: "fette-oele", label: "Fette / Öle", hint: "Feinkost, Backwaren, Großküche" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_TEMPERATURES = [
  { id: "dauernass-kalt", label: "Dauernass kalt (< 20 °C)" },
  { id: "warmwasser-60", label: "Warmwasser bis 60 °C" },
  { id: "thermoschock-85", label: "Thermoschock / CIP-Reinigung bis 85 °C" },
  { id: "heissdampf-100", label: "Heißdampf > 100 °C" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_MECHANICAL = [
  { id: "handhubwagen", label: "Handhubwagen" },
  { id: "gabelstapler-3-5t", label: "Gabelstapler 3–5 t" },
  { id: "schwerlast-vulkollan", label: "Schwerlast-Flurförderzeuge mit Vulkollanrollen (> 30 N/mm²)" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_TIME_WINDOWS = [
  { id: "wochenende-48h", label: "Wochenendstillstand (< 48 h)" },
  { id: "revision-7-14d", label: "Revisionsstillstand (7–14 Tage)" },
  { id: "neubau", label: "Neubau" },
] as const satisfies readonly StressOption<string>[];

export type StressMediumId = (typeof STRESS_MEDIA)[number]["id"];
export type StressTemperatureId = (typeof STRESS_TEMPERATURES)[number]["id"];
export type StressMechanicalId = (typeof STRESS_MECHANICAL)[number]["id"];
export type StressTimeWindowId = (typeof STRESS_TIME_WINDOWS)[number]["id"];

export interface StressCheckInput {
  medium: StressMediumId;
  tempRange: StressTemperatureId;
  mechanicalLoad: StressMechanicalId;
  timeWindow: StressTimeWindowId;
}

export type StressSystemId = "agi-s40-ruettelkeramik" | "pu-beton-hochtemperatur" | "whg-fachbeschichtung";

export interface StressSystem {
  id: StressSystemId;
  name: string;
  short: string;
  description: string;
  serviceSlug: string;
  norms: NormId[];
}

export const STRESS_SYSTEMS: Record<StressSystemId, StressSystem> = {
  "agi-s40-ruettelkeramik": {
    id: "agi-s40-ruettelkeramik",
    name: "AGI S 40 Vibro-Rüttelkeramik mit Kunstharzfuge",
    short: "Rüttelkeramik (AGI S 40)",
    description:
      "Keramische Platten nach DIN EN 14411, im Rüttelverfahren in ein Reaktionsharz-Bett eingebracht und mit Kunstharzfuge geschlossen. Beständig gegen organische und anorganische Säuren, Laugen und Thermoschock; sehr hohe Druck- und Flächenpressungsfestigkeit durch das Rüttelverfahren.",
    serviceSlug: "keramische-industrieboeden",
    norms: ["AGI S 40", "DIN EN 14411"],
  },
  "pu-beton-hochtemperatur": {
    id: "pu-beton-hochtemperatur",
    name: "Hochtemperatur-Polyurethanbeton (PU-Beton bis 120 °C)",
    short: "PU-Beton (bis 120 °C)",
    description:
      "Fugenarmes, thermoschockbeständiges Polyurethan-Zement-System für Fette, Öle und organische Säuren. Schnell härtend und deshalb erste Wahl für kurze Stillstandsfenster.",
    serviceSlug: "pu-beton-industrieboden",
    norms: [],
  },
  "whg-fachbeschichtung": {
    id: "whg-fachbeschichtung",
    name: "WHG § 62 Fachbeschichtung (Chemie / Auffangwannen)",
    short: "WHG § 62 Fachbeschichtung",
    description:
      "Dichte, chemikalienbeständige Flächen- und Auffangwannenbeschichtung für den Umgang mit wassergefährdenden Stoffen, ausgeführt als Fachbetrieb nach § 62 WHG / AwSV mit Dokumentation für Behörden und Sachverständige.",
    serviceSlug: "whg-abdichtung-industrieboden",
    norms: ["WHG § 62"],
  },
};

export interface StressCheckResult {
  system: StressSystem;
  reasons: string[];
  windowNote?: string;
}

const MEDIA_IDS = new Set<string>(STRESS_MEDIA.map((item) => item.id));
const TEMPERATURE_IDS = new Set<string>(STRESS_TEMPERATURES.map((item) => item.id));
const MECHANICAL_IDS = new Set<string>(STRESS_MECHANICAL.map((item) => item.id));
const TIME_WINDOW_IDS = new Set<string>(STRESS_TIME_WINDOWS.map((item) => item.id));

export function isStressCheckInput(value: unknown): value is StressCheckInput {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.medium === "string" && MEDIA_IDS.has(candidate.medium) &&
    typeof candidate.tempRange === "string" && TEMPERATURE_IDS.has(candidate.tempRange) &&
    typeof candidate.mechanicalLoad === "string" && MECHANICAL_IDS.has(candidate.mechanicalLoad) &&
    typeof candidate.timeWindow === "string" && TIME_WINDOW_IDS.has(candidate.timeWindow)
  );
}

const WINDOW_NOTE_KERAMIK =
  "Rüttelkeramik ist in einem Wochenendfenster unter 48 h nur in Bauabschnitten realisierbar – die Taktung wird im Vor-Ort-Audit festgelegt.";
const WINDOW_NOTE_WHG =
  "Eine WHG-Fachbeschichtung benötigt Untergrundvorbereitung, Dichtheitsprüfung und Dokumentation – ein Wochenendfenster reicht nur für Teilflächen.";

/**
 * Deterministische Systemauslegung: geordnete Regeln, erste zutreffende gewinnt.
 * 1. Heißdampf > 100 °C          -> Rüttelkeramik (Reaktionsharzsysteme thermisch begrenzt)
 * 2. Schwerlast > 30 N/mm²       -> Rüttelkeramik (Druck-/Flächenpressungsfestigkeit)
 * 3. Anorganische Säuren pH 0–2  -> mit Thermoschock: Rüttelkeramik, sonst WHG § 62 Fachbeschichtung
 * 4. Wochenendfenster < 48 h     -> PU-Beton (schnell härtend)
 * 5. Fette / Öle                 -> PU-Beton (fugenarm, fettbeständig)
 * 6. Organische Säuren / Laugen  -> Rüttelkeramik (Kunstharzfuge, pH 0–14)
 */
export function resolveStressSystem(input: StressCheckInput): StressCheckResult {
  const reasons: string[] = [];
  const weekend = input.timeWindow === "wochenende-48h";

  if (input.tempRange === "heissdampf-100") {
    reasons.push("Heißdampf über 100 °C als Dauer- und Wechselbelastung liegt an der Systemgrenze fugenarmer PU- und Reaktionsharz-Systeme; Rüttelkeramik mit Kunstharzfuge bleibt formstabil.");
    if (input.mechanicalLoad === "schwerlast-vulkollan") reasons.push("Flächenpressungen über 30 N/mm² aus Vulkollanrollen werden von der keramischen Rüttelverlegung abgetragen.");
    return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
  }

  if (input.mechanicalLoad === "schwerlast-vulkollan") {
    reasons.push("Flächenpressungen über 30 N/mm² aus Vulkollanrollen erfordern die Druckfestigkeit keramischer Rüttelbeläge nach AGI S 40.");
    if (input.medium === "anorganische-saeuren") reasons.push("Anorganische Säuren im pH-Bereich 0–2 werden durch die Kunstharzfuge nach AGI S 40 dauerhaft abgedeckt.");
    return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
  }

  if (input.medium === "anorganische-saeuren") {
    if (input.tempRange === "thermoschock-85") {
      reasons.push("Die Kombination aus anorganischen Säuren (pH 0–2) und Thermoschock bis 85 °C überfordert Beschichtungen; Rüttelkeramik mit Kunstharzfuge nach AGI S 40 ist hier Stand der Technik.");
      return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
    }
    reasons.push("Anorganische Säuren im pH-Bereich 0–2 sind in der Regel wassergefährdende Stoffe im Sinne der AwSV; für Anlagen greift § 62 WHG, die Fachbeschichtung liefert Dichtheit, Beständigkeit und die behördlich geforderte Dokumentation.");
    if (input.mechanicalLoad === "gabelstapler-3-5t") reasons.push("Staplerverkehr bis 5 t wird bei der Auslegung des Schichtaufbaus berücksichtigt.");
    return { system: STRESS_SYSTEMS["whg-fachbeschichtung"], reasons, windowNote: weekend ? WINDOW_NOTE_WHG : undefined };
  }

  if (weekend) {
    reasons.push("Ein Wochenendfenster unter 48 h erlaubt nur schnell härtende Systeme; PU-Beton ist nach kurzer Zeit befahrbar und voll belastbar.");
    if (input.tempRange === "thermoschock-85") reasons.push("PU-Beton ist thermoschockbeständig und übersteht CIP-Reinigung bis 85 °C.");
    if (input.medium === "cip-laugen") reasons.push("Die Laugenbeständigkeit wird im Audit anhand Konzentration und Temperatur gegen das Systemdatenblatt geprüft.");
    else if (input.medium !== "fette-oele") reasons.push("Organische Säuren im Konzentrationsbereich der Lebensmittelproduktion werden dauerhaft abgedeckt.");
    return { system: STRESS_SYSTEMS["pu-beton-hochtemperatur"], reasons };
  }

  if (input.medium === "fette-oele") {
    reasons.push("Fette und Öle verlangen eine fugenarme, porenfreie Oberfläche; PU-Beton verhindert Unterwanderung und Keimnester.");
    if (input.tempRange === "thermoschock-85") reasons.push("PU-Beton ist thermoschockbeständig und übersteht CIP-Reinigung bis 85 °C.");
    return { system: STRESS_SYSTEMS["pu-beton-hochtemperatur"], reasons };
  }

  reasons.push("Milchsäure, Fruchtsäuren und CIP-Laugen greifen zementöse und viele Reaktionsharz-Fugen an; die Kunstharzfuge nach AGI S 40 deckt pH 0–14 dauerhaft ab.");
  if (input.tempRange === "thermoschock-85") reasons.push("Thermoschock bis 85 °C wird durch die keramische Rüttelverlegung ohne Haftverbund-Verlust aufgenommen.");
  if (input.mechanicalLoad === "gabelstapler-3-5t") reasons.push("Staplerverkehr bis 5 t liegt innerhalb der Druckfestigkeit keramischer Rüttelbeläge nach AGI S 40.");
  if (input.timeWindow === "neubau") reasons.push("Im Neubau kann Gefälle- und Rinnenplanung direkt in die keramische Fläche integriert werden.");
  return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons };
}
