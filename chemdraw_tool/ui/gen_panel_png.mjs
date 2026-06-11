// Screenshottet eine beliebige Panel-View der gebauten UI aus einem Payload-JSON —
// für statische README-Bilder (z.B. AnkiDeckView).
// usage: node gen_panel_png.mjs <distUrl> <payload.json> <out.png> [width] [height]
import { chromium } from "playwright";
import { readFileSync } from "node:fs";

const [distUrl, payloadPath, outPath, w = "640", h = "420"] = process.argv.slice(2);
const payload = JSON.parse(readFileSync(payloadPath, "utf8"));

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: Number(w), height: Number(h) },
  deviceScaleFactor: 2,
});
await page.goto(distUrl);
await page.waitForTimeout(500);

await page.evaluate((data) => {
  window.postMessage(
    { jsonrpc: "2.0", method: "ontoolresult", params: { structuredContent: data } },
    "*"
  );
}, payload);
await page.waitForTimeout(600);

await page.screenshot({ path: outPath });
await browser.close();
console.log(outPath);
