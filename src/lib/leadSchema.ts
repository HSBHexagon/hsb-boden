import { z } from "zod";
import { loadOptions } from "./validation";

// Schema für POST /api/lead (serverseitig). Bewusst getrennt von leadFormSchema
// in validation.ts: andere Pflichtfelder (source/legalBasis/honeypot serverseitig
// relevant), siehe PUBLIC_LEAD_ENDPOINT_SPEC.md §4-5.
export const leadEndpointSchema = z
  .object({
    firstName: z.string().trim().min(2).max(80),
    lastName: z.string().trim().min(2).max(80),
    company: z.string().trim().min(2).max(120),
    email: z.string().trim().email(),
    phone: z.string().trim().min(5),
    industry: z.string().trim().min(2),
    projectType: z.enum(["neubau", "sanierung", "bewertung"]),
    areaSize: z.string().trim().max(80).optional(),
    liveOperation: z.enum(["ja", "nein", "unklar"]),
    loads: z.array(z.enum(loadOptions)).min(1),
    message: z.string().trim().min(10).max(2000),
    privacyConsent: z.literal(true),
    source: z.string().trim().min(1),
    legalBasis: z.string().trim().min(1),
    access_key: z.string().trim().optional(),
    utm_source: z.string().trim().max(100).optional(),
    utm_medium: z.string().trim().max(100).optional(),
    utm_campaign: z.string().trim().max(100).optional(),
    utm_term: z.string().trim().max(100).optional(),
    utm_content: z.string().trim().max(100).optional(),
    // Attribution (Client erfasst, siehe src/lib/attribution.ts): Referrer nur
    // als externes Origin, Pfade ohne Query — Webhook reicht sie 1:1 ans CRM.
    referrer: z.string().trim().max(200).optional(),
    landing_page: z.string().trim().max(200).optional(),
    form_path: z.string().trim().max(200).optional(),
    attribution_channel: z.enum(["campaign", "referral", "direct"]).optional(),
    honeypot: z.string().trim().max(0).optional(),
    timestamp: z.number().optional(),
  })
  .transform(({ honeypot, ...rest }) => rest);

export type LeadEndpointPayload = z.infer<typeof leadEndpointSchema>;
