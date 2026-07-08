/**
 * Safely serializes data to JSON for use in HTML script tags (like application/ld+json).
 * Escapes characters that could be used for XSS attacks when parsed by an HTML parser.
 */
export function sanitizeJsonLd(data: unknown): string {
  if (data === undefined) {
    return '';
  }
  return JSON.stringify(data)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    // Line terminators are valid in JSON but not in JS/HTML script contexts
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}
