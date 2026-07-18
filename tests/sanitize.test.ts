import { describe, it, expect } from "vitest";
import { sanitizeJsonLd } from "../src/lib/sanitize";

describe("sanitizeJsonLd", () => {
  it("should return an empty string for undefined input", () => {
    expect(sanitizeJsonLd(undefined)).toBe("");
  });

  it("should securely serialize standard JSON objects", () => {
    const data = { title: "Hello", content: "World" };
    expect(sanitizeJsonLd(data)).toBe('{"title":"Hello","content":"World"}');
  });

  it("should escape unsafe HTML characters (<, >)", () => {
    const data = { text: "<script>alert('xss & more')</script>" };
    const result = sanitizeJsonLd(data);
    expect(result).not.toContain("<script>");
    expect(result).not.toContain("</script>");
    expect(result).toContain("\\u003Cscript\\u003Ealert('xss & more')\\u003C\\u002Fscript\\u003E");
  });

  it("should escape line terminators which are invalid in inline scripts", () => {
    // \u2028 and \u2029 are valid in JSON but break JS if injected directly
    const data = { text: "Line 1\u2028Line 2\u2029Line 3" };
    const result = sanitizeJsonLd(data);
    expect(result).toContain("Line 1\\u2028Line 2\\u2029Line 3");
  });
});
