// Playwright-Repro: unser dist/index.html gegen den ext-apps-Referenz-Host.
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const APP_HTML = "/Users/tom/Documents/projects/chemdraw-mcp/chemdraw_tool/ui/dist/index.html";

const hostHtml = `<!doctype html><html><body>
<iframe id="app" style="width:800px;height:600px"></iframe>
<script src="/host.bundle.js"></script>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage();

page.on("console", (m) => console.log(`[console:${m.type()}]`, m.text().slice(0, 300)));
page.on("pageerror", (e) => console.log("[pageerror]", String(e).slice(0, 300)));

await page.route("**/*", (route) => {
  const url = new URL(route.request().url());
  if (url.pathname === "/host.html") return route.fulfill({ contentType: "text/html", body: hostHtml });
  if (url.pathname === "/app.html") return route.fulfill({ contentType: "text/html", body: readFileSync(APP_HTML, "utf8") });
  if (url.pathname === "/host.bundle.js") return route.fulfill({ contentType: "text/javascript", body: readFileSync(join(here, "host.bundle.js"), "utf8") });
  if (url.pathname.endsWith(".json")) return route.fulfill({ contentType: "application/json", body: readFileSync(join(here, url.pathname.slice(1)), "utf8") });
  return route.fulfill({ status: 404, body: "not found" });
});

const payloadFile = process.env.PAYLOAD || "payload.json";
await page.goto("http://repro.test/host.html?payload=" + payloadFile);

// Bis zu 15 s warten, ob das Panel echten Inhalt rendert
let verdict = "TIMEOUT";
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(500);
  const status = await page.evaluate(() => window.__status);
  const text = await page.frames()[1]?.evaluate(() => document.body.innerText.slice(0, 200)).catch(() => "(frame weg)");
  if (i % 6 === 0) console.log(`[poll ${i}] host=${status} | iframe="${text?.slice(0, 80)}"`);
  if (text && !/Warte auf Daten|Verbinde|Verbindungsfehler/.test(text) && text.trim().length > 0) {
    verdict = "PANEL RENDERT: " + text.slice(0, 120).replace(/\n/g, " · ");
    break;
  }
  if (text && /Verbindungsfehler/.test(text)) { verdict = "VERBINDUNGSFEHLER im Panel"; break; }
}
console.log("\n=== ERGEBNIS:", verdict);
const diag = await page.frames()[1]?.evaluate(() => {
  const t = document.body.innerText;
  const i = t.indexOf("[DIAGNOSE]");
  return i >= 0 ? t.slice(i, i + 400) : "(kein DIAGNOSE-Badge)";
}).catch(() => "(frame weg)");
console.log("=== DIAGNOSE-BADGE:", diag);
await browser.close();
