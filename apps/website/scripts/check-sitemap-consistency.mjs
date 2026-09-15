import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";

const distDir = join(process.cwd(), "dist");
const sitemapPath = join(distDir, "sitemap.xml");

if (!existsSync(sitemapPath)) {
  console.error(`FEHLER: ${sitemapPath} existiert nicht. Zuerst "npm run build" ausführen.`);
  process.exit(1);
}

const sitemapXml = readFileSync(sitemapPath, "utf-8");
const locMatches = [...sitemapXml.matchAll(/<loc>(.*?)<\/loc>/g)];

if (locMatches.length === 0) {
  console.error("FEHLER: Keine <loc>-Einträge in der Sitemap gefunden.");
  process.exit(1);
}

const missing = [];

for (const match of locMatches) {
  const url = new URL(match[1]);
  const pathname = url.pathname;
  const expectedFile = pathname.endsWith("/")
    ? join(distDir, pathname, "index.html")
    : join(distDir, pathname);

  if (!existsSync(expectedFile)) {
    missing.push({ pathname, expectedFile });
  }
}

if (missing.length > 0) {
  console.error(`FEHLER: ${missing.length} Sitemap-URL(s) haben keine entsprechende gebaute Datei:`);
  for (const item of missing) {
    console.error(`  - ${item.pathname} -> erwartet: ${item.expectedFile}`);
  }
  process.exit(1);
}

// Gegenrichtung: jede gebaute, indexierbare Seite muss auch in der Sitemap
// stehen. Ohne diese Prüfung fällt eine vergessene öffentliche Route nicht auf.
function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

const sitemapPaths = new Set(locMatches.map((m) => new URL(m[1]).pathname));
const notInSitemap = [];

for (const file of walk(distDir).filter((f) => f.endsWith(".html"))) {
  const html = readFileSync(file, "utf-8");
  // Seiten, die sich selbst auf noindex setzen, gehören bewusst nicht hinein.
  if (/<meta[^>]*name\s*=\s*"robots"[^>]*content\s*=\s*"[^"]*noindex/i.test(html)) continue;

  const rel = relative(distDir, file).replace(/\\/g, "/");
  if (rel === "404.html") continue;

  const pathname = "/" + rel.replace(/index\.html$/, "");
  if (!sitemapPaths.has(pathname)) notInSitemap.push(pathname);
}

if (notInSitemap.length > 0) {
  console.error(`FEHLER: ${notInSitemap.length} indexierbare Seite(n) fehlen in der Sitemap:`);
  for (const pathname of notInSitemap) {
    console.error(`  - ${pathname}`);
  }
  process.exit(1);
}

console.log(
  `OK: ${locMatches.length} Sitemap-URLs und alle indexierbaren Seiten stimmen überein.`,
);
process.exit(0);
