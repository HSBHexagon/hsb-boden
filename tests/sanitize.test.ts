import { describe, expect, it } from "vitest";
import { sanitizeJsonLd } from "../src/lib/sanitize";

describe("sanitizeJsonLd", () => {
  it("escapes dangerous characters (<, >, &)", () => {
    const input = {
      text: "<script>alert('xss')</script> & other bad stuff",
    };
    const output = sanitizeJsonLd(input);
    expect(output).toContain("\\u003cscript\\u003ealert('xss')\\u003c/script\\u003e \\u0026 other bad stuff");
  });

  it("returns empty string when input is undefined", () => {
    expect(sanitizeJsonLd(undefined)).toBe("");
  });

  it("returns valid JSON for primitives when no special chars are present", () => {
    expect(sanitizeJsonLd("hello")).toBe('"hello"');
    expect(sanitizeJsonLd(123)).toBe("123");
    expect(sanitizeJsonLd(true)).toBe("true");
    expect(sanitizeJsonLd(null)).toBe("null");
  });

  it("escapes line terminators", () => {
    const input = { text: "line 1\u2028line 2\u2029" };
    const output = sanitizeJsonLd(input);
    expect(output).toContain("line 1\\u2028line 2\\u2029");
  });
});
