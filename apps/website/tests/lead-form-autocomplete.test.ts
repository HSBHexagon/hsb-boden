import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// WCAG 2.2 AA 1.3.5 (Identify Input Purpose): Felder, die Daten über die
// nutzende Person erfassen, brauchen ein passendes autocomplete-Token. Ohne das
// füllt weder Browser noch Passwortmanager vor — auf Mobilgeräten kostet das
// Ausfüllzeit und damit Anfragen.
const source = readFileSync(
  join(process.cwd(), "src/components/forms/LeadForm.astro"),
  "utf8",
);

const expected: Array<[string, string]> = [
  ["firstName", "given-name"],
  ["lastName", "family-name"],
  ["company", "organization"],
  ["email", "email"],
  ["phone", "tel"],
];

describe("Lead-Formular autocomplete", () => {
  for (const [name, token] of expected) {
    it(`setzt autocomplete="${token}" auf ${name}`, () => {
      const field = source.match(
        new RegExp(`<input[^>]*name="${name}"[^>]*>`),
      )?.[0];

      expect(field, `Feld ${name} nicht gefunden`).toBeTruthy();
      expect(field).toContain(`autocomplete="${token}"`);
    });
  }

  it("setzt kein autocomplete auf die projektbezogenen Freitextfelder", () => {
    // areaSize/message beschreiben das Projekt, nicht die Person — ein
    // autocomplete-Token waere hier semantisch falsch.
    const areaSize = source.match(/<input[^>]*name="areaSize"[^>]*>/)?.[0];

    expect(areaSize).toBeTruthy();
    expect(areaSize).not.toContain("autocomplete=");
  });
});
