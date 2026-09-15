// Einmalige Bildoptimierung: große PNG/JPEG-Referenzbilder -> WebP.
// Sicher gegenüber imageService:"passthrough" (umgeht astro:assets komplett).
// Lauf: node scripts/optimize-images.mjs
import sharp from "sharp";
import { readFile, writeFile, stat } from "node:fs/promises";
import path from "node:path";

const dir = "public/media/hsb/current";
const files = [
  "referenzflaeche-1.png",
  "referenzflaeche-2.png",
  "referenzflaeche-3.png",
  "industrieboden-baustelle.jpeg",
];

const MAX_W = 1200; // ausreichend für Retina bei Kartenbreite ~480-600px
let before = 0;
let after = 0;

for (const file of files) {
  const src = path.join(dir, file);
  const out = path.join(dir, file.replace(/\.(png|jpe?g)$/i, ".webp"));
  const input = await readFile(src);
  const meta = await sharp(input).metadata();
  const width = Math.min(meta.width ?? MAX_W, MAX_W);
  const webp = await sharp(input).resize({ width, withoutEnlargement: true }).webp({ quality: 78 }).toBuffer();
  await writeFile(out, webp);
  const inKB = Math.round((await stat(src)).size / 1024);
  const outKB = Math.round(webp.length / 1024);
  before += inKB;
  after += outKB;
  console.log(`${file}: ${inKB} KB -> ${path.basename(out)} ${outKB} KB (${meta.width}px -> ${width}px)`);
}

console.log(`\nGESAMT: ${before} KB -> ${after} KB  (-${Math.round((1 - after / before) * 100)}%)`);
