import { getAllPublicPages } from "../lib/content";
import { canonical } from "../lib/seo";

// Priority-Map: Startseite > Leistungen/Branchen > Blog/Referenzen > Rest
const PRIORITY_MAP: Record<string, { priority: string; changefreq: string }> = {
  "/": { priority: "1.0", changefreq: "weekly" },
  "/leistungen/": { priority: "0.9", changefreq: "monthly" },
  "/branchen/": { priority: "0.9", changefreq: "monthly" },
  "/referenzen/": { priority: "0.8", changefreq: "monthly" },
  "/wissen/": { priority: "0.8", changefreq: "weekly" },
  "/projektablauf/": { priority: "0.8", changefreq: "monthly" },
  "/kontakt/": { priority: "0.7", changefreq: "monthly" },
  "/karriere/": { priority: "0.6", changefreq: "monthly" },
};

function getPriority(path: string) {
  // Exakte Übereinstimmung zuerst
  if (PRIORITY_MAP[path]) return PRIORITY_MAP[path];
  // Leistungs-Unterseiten
  if (path.startsWith("/leistungen/")) return { priority: "0.85", changefreq: "monthly" };
  // Branchen-Unterseiten
  if (path.startsWith("/branchen/")) return { priority: "0.85", changefreq: "monthly" };
  // Wissen-Artikel
  if (path.startsWith("/wissen/")) return { priority: "0.75", changefreq: "monthly" };
  // Referenzen
  if (path.startsWith("/referenzen/")) return { priority: "0.7", changefreq: "monthly" };
  // Standard
  return { priority: "0.5", changefreq: "yearly" };
}

export async function GET() {
  const lastmod = new Date().toISOString().split("T")[0]; // YYYY-MM-DD
  const pages = getAllPublicPages();

  const urls = pages
    .map((page) => {
      const { priority, changefreq } = getPriority(page.canonicalPath);
      return `<url><loc>${canonical(page.canonicalPath)}</loc><lastmod>${lastmod}</lastmod><changefreq>${changefreq}</changefreq><priority>${priority}</priority></url>`;
    })
    .join("");

  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, {
    headers: {
      "Content-Type": "application/xml",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
