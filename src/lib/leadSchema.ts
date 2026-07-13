import { z } from "zod";
import { loadOptions } from "./validation";
import { resolveChannel, sanitizePagePath, sanitizeReferrerOrigin, sanitizeUtmValue } from "./attribution";

// Bewusst NICHT aus src/data/site.ts importiert: site.ts liest import.meta.env,
// das im Pages-Function-Bundle nicht existiert (Publish-Crash). Muss mit
// site.domain übereinstimmen — abgesichert durch Test in lead-endpoint-schema.
export const SITE_ORIGIN = "https://www.hsb-boden.de";

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
    // Bewusst kein .max() vor dem Transform: ungültige/überlange Werte werden
    // verworfen bzw. gekappt statt den Lead abzulehnen (Payload-Größe deckelt
    // der Endpoint separat mit 413). Same-Origin-Referrer werden auch server-
    // seitig verworfen, damit direkte POSTs kein "referral" fälschen können.
    utm_source: z.string().optional().transform(sanitizeUtmValue),
    utm_medium: z.string().optional().transform(sanitizeUtmValue),
    utm_campaign: z.string().optional().transform(sanitizeUtmValue),
    utm_term: z.string().optional().transform(sanitizeUtmValue),
    utm_content: z.string().optional().transform(sanitizeUtmValue),
    referrer: z.string().optional().transform((v) => sanitizeReferrerOrigin(v, SITE_ORIGIN)),
    landing_page: z.string().optional().transform(sanitizePagePath),
    form_path: z.string().optional().transform(sanitizePagePath),
    attribution_channel: z
      .string()
      .optional()
      .transform((v) =>
        v === "campaign" || v === "referral" || v === "direct" ? v : undefined,
      ),
    honeypot: z.string().trim().max(0).optional(),
    timestamp: z.number().optional(),
  })
  .transform(({ honeypot, ...rest }) => {
    // attribution_channel serverseitig aus den normalisierten Feldern ableiten,
    // damit direkte POSTs die CRM-Attribution nicht verfälschen können. Nur
    // setzen, wenn der Client überhaupt Attribution mitschickt (Legacy-Payloads
    // bleiben unverändert ohne das Feld).
    if (
      rest.attribution_channel !== undefined ||
      rest.utm_source !== undefined ||
      rest.utm_medium !== undefined ||
      rest.utm_campaign !== undefined ||
      rest.utm_term !== undefined ||
      rest.utm_content !== undefined ||
      rest.referrer !== undefined
    ) {
      rest.attribution_channel = resolveChannel(rest);
    }
    return rest;
  });

export type LeadEndpointPayload = z.infer<typeof leadEndpointSchema>;
