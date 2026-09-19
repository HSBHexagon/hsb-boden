import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Image Performance & Zero-CLS Guardrails", () => {
  const headerPath = resolve(__dirname, "../src/components/layout/Header.astro");
  const content = readFileSync(headerPath, "utf-8");

  it("header logo must target dark brand logo with explicit dimensions", () => {
    expect(content).toContain('/brand/hsb-boden-logo-dark.png');
    expect(content).toMatch(/width=["']60["']/);
    expect(content).toMatch(/height=["']44["']/);
  });

  it("header logo must declare decoding='async' and fetchpriority='high'", () => {
    expect(content).toMatch(/decoding=["']async["']/);
    expect(content).toMatch(/fetchpriority=["']high["']/);
  });
});
