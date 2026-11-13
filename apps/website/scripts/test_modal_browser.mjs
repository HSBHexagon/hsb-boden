import assert from "node:assert/strict";
import { createStaticPreview } from "./static-preview.mjs";
import { chromium } from "playwright";

const server = createStaticPreview();

await new Promise((resolve) => server.listen(4322, "127.0.0.1", resolve));
console.log("Test server running on http://localhost:4322");

let browser;
try {
  browser = await chromium.launch({
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
  assert.ok(isOpen === false, "Test 1 (Initial closed):");
  console.log("Test 1 (Initial closed):", "PASS");

  // Test 2: Trigger via hash #foto-modal
  await page.goto("http://localhost:4322/#foto-modal", { waitUntil: "networkidle" });
  await page.waitForTimeout(200);
  isOpen = await page.evaluate(() => {
    const modal = document.getElementById("repair-modal");
    return modal?.hasAttribute("open") ?? false;
  });
  assert.ok(isOpen === true, "Test 2 (Hash trigger #foto-modal opens):");
  console.log("Test 2 (Hash trigger #foto-modal opens):", "PASS");

  // Test 3: Close button closes modal
  const closeBtn = await page.$("#repair-modal-close");
  await closeBtn.click();
  await page.waitForTimeout(200);
  isOpen = await page.evaluate(() => {
    const modal = document.getElementById("repair-modal");
    return modal?.hasAttribute("open") ?? false;
  });
  assert.ok(isOpen === false, "Test 3 (Close button closes):");
  console.log("Test 3 (Close button closes):", "PASS");

  // Test 4: Trigger via programmatic window.openRepairModal()
  await page.evaluate(() => {
    window.openRepairModal?.();
  });
  await page.waitForTimeout(200);
  isOpen = await page.evaluate(() => {
    const modal = document.getElementById("repair-modal");
    return modal?.hasAttribute("open") ?? false;
  });
  assert.ok(isOpen === true, "Test 4 (openRepairModal() opens):");
  console.log("Test 4 (openRepairModal() opens):", "PASS");

  // Test 5: ESC key closes modal
  await page.keyboard.press("Escape");
  await page.waitForTimeout(200);
  isOpen = await page.evaluate(() => {
    const modal = document.getElementById("repair-modal");
    return modal?.hasAttribute("open") ?? false;
  });
  assert.ok(isOpen === false, "Test 5 (Escape closes):");
  console.log("Test 5 (Escape closes):", "PASS");

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
  assert.ok(hasDropZone, "Test 6 (Modal contains functional dropzone & intents):");
  console.log("Test 6 (Modal contains functional dropzone & intents):", "PASS");

  // Gleichzeitige Dateiauswahl darf die Grenze von drei Bildern nicht überschreiten.
  const uploadState = await page.evaluate(async () => {
    const canvas = document.createElement("canvas");
    canvas.width = 2400;
    canvas.height = 800;
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    const originalDecode = window.createImageBitmap;
    window.createImageBitmap = async (...args) => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      return originalDecode(...args);
    };
    try {
      const input = document.querySelector("#modal-repair-photo-input");
      for (let batch = 0; batch < 2; batch += 1) {
        const data = new DataTransfer();
        for (let index = 0; index < 3; index += 1) {
          data.items.add(new File([blob], `test-${batch}-${index}.png`, { type: "image/png" }));
        }
        input.files = data.files;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
      const button = document.querySelector("#modal-repair-photo-submit");
      const disabledDuring = button.disabled;
      const form = document.querySelector("#modal-repair-photo-form");
      const deadline = Date.now() + 5000;
      while (form.getAttribute("aria-busy") === "true" && Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
      return {
        count: document.querySelectorAll("#modal-repair-photo-previews li").length,
        disabledDuring,
        enabledAfter: !button.disabled,
      };
    } finally {
      window.createImageBitmap = originalDecode;
    }
  });
  assert.deepEqual(uploadState, { count: 3, disabledDuring: true, enabledAfter: true });
  console.log("Test 7 (Concurrent photo selection): PASS");

} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
console.log("All browser tests completed.");
