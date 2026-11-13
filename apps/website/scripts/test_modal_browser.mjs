import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const distDir = path.resolve("dist");

// Löst einen Anfragepfad innerhalb von dist/ auf. Alles, was nach dem
// Normalisieren außerhalb liegt (z. B. "/../../etc/passwd"), wird verworfen.
function resolveInDist(requestPath) {
  const resolved = path.resolve(distDir, "." + path.posix.normalize("/" + requestPath));
  if (resolved !== distDir && !resolved.startsWith(distDir + path.sep)) return null;
  return resolved;
}

function findFile(requestPath) {
  const base = resolveInDist(requestPath);
  if (!base) return null;
  for (const candidate of [base, base + ".html", path.join(base, "index.html")]) {
    if (!candidate.startsWith(distDir + path.sep)) continue;
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
  }
  return null;
}

const server = http.createServer((req, res) => {
  let reqPath;
  try {
    reqPath = decodeURIComponent(req.url.split("?")[0]);
  } catch {
    res.writeHead(400);
    res.end("Bad Request");
    return;
  }
  if (reqPath.endsWith("/")) reqPath += "index.html";
  const filePath = findFile(reqPath);

  if (filePath) {
    const ext = path.extname(filePath);
    const mimeTypes = {
      ".html": "text/html",
      ".css": "text/css",
      ".js": "application/javascript",
      ".json": "application/json",
      ".webp": "image/webp",
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".svg": "image/svg+xml",
      ".woff2": "font/woff2",
    };
    res.writeHead(200, { "Content-Type": mimeTypes[ext] || "application/octet-stream" });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end("Not Found");
  }
});

await new Promise((resolve) => server.listen(4322, resolve));
console.log("Test server running on http://localhost:4322");

const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});

const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

// Test 1: Page load without hash - modal should be closed
await page.goto("http://localhost:4322/", { waitUntil: "networkidle" });
let isOpen = await page.evaluate(() => {
  const modal = document.getElementById("repair-modal");
  return modal?.hasAttribute("open") ?? false;
});
console.log("Test 1 (Initial closed):", isOpen === false ? "PASS" : "FAIL");

// Test 2: Trigger via hash #foto-modal
await page.goto("http://localhost:4322/#foto-modal", { waitUntil: "networkidle" });
await page.waitForTimeout(200);
isOpen = await page.evaluate(() => {
  const modal = document.getElementById("repair-modal");
  return modal?.hasAttribute("open") ?? false;
});
console.log("Test 2 (Hash trigger #foto-modal opens):", isOpen === true ? "PASS" : "FAIL");

// Test 3: Close button closes modal
const closeBtn = await page.$("#repair-modal-close");
await closeBtn.click();
await page.waitForTimeout(200);
isOpen = await page.evaluate(() => {
  const modal = document.getElementById("repair-modal");
  return modal?.hasAttribute("open") ?? false;
});
console.log("Test 3 (Close button closes):", isOpen === false ? "PASS" : "FAIL");

// Test 4: Trigger via programmatic window.openRepairModal()
await page.evaluate(() => {
  window.openRepairModal?.();
});
await page.waitForTimeout(200);
isOpen = await page.evaluate(() => {
  const modal = document.getElementById("repair-modal");
  return modal?.hasAttribute("open") ?? false;
});
console.log("Test 4 (openRepairModal() opens):", isOpen === true ? "PASS" : "FAIL");

// Test 5: ESC key closes modal
await page.keyboard.press("Escape");
await page.waitForTimeout(200);
isOpen = await page.evaluate(() => {
  const modal = document.getElementById("repair-modal");
  return modal?.hasAttribute("open") ?? false;
});
console.log("Test 5 (Escape closes):", isOpen === false ? "PASS" : "FAIL");

// Test 6: Verify form inside modal is functional
await page.evaluate(() => {
  window.openRepairModal?.();
});
await page.waitForTimeout(200);
const hasDropZone = await page.evaluate(() => {
  const drop = document.querySelector("#modal-repair-photo [data-drop-zone]");
  const intentRadios = document.querySelectorAll("#modal-repair-photo input[name='intent']");
  return drop !== null && intentRadios.length === 3;
});
console.log("Test 6 (Modal contains functional dropzone & intents):", hasDropZone ? "PASS" : "FAIL");

await browser.close();
server.close();
console.log("All browser tests completed.");
