// Screenshottet die MechanismView der gebauten UI pro Step — Frames für das README-GIF.
// Navigation per "Next →"-Klick: die View hält den Step in useState, spätere
// Payload-Posts ändern ihn nicht.
import { chromium } from "playwright";
import { readFileSync } from "node:fs";

const payload = JSON.parse(readFileSync("/tmp/mech_payload.json", "utf8"));
const distUrl = process.argv[2]; // file:///…/ui/dist/index.html

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 640, height: 460 },
  deviceScaleFactor: 2,
});
await page.goto(distUrl);
await page.waitForTimeout(500);

await page.evaluate((data) => {
  window.postMessage(
    { jsonrpc: "2.0", method: "ontoolresult", params: { structuredContent: data } },
    "*"
  );
}, { ...payload, current_step: 1 });
await page.waitForTimeout(600);

const total = payload.steps.length;
for (let step = 1; step <= total; step++) {
  await page.screenshot({ path: `/tmp/mech_frame_${String(step).padStart(2, "0")}.png` });
  console.log(`frame ${step}/${total}`);
  if (step < total) {
    await page.getByRole("button", { name: /Next/ }).click();
    await page.waitForTimeout(350);
  }
}

await browser.close();
