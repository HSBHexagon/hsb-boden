import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const root = join(__dirname, "..");
const read = (path: string) => readFileSync(join(root, path), "utf8");

function sourceFiles(dir: string): string[] {
  return readdirSync(join(root, dir)).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(join(root, path)).isDirectory()) return sourceFiles(path);
    return /\.(astro|ts|css)$/.test(name) ? [path] : [];
  });
}

describe("Gestaltungsregeln der Website", () => {
  it("hält Unterseiten-Überschriften unter der Startseiten-Obergrenze von 3,25 rem", () => {
    const css = read("src/styles/global.css");
    const h1 = css.match(/\.h1 \{[^}]*font-size: clamp\([^,]+,[^,]+, ([\d.]+)rem\)/);
    expect(h1).not.toBeNull();
    expect(Number(h1?.[1])).toBeLessThanOrEqual(3.25);
  });

  it("verwendet keine Schrift unter 12 px", () => {
    const offenders = sourceFiles("src").filter((path) => /text-\[(?:1[01]px|0\.6\d*rem)\]/.test(read(path)));
    expect(offenders).toEqual([]);
  });

  it("stapelt die Auswahl im Reparaturformular auf schmalen Bildschirmen", () => {
    const form = read("src/components/forms/RepairPhotoForm.astro");
    expect(form).toContain('class="mt-3 grid gap-2 sm:grid-cols-3"');
    expect(form).not.toContain('class="mt-3 grid grid-cols-3 gap-2"');
  });

  it("benennt gleiche Anfragewege gleich", () => {
    const home = read("src/pages/index.astro");
    const modalLinks = [...home.matchAll(/<a[^>]*data-open-repair-modal[^>]*>([^<]+)<\/a>/g)].map((match) => match[1].trim());
    expect(modalLinks.length).toBeGreaterThan(0);
    expect(new Set(modalLinks)).toEqual(new Set(["Schadstelle melden"]));

    const header = read("src/components/layout/Header.astro");
    const contactLinks = [...header.matchAll(/href="\/kontakt\/">([^<]+)<\/a>/g)].map((match) => match[1].trim());
    expect(new Set(contactLinks)).toEqual(new Set(["Projekt besprechen"]));
  });

  it("verlangt im Kontaktformular nur die Angaben für den Erstkontakt", () => {
    const form = read("src/components/forms/LeadForm.astro");
    expect(form).not.toMatch(/<select required name="industry"/);
    expect(form).not.toMatch(/<select required name="liveOperation"/);
    expect(form).toMatch(/<select required name="projectType"/);
    // Der Endpunkt erwartet beide Felder weiterhin; ohne Angabe gehen neutrale Werte.
    expect(form).toContain('industry: fd.get("industry") || "sonstige"');
    expect(form).toContain('liveOperation: fd.get("liveOperation") || "unklar"');
  });

  it("zeigt in Seitenköpfen mit Foto das Bild ohne Verzögerung", () => {
    const hero = read("src/components/sections/PageHero.astro");
    expect(hero).toContain('loading="eager"');
    expect(hero).toContain('fetchpriority="high"');
  });
});
