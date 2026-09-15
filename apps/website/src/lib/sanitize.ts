import serialize from "serialize-javascript";

/**
 * Safely serializes data to JSON for use in HTML script tags (like application/ld+json).
 * Escapes characters that could be used for XSS attacks when parsed by an HTML parser.
 */
export function sanitizeJsonLd(data: unknown): string {
  if (data === undefined) {
    return "";
  }
  return serialize(data, { isJSON: true });
}
