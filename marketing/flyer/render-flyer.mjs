// Rendert flyer.html via Playwright/Chromium als A4-PDF (digitaler Anhang, < 1 MB).
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { statSync } from "node:fs";

const here = dirname(fileURLToPath(import.meta.url));
const htmlPath = resolve(here, "flyer.html");
const outPath = resolve(here, "HSB-Industrieboden-Flyer.pdf");

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto("file://" + htmlPath, { waitUntil: "networkidle" });
await page.emulateMedia({ media: "print" });
await page.pdf({
  path: outPath,
  format: "A4",
  printBackground: true,
  preferCSSPageSize: true,
});
await browser.close();

const kb = statSync(outPath).size / 1024;
console.log(`PDF: ${outPath}`);
console.log(`Größe: ${kb.toFixed(0)} KB  (${(kb / 1024).toFixed(2)} MB)`);
