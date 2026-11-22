// Rendert jede JSON-Datei in <dir> (Tool-Ergebnisse: {structuredContent, content}) als Panel
// hinter dem AppBridge-Host und speichert <name>.png daneben. Aufruf durch tests/gallery_ui.py.
// usage: node src/host/gallery.mjs <dir>
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join, basename } from "node:path";
import { mkdtempSync, readFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";

const dir = process.argv[2];
const here = dirname(fileURLToPath(import.meta.url));
const out = join(mkdtempSync(join(tmpdir(), "gallery-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });
const html = readFileSync(join(here, "..", "..", "dist", "index.html"), "utf8");

const browser = await chromium.launch();
for (const f of readdirSync(dir).filter((n) => n.endsWith(".json"))) {
  const toolResult = JSON.parse(readFileSync(join(dir, f), "utf8"));
  const page = await browser.newPage({ viewport: { width: 640, height: 560 } });
  await page.exposeFunction("__callTool", () => ({ isError: true, content: [{ type: "text", text: "Galerie: kein Server" }] }));
  await page.setContent("<body style='margin:0'></body>");
  await page.addScriptTag({ path: out });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput: {}, toolResult });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: join(dir, basename(f, ".json") + ".png") });
  console.log("✔", basename(f, ".json"));
  await page.close();
}
await browser.close();
