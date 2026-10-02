import { z } from "zod";

export const loadOptions = [
  "Säuren/Laugen",
  "Fette/Öle",
  "Hochdruckreinigung",
  "Temperaturwechsel",
  "Staplerverkehr",
  "Nassbereich",
  "Hygiene/Audit",
  "Rutschhemmung",
  "Undichtigkeiten",
  "Risse/Fugenprobleme",
] as const;

export const leadFormSchema = z.object({
  firstName: z.string().trim().min(2).max(80),
  lastName: z.string().trim().max(80).optional().default(""),
  company: z.string().trim().min(2).max(120),
  email: z.string().trim().email().max(254),
  phone: z.string().trim().max(64).refine(value => !value || value.length >= 5).optional().default(""),
  industry: z.string().trim().max(120).optional().default(""),
  projectType: z.enum(["neubau", "sanierung", "bewertung"]).optional().default("bewertung"),
  areaSize: z.string().optional(),
  currentFloor: z.string().optional(),
  loads: z.array(z.enum(loadOptions)).optional().default([]),
  liveOperation: z.enum(["ja", "nein", "unklar"]).optional().default("unklar"),
  timeframe: z.string().optional(),
  message: z.string().trim().min(10).max(2000),
  privacyConsent: z.literal(true),
});

export type LeadPayload = z.input<typeof leadFormSchema>;

export function serializeLeadPayload(payload: unknown) {
  const parsed = leadFormSchema.parse(payload);
  return {
    source: "website",
    legalBasis: "inquiry",
    optOutStatus: "not_applicable",
    firstName: parsed.firstName,
    lastName: parsed.lastName,
    company: parsed.company,
    email: parsed.email,
    phone: parsed.phone,
    industry: parsed.industry,
    projectType: parsed.projectType,
    areaSize: parsed.areaSize ?? "",
    currentFloor: parsed.currentFloor ?? "",
    systemInterest: parsed.loads.join(", "),
    liveOperation: parsed.liveOperation,
    timeframe: parsed.timeframe ?? "",
    message: parsed.message,
  };
}
