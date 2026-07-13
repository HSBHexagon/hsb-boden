import { z } from "zod";
import { loadOptions } from "./validation";
import { sanitizePagePath, sanitizeReferrerOrigin, sanitizeUtmValue } from "./attribution";

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
    // Attribution: Client sanitisiert bereits (src/lib/attribution.ts), aber die
    // Vertrauensgrenze ist dieser Endpoint — direkte POSTs umgehen den Browser.
    // Deshalb serverseitige Re-Normalisierung (Allowlist, Formula-Prefix-Schutz,
    // Referrer→Origin, Pfade ohne Query); ungültige Werte werden verworfen statt
    // den Lead abzulehnen. Alle Felder optional, weil ältere gecachte
    // Client-Bundles ohne Attribution senden.
    utm_source: z.string().max(100).optional().transform(sanitizeUtmValue),
    utm_medium: z.string().max(100).optional().transform(sanitizeUtmValue),
    utm_campaign: z.string().max(100).optional().transform(sanitizeUtmValue),
    utm_term: z.string().max(100).optional().transform(sanitizeUtmValue),
    utm_content: z.string().max(100).optional().transform(sanitizeUtmValue),
    referrer: z.string().max(200).optional().transform((v) => sanitizeReferrerOrigin(v)),
    landing_page: z.string().max(200).optional().transform(sanitizePagePath),
    form_path: z.string().max(200).optional().transform(sanitizePagePath),
    attribution_channel: z.enum(["campaign", "referral", "direct"]).optional(),
    honeypot: z.string().trim().max(0).optional(),
    timestamp: z.number().optional(),
  })
  .transform(({ honeypot, ...rest }) => rest);

export type LeadEndpointPayload = z.infer<typeof leadEndpointSchema>;
