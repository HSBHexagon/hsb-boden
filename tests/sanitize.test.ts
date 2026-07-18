import { describe, expect, it } from "vitest";
import { sanitizeJsonLd } from "../src/lib/sanitize";

describe("sanitizeJsonLd", () => {
  it("should return empty string if data is undefined", () => {
    expect(sanitizeJsonLd(undefined)).toBe("");
  });

  it("should securely serialize objects to prevent XSS", () => {
    const maliciousData = {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "Malicious Org </script><script>alert('xss')</script>"
    };

    const result = sanitizeJsonLd(maliciousData);

    // Ensure it correctly converted to JSON string and escaped HTML tags
    expect(result).toContain("Malicious Org \\u003C\\u002Fscript\\u003E\\u003Cscript\\u003Ealert('xss')\\u003C\\u002Fscript\\u003E");
    expect(result).not.toContain("</script>");
    expect(result).not.toContain("<script>");
  });

  it("should securely serialize array data", () => {
     const maliciousData = [
         { name: "John & Jane" }
     ];

     const result = sanitizeJsonLd(maliciousData);

     // Note that serialize-javascript doesn't escape & by default unless configured or required.
     // By default it escapes <, >, \u2028, \u2029
     // Let's verify standard parsing
     const parsed = JSON.parse(result);
     expect(parsed[0].name).toBe("John & Jane");
  });
});
