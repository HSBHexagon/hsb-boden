import { describe, expect, it } from "vitest";
import { sanitizeJsonLd } from "../src/lib/sanitize";

describe("sanitizeJsonLd", () => {
  it("should return empty string for undefined input", () => {
    expect(sanitizeJsonLd(undefined)).toBe("");
  });

  it("should return stringified json for null", () => {
    expect(sanitizeJsonLd(null)).toBe("null");
  });

  it("should stringify normal objects correctly", () => {
    const data = { key: "value", num: 123, bool: true };
    expect(sanitizeJsonLd(data)).toBe('{"key":"value","num":123,"bool":true}');
  });

  it("should escape HTML brackets and ampersands", () => {
    const data = { html: "<script>alert('XSS & more');</script>" };
    const result = sanitizeJsonLd(data);
    expect(result).toBe('{"html":"\\u003cscript\\u003ealert(\'XSS \\u0026 more\');\\u003c/script\\u003e"}');
  });

  it("should escape line terminators", () => {
    const data = { lsep: "\u2028", psep: "\u2029" };
    const result = sanitizeJsonLd(data);
    expect(result).toBe('{"lsep":"\\u2028","psep":"\\u2029"}');
  });

  it("should handle nested structures with dangerous characters", () => {
    const data = {
      user: {
        name: "Test <user>",
        bio: "Bio with & \u2028 \u2029"
      },
      tags: ["<script>", "&", "\u2028"]
    };
    const result = sanitizeJsonLd(data);

    expect(result).toContain('\\u003cuser\\u003e');
    expect(result).toContain('\\u0026');
    expect(result).toContain('\\u2028');
    expect(result).toContain('\\u2029');
    expect(result).toContain('\\u003cscript\\u003e');
  });
});
