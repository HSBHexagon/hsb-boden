import { getAllPublicPages } from "../lib/content";
import { canonical } from "../lib/seo";

export async function GET() {
  const pages = getAllPublicPages();
  const urls = pages
    // Conversion-Bestaetigungsseiten gehoeren nicht in die Sitemap, da die
    // Sitemap nur URLs enthalten soll, die in der Suche erscheinen sollen.
    .filter((page) => page.canonicalPath !== "/danke-projektanfrage/")
    // Google ignoriert priority/changefreq. Ein pauschales Build-Datum als
    // lastmod waere nicht verifizierbar; daher nur kanonische URLs ausgeben.
    .map((page) => `<url><loc>${canonical(page.canonicalPath)}</loc></url>`)
    .join("");

  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, {
    headers: {
      "Content-Type": "application/xml",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
