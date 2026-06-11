// Screenshottet die Molecule3DView der gebauten UI während einer vollen
// 360°-Drag-Rotation — Frames für das README-GIF. Rotation läuft über echte
// Pointer-Events (0.01 rad/px in der View); 2π ≈ 628 px Drag-Distanz,
// aufgeteilt in mehrere Strokes, weil die Maus im Viewport bleiben muss.
import { chromium } from "playwright";
import { readFileSync } from "node:fs";

const payload = JSON.parse(readFileSync("/tmp/mol3d_payload.json", "utf8"));
const distUrl = process.argv[2]; // file:///…/ui/dist/index.html

const FRAMES = 48;
const TOTAL_DX = (2 * Math.PI) / 0.01; // volle Umdrehung um die y-Achse
const STEP = TOTAL_DX / FRAMES;

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 640, height: 500 },
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

const Y = 260;
let x = 60;
await page.mouse.move(x, Y);
await page.mouse.down();

for (let frame = 1; frame <= FRAMES; frame++) {
  await page.screenshot({ path: `/tmp/mol3d_frame_${String(frame).padStart(2, "0")}.png` });
  console.log(`frame ${frame}/${FRAMES}`);
  if (x + STEP > 620) {
    // Stroke neu ansetzen: Rotation bleibt erhalten (Deltas sind press-relativ)
    await page.mouse.up();
    x = 60;
    await page.mouse.move(x, Y);
    await page.mouse.down();
  }
  x += STEP;
  await page.mouse.move(x, Y);
  await page.waitForTimeout(40);
}

await page.mouse.up();
await browser.close();
