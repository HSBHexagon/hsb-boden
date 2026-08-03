import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

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

console.log(`OK: Alle ${locMatches.length} Sitemap-URLs haben eine entsprechende gebaute Datei.`);
process.exit(0);
