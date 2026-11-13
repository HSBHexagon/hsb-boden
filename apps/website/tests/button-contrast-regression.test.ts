import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const root = join(__dirname, "..", "src");
const css = readFileSync(join(root, "styles", "global.css"), "utf8");

function astroFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return astroFiles(path);
    return name.endsWith(".astro") ? [path] : [];
  });
}

describe("Lesbarkeit von Links und Buttons", () => {
  it("lässt Farb-Utilities auf Links greifen (a-Regel liegt in der Basisebene)", () => {
    // Ungeschichtet überstimmt `a { color: inherit }` jede Tailwind-Utility wie text-white:
    // die mobile Kontaktleiste zeigte dann dunkle Schrift auf Rot.
    const unlayered = css.replace(/@layer\s+base\s*\{[\s\S]*?\n\}\n/g, "");
    expect(unlayered).not.toMatch(/(^|\n)a\s*\{\s*color:\s*inherit/);
    expect(css).toMatch(/@layer\s+base\s*\{\s*a\s*\{\s*color:\s*inherit;/);
  });

  it("verwendet den hellen Sekundärbutton nur auf dunklem Grund", () => {
    // .button-secondary hat weiße Schrift. Auf hellen Flächen ist er unsichtbar; dort gehört .button-secondary-dark hin.
    const allowed = new Map<string, number>([
      ["components/sections/CTASection.astro", 1], // bg-hsb-black
      ["pages/index.astro", 1], // dunkler Hero
    ]);
    const found = new Map<string, number>();
    for (const file of astroFiles(root)) {
      const count = (readFileSync(file, "utf8").match(/class="button-secondary(?!-)/g) ?? []).length;
      if (count) found.set(file.slice(root.length + 1).replaceAll("\\", "/"), count);
    }
    expect(Object.fromEntries(found)).toEqual(Object.fromEntries(allowed));
  });
});
