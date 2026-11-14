/** Manual technical pages have fixed counterparts; never point a detail hreflang to a homepage. */
export const spanishStaticPaths: Record<string, string> = {
  "/wissen/ruettelkeramik-agi-s-40/": "/es/conocimiento/estructura-pavimento-vibrado-agi-s-40/",
  "/wissen/muster-abnahmeprotokoll/": "/es/conocimiento/protocolo-recepcion-pavimentos/",
  "/wissen/fugen-forensik/": "/es/conocimiento/analisis-juntas/",
  "/wissen/fugen-forensik/fliesen-hohl/": "/es/conocimiento/analisis-juntas/baldosas-huecas/",
  "/wissen/fugen-forensik/fuge-ausgewaschen/": "/es/conocimiento/analisis-juntas/junta-erosionada/",
  "/wissen/fugen-forensik/thermoschock-schaeden/": "/es/conocimiento/analisis-juntas/danos-choque-termico/",
  "/wissen/fugen-forensik/rinnenkante-gerissen/": "/es/conocimiento/analisis-juntas/fisuras-borde-canaleta/",
  "/wissen/fugen-forensik/hohlkehle-undicht/": "/es/conocimiento/analisis-juntas/filtraciones-media-cana/",
};

export function spanishStaticAlternates(germanPath: string) {
  const path = spanishStaticPaths[germanPath];
  if (!path) throw new Error(`Missing Spanish manual page: ${germanPath}`);
  return [{ lang: "de", path: germanPath }, { lang: "es", path }];
}
