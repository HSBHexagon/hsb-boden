import { describe, expect, it } from "vitest";
import { sanitizeJsonLd } from "../src/lib/sanitize";

describe("sanitizeJsonLd", () => {
  it("should return an empty string for undefined input", () => {
    expect(sanitizeJsonLd(undefined)).toBe("");
  });

  it("should correctly serialize normal JSON without special characters", () => {
    const data = { name: "Test", value: 123 };
    expect(sanitizeJsonLd(data)).toBe('{"name":"Test","value":123}');
  });

  it("should escape the < character", () => {
    const data = { html: "<script>alert('xss')</script>" };
    expect(sanitizeJsonLd(data)).toBe('{"html":"\\u003cscript\\u003ealert(\'xss\')\\u003c/script\\u003e"}');
  });

  it("should escape the > character", () => {
    const data = { tag: "</div>" };
    expect(sanitizeJsonLd(data)).toBe('{"tag":"\\u003c/div\\u003e"}');
  });

  it("should escape the & character", () => {
    const data = { text: "this & that" };
    expect(sanitizeJsonLd(data)).toBe('{"text":"this \\u0026 that"}');
  });

  it("should escape line separator characters", () => {
    const data = { text: "line1\u2028line2" };
    expect(sanitizeJsonLd(data)).toBe('{"text":"line1\\u2028line2"}');
  });

  it("should escape paragraph separator characters", () => {
    const data = { text: "para1\u2029para2" };
    expect(sanitizeJsonLd(data)).toBe('{"text":"para1\\u2029para2"}');
  });

  it("should escape all special characters in a complex nested object", () => {
    const data = {
      nested: {
        attack: "<script>&",
        more: {
          text: "a\u2028b\u2029c>"
        }
      }
    };
    expect(sanitizeJsonLd(data)).toBe(
      '{"nested":{"attack":"\\u003cscript\\u003e\\u0026","more":{"text":"a\\u2028b\\u2029c\\u003e"}}}'
    );
  });
});
