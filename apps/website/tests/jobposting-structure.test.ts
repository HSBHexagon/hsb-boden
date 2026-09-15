import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { getJobs } from "../src/data/jobs";
import { buildJobPostingJsonLd } from "../src/lib/schema";
import { getAllPublicPages } from "../src/lib/content";

// Ursprünglicher Fund (Search Console): /karriere/ enthielt ein Array aus
// mehreren JobPosting-Objekten in einer einzigen Seite/URL. Google erwartet
// pro Stelle eine eigene Seite mit genau einem JobPosting. Dieser Test
// verhindert die Rückkehr zum Array-Muster.
describe("JobPosting-Struktur", () => {
  it("die Karriere-Übersicht enthält kein JobPosting-JSON-LD mehr", () => {
    const source = readFileSync(
      join(process.cwd(), "src/pages/karriere/index.astro"),
      "utf8",
    );

    expect(source).not.toContain("JobPosting");
  });

  it("jede Job-Detailseite liefert genau ein JobPosting-Objekt (kein Array)", () => {
    for (const job of getJobs()) {
      const jsonLd = buildJobPostingJsonLd({
        slug: job.slug,
        title: job.title,
        description: job.fullDescription,
        employmentType: job.employmentType,
        occupationalCategory: job.occupationalCategory,
        datePosted: job.datePosted,
      });

      expect(Array.isArray(jsonLd)).toBe(false);
      expect(jsonLd["@type"]).toBe("JobPosting");
    }
  });

  it("setzt nur belegte Pflichtfelder, keine erfundenen Werte", () => {
    for (const job of getJobs()) {
      const jsonLd = buildJobPostingJsonLd({
        slug: job.slug,
        title: job.title,
        description: job.fullDescription,
        employmentType: job.employmentType,
        occupationalCategory: job.occupationalCategory,
        datePosted: job.datePosted,
      });

      expect(jsonLd.title).toBeTruthy();
      expect(jsonLd.description).toBeTruthy();
      expect(jsonLd.datePosted).toBe("2026-06-05");
      expect(jsonLd.hiringOrganization.name).toBe("HSB Hexagon Säurebau GmbH");
      expect(jsonLd.jobLocation.address.streetAddress).toBe("Benzstraße 6");
      expect(jsonLd.jobLocation.address.postalCode).toBe("48599");
      expect(jsonLd.jobLocation.address.addressRegion).toBe("Nordrhein-Westfalen");
      expect(jsonLd.jobLocation.address.addressLocality).toBe("Gronau");
      expect(jsonLd.jobLocation.address.addressCountry).toBe("DE");

      // baseSalary/validThrough/directApply bewusst nicht gesetzt (keine
      // belegten Werte in Projektquellen) statt geschätzt oder erfunden.
      expect(jsonLd).not.toHaveProperty("baseSalary");
      expect(jsonLd).not.toHaveProperty("validThrough");
      expect(jsonLd).not.toHaveProperty("directApply");
    }
  });

  it("jede Job-Detailseite hat eine eigene kanonische URL in der Sitemap", () => {
    const paths = getAllPublicPages().map((page) => page.canonicalPath);

    for (const job of getJobs()) {
      expect(paths).toContain(`/karriere/${job.slug}/`);
    }
  });

  it("sichtbarer Seiteninhalt und JSON-LD-Beschreibung stimmen überein (keine widersprüchlichen Aussagen)", () => {
    const source = readFileSync(
      join(process.cwd(), "src/pages/karriere/[slug].astro"),
      "utf8",
    );

    // Detailseite rendert job.fullDescription sichtbar UND übergibt dieselbe
    // Property an buildJobPostingJsonLd — keine getrennten Texte.
    expect(source).toContain("job.fullDescription");
    expect(source.match(/job\.fullDescription/g)?.length).toBeGreaterThanOrEqual(2);
  });
});
