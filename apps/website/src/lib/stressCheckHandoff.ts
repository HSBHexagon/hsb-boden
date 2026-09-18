import {
  STRESS_MECHANICAL,
  STRESS_MEDIA,
  STRESS_SYSTEMS,
  STRESS_TEMPERATURES,
  STRESS_TIME_WINDOWS,
  isStressCheckInput,
  type StressCheckInput,
  type StressCheckResult,
  type StressSystemId,
} from "../data/stressMatrix";
import { loadOptions } from "./validation";

export const STRESS_CHECK_STORAGE_KEY = "hsb-stresscheck-v1";
export const STRESS_CHECK_EVENT = "hsb:stresscheck";

export interface LeadPrefill {
  loads: string[];
  projectType: "neubau" | "sanierung";
  liveOperation: "ja" | "nein";
  message: string;
  recommendedSystem: StressSystemId;
  input: StressCheckInput;
}

type LoadOption = (typeof loadOptions)[number];
const LOAD_OPTION_SET = new Set<string>(loadOptions);

function labelOf<Id extends string>(options: readonly { id: Id; label: string }[], id: Id): string {
  return options.find((option) => option.id === id)?.label ?? id;
}

// Abbildung der Check-Parameter auf die im Formular vorhandenen Belastungen
// (validation.ts: loadOptions). Es werden keine neuen Optionen erfunden.
function mapLoads(input: StressCheckInput): LoadOption[] {
  const loads = new Set<LoadOption>();
  loads.add(input.medium === "fette-oele" ? "Fette/Öle" : "Säuren/Laugen");
  if (input.medium === "cip-laugen") loads.add("Hochdruckreinigung");
  if (input.tempRange === "dauernass-kalt") loads.add("Nassbereich");
  else loads.add("Temperaturwechsel");
  if (input.mechanicalLoad !== "handhubwagen") loads.add("Staplerverkehr");
  return [...loads];
}

export function buildLeadPrefill(input: StressCheckInput, result: StressCheckResult): LeadPrefill {
  const isNeubau = input.timeWindow === "neubau";
  const message = [
    "Technischer Beanspruchungs-Check (Website):",
    `Chemisches Medium: ${labelOf(STRESS_MEDIA, input.medium)}`,
    `Thermische Belastung: ${labelOf(STRESS_TEMPERATURES, input.tempRange)}`,
    `Mechanische Last: ${labelOf(STRESS_MECHANICAL, input.mechanicalLoad)}`,
    `Sanierungsfenster: ${labelOf(STRESS_TIME_WINDOWS, input.timeWindow)}`,
    `Vorläufige Systemempfehlung: ${result.system.name}`,
    "",
    "Bitte um Terminvorschlag für ein qualifiziertes Vor-Ort-Audit.",
  ].join("\n");

  return {
    loads: mapLoads(input),
    projectType: isNeubau ? "neubau" : "sanierung",
    liveOperation: isNeubau ? "nein" : "ja",
    message,
    recommendedSystem: result.system.id,
    input,
  };
}

function isLeadPrefill(value: unknown): value is LeadPrefill {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    Array.isArray(candidate.loads) &&
    candidate.loads.every((load) => typeof load === "string" && LOAD_OPTION_SET.has(load)) &&
    (candidate.projectType === "neubau" || candidate.projectType === "sanierung") &&
    (candidate.liveOperation === "ja" || candidate.liveOperation === "nein") &&
    typeof candidate.message === "string" && candidate.message.length <= 2000 &&
    typeof candidate.recommendedSystem === "string" && candidate.recommendedSystem in STRESS_SYSTEMS &&
    isStressCheckInput(candidate.input)
  );
}

export function saveStressCheckHandoff(storage: Storage, prefill: LeadPrefill): void {
  try {
    storage.setItem(STRESS_CHECK_STORAGE_KEY, JSON.stringify(prefill));
  } catch {
    // Storage blockiert: Übergabe läuft dann nur über das DOM-Event.
  }
}

export function loadStressCheckHandoff(storage: Storage): LeadPrefill | undefined {
  try {
    const raw = storage.getItem(STRESS_CHECK_STORAGE_KEY);
    if (raw === null) return undefined;
    const parsed: unknown = JSON.parse(raw);
    return isLeadPrefill(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
}

export function clearStressCheckHandoff(storage: Storage): void {
  try {
    storage.removeItem(STRESS_CHECK_STORAGE_KEY);
  } catch {
    // Storage blockiert: nichts zu löschen.
  }
}
