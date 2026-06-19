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
  firstName: z.string().min(2),
  lastName: z.string().min(2),
  company: z.string().min(2),
  email: z.string().email(),
  phone: z.string().min(5),
  industry: z.string().min(2),
  projectType: z.string().min(2),
  areaSize: z.string().optional(),
  currentFloor: z.string().optional(),
  loads: z.array(z.string()).min(1),
  liveOperation: z.string().min(2),
  timeframe: z.string().optional(),
  message: z.string().min(10),
  privacyConsent: z.literal(true),
});

export type LeadPayload = z.input<typeof leadFormSchema>;
