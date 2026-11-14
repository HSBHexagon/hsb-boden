import fs from "node:fs";
import path from "node:path";
import { createStaticPreview } from "./static-preview.mjs";
import { chromium } from "playwright";

const screenshotDir = path.resolve("node_modules/.cache/browser-audit");
fs.mkdirSync(screenshotDir, { recursive: true });

const server = createStaticPreview();

await new Promise((resolve) => server.listen(4321, "127.0.0.1", resolve));
console.log("Static server running on http://localhost:4321");

const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});

const viewports = [
  { name: "desktop-1440", width: 1440, height: 1000 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "mobile-390", width: 390, height: 844 },
];

const results = [];

for (const vp of viewports) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
  });
  const page = await context.newPage();

  const consoleMessages = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warning") {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  await page.goto("http://localhost:4321/", { waitUntil: "networkidle" });

  // Dismiss cookie banner if visible so measurements reflect natural page
  const cookieBtn = await page.$("#cookie-necessary");
  if (cookieBtn && (await cookieBtn.isVisible())) {
    await cookieBtn.click();
    await page.waitForTimeout(300);
  }

  // Sanftes Scrollen, damit lazy-loaded Bilder und Deferred-Assets laden
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let total = 0;
      const step = 600;
      const t = setInterval(() => {
        window.scrollBy(0, step);
        total += step;
        if (total >= document.body.scrollHeight) {
          clearInterval(t);
          window.scrollTo(0, 0);
          resolve();
        }
      }, 40);
    });
  });
  await page.waitForTimeout(400);

  const scrollHeight = await page.evaluate(() => document.documentElement.scrollHeight);
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  const hasHorizontalOverflow = scrollWidth > clientWidth;

  // Measure sections
  const sectionHeights = await page.evaluate(() => {
    const sections = Array.from(document.querySelectorAll("main > section, main > div, header, footer"));
    return sections.map((s) => ({
      tag: s.tagName.toLowerCase(),
      id: s.id || "",
      class: (s.className || "").slice(0, 40),
      height: Math.round(s.getBoundingClientRect().height),
    }));
  });

  // Verify images
  const brokenImages = await page.evaluate(() => {
    const imgs = Array.from(document.querySelectorAll("img"));
    return imgs
      .filter((img) => !img.complete || (img.naturalWidth === 0 && !img.src.endsWith(".svg")))
      .map((img) => img.src);
  });

  // Check Schema JSON-LD
  const jsonLdCount = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    return scripts.length;
  });

  // Take screenshot
  const screenshotPath = path.join(screenshotDir, `${vp.name}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });

  results.push({
    viewport: vp.name,
    dimensions: `${vp.width}x${vp.height}`,
    scrollHeight,
    hasHorizontalOverflow,
    consoleErrors: consoleMessages,
    brokenImages,
    jsonLdCount,
    screenshotPath,
    sectionHeights,
  });

  await context.close();
}

// Also test /kontakt/
const kontaktContext = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const kontaktPage = await kontaktContext.newPage();
await kontaktPage.goto("http://localhost:4321/kontakt/", { waitUntil: "networkidle" });
const kontaktFormStatus = await kontaktPage.evaluate(() => {
  const form = document.getElementById("lead-form");
  const submitBtn = document.getElementById("form-submit");
  return {
    deliveryConfigured: form?.getAttribute("data-delivery-configured"),
    submitDisabled: submitBtn?.hasAttribute("disabled"),
    submitText: submitBtn?.textContent?.trim(),
  };
});
await kontaktContext.close();

await browser.close();
server.close();

console.log(JSON.stringify({ results, kontaktFormStatus }, null, 2));
