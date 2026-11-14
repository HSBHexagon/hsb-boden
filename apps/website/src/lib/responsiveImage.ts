// Projektfotos unter /media/hsb/projekte/ liegen zusätzlich als 640px-Variante
// ("<name>-640.webp") vor. Mobilgeräte laden damit ~70 % weniger Bilddaten.
// Für alle anderen Pfade gibt es kein srcset (undefined → Attribut entfällt).
const PROJECT_WIDTHS: Record<string, number> = {
  "beschichtete-halle": 1200,
  "brauerei-tanks-keramik": 1200,
  "chemie-anlage-keramik": 1600,
  "entwaesserungsrinne-detail": 1200,
  "halle-doppelrinne-keramik": 1600,
  "halle-in-ausfuehrung": 1600,
  "hexagon-rinne-detail": 1200,
  "keramik-halle-rinnen": 1600,
  "pharma-halle-keramik": 1512,
  "produktionsanlage-keramik": 1600,
  "saeulen-anschluss-keramik": 1200,
  "verlegung-keramik": 1200,
};

const PROJECT_IMAGE = /^\/media\/hsb\/projekte\/([a-z0-9-]+)\.webp$/;

export function projectSrcset(src: string): string | undefined {
  const match = PROJECT_IMAGE.exec(src);
  if (!match) return undefined;
  const width = PROJECT_WIDTHS[match[1]];
  if (!width) return undefined;
  return `/media/hsb/projekte/${match[1]}-640.webp 640w, ${src} ${width}w`;
}
