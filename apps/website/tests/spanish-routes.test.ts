import { describe, expect, it } from "vitest";
import { spanishArticles } from "../src/data/es/articles";
import { spanishIndustries } from "../src/data/es/industries";
import { spanishRegionalGuides } from "../src/data/es/regionalGuides";
import { spanishServices } from "../src/data/es/services";
import { getAllPublicPages } from "../src/lib/content";
import {
  hasSpanishEquivalent,
  spanishAlternates,
  toGermanPath,
  toSpanishPath,
} from "../src/lib/spanishPaths";

describe("Spanish localization routing and hreflang integrity", () => {
  it("maps core German hubs and tools bidirectionally to Spanish", () => {
    const pairs: Array<[string, string]> = [
      ["/", "/es/"],
      ["/leistungen/", "/es/servicios/"],
      ["/branchen/", "/es/sectores/"],
      ["/wissen/", "/es/conocimiento/"],
      ["/referenzen/", "/es/referencias/"],
      ["/beanspruchungs-check/", "/es/analisis-cargas/"],
      ["/rechner/sanierungsfenster/", "/es/calculadora-paradas/"],
      ["/danke-projektanfrage/", "/es/gracias/"],
    ];

    for (const [de, es] of pairs) {
      expect(toSpanishPath(de)).toBe(es);
      expect(toGermanPath(es)).toBe(de);
      expect(hasSpanishEquivalent(de)).toBe(true);
      expect(hasSpanishEquivalent(es)).toBe(true);
    }
  });

  it("maps all 9 services, 6 industries, 12 articles, and 9 regions bidirectionally", () => {
    expect(spanishServices).toHaveLength(9);
    expect(spanishIndustries).toHaveLength(6);
    expect(spanishArticles).toHaveLength(12);
    expect(Object.keys(spanishRegionalGuides)).toHaveLength(9);

    for (const service of spanishServices) {
      const de = `/leistungen/${service.slug}/`;
      const es = `/es/servicios/${service.localizedSlug}/`;
      expect(toSpanishPath(de)).toBe(es);
      expect(toGermanPath(es)).toBe(de);
      expect(spanishAlternates(de)).toEqual([
        { lang: "de", path: de },
        { lang: "es", path: es },
        { lang: "x-default", path: de },
      ]);
    }

    for (const industry of spanishIndustries) {
      const de = `/branchen/${industry.slug}/`;
      const es = `/es/sectores/${industry.localizedSlug}/`;
      expect(toSpanishPath(de)).toBe(es);
      expect(toGermanPath(es)).toBe(de);
    }

    for (const article of spanishArticles) {
      const de = `/wissen/${article.slug}/`;
      const es = `/es/conocimiento/${article.localizedSlug}/`;
      expect(toSpanishPath(de)).toBe(es);
      expect(toGermanPath(es)).toBe(de);
    }

    for (const regionSlug of Object.keys(spanishRegionalGuides)) {
      const de = `/standorte/${regionSlug}/`;
      const es = `/es/regiones/${regionSlug}/`;
      expect(toSpanishPath(de)).toBe(es);
      expect(toGermanPath(es)).toBe(de);
    }
  });

  it("includes all Spanish indexable routes in getAllPublicPages()", () => {
    const publicPaths = new Set(
      getAllPublicPages().map((page) => page.canonicalPath),
    );
    expect(publicPaths.has("/es/")).toBe(true);
    expect(publicPaths.has("/es/servicios/")).toBe(true);
    expect(publicPaths.has("/es/sectores/")).toBe(true);
    expect(publicPaths.has("/es/conocimiento/")).toBe(true);
    expect(publicPaths.has("/es/referencias/")).toBe(true);
    expect(publicPaths.has("/es/analisis-cargas/")).toBe(true);
    expect(publicPaths.has("/es/calculadora-paradas/")).toBe(true);
  });
});
