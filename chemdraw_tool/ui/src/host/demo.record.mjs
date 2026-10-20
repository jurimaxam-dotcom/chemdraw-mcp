// Demo-Aufnahme: dasselbe Setup wie host.e2e.mjs (sandboxed iframe, echte AppBridge,
// echter MCP-Server), aber als Video mit sichtbarem Mauszeiger. Keine Attrappe von
// Claude Desktop: gezeigt wird nur das Panel, so wie der Server es ausliefert.
// usage: node src/host/demo.record.mjs <ausgabeordner> [szene …]
//   Szenen: molecule (Standard), compare, reaction, 3d, mechanism
//   (3d und mechanism gibt es nur im vollen Profil — der Recorder startet den Server deshalb mit CHEMDRAW_PROFILE=full)
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, renameSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const outDir = resolve(process.argv[2] ?? join(tmpdir(), "chemdraw-demo"));
const szenen = process.argv.slice(3).length ? process.argv.slice(3) : ["molecule"];
mkdirSync(outDir, { recursive: true });

const SZENEN = {
  molecule: { tool: "generate_molecule", args: { name_or_smiles: "aspirin" }, ablauf: "struktur-gruppen-daten" },
  compare: { tool: "compare_molecules", args: { structures: ["ibuprofen", "naproxen", "ketoprofen"] }, ablauf: "ansehen" },
  reaction: { tool: "generate_reaction", args: { reactants: ["acetic acid", "ethanol"], products: ["ethyl acetate", "water"], conditions: "H2SO4, heat" }, ablauf: "ansehen" },
  "3d": { tool: "generate_3d", args: { name_or_smiles: "caffeine", label: "Caffeine" }, ablauf: "drehen" },
  mechanism: { tool: "generate_mechanism", args: { reaction_type: "fischer_ester", substrates: ["acetic acid", "ethanol"] }, ablauf: "schritte" },
};

const hostJs = join(mkdtempSync(join(tmpdir(), "panel-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: hostJs, logLevel: "error" });

const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const client = new Client({ name: "panel-demo", version: "0.0.0" });
// Wegwerf-HOME wie im Host-Test: die Aufnahme soll ~/ChemDraw-Output nicht füllen
const wegwerfHome = mkdtempSync(join(tmpdir(), "panel-home-"));
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "full" }, cwd: repo }));
// Im Bild soll ~/ChemDraw-Output stehen, nicht der Wegwerf-Pfad: Ergebnis auf ein neutrales Home umschreiben
const neutral = (r) => JSON.parse(JSON.stringify(r).replaceAll(wegwerfHome, "/Users/demo"));

const W = 720, H = 560;
const browser = await chromium.launch();
try {
  const tools = (await client.listTools()).tools;
  for (const name of szenen) {
    const s = SZENEN[name];
    if (!s) throw new Error(`unbekannte Szene: ${name}`);
    const toolResult = neutral(await client.callTool({ name: s.tool, arguments: s.args }));
    if (toolResult.isError) throw new Error(`${s.tool}: ` + JSON.stringify(toolResult.content).slice(0, 300));
    const uri = tools.find((t) => t.name === s.tool)._meta.ui.resourceUri;
    const html = (await client.readResource({ uri })).contents[0].text;

    const context = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: outDir, size: { width: W, height: H } }, colorScheme: "light" });
    const page = await context.newPage();
    await page.exposeFunction("__callTool", (p) => client.callTool(p));
    await page.setContent(`<body style="margin:0;background:#fafbf9"></body>`);
    await page.addScriptTag({ path: hostJs });
    await page.evaluate((a) => window.__startHost(a), { html, toolInput: s.args, toolResult });
    await page.locator("iframe").evaluate((el, [w, h]) => { el.style.width = `${w}px`; el.style.height = `${h}px`; }, [W, H]);
    // Zeiger im Elternfenster: Playwright-Videos zeigen den echten Mauszeiger nicht
    await page.evaluate(() => {
      const c = document.createElement("div");
      c.id = "demo-cursor";
      c.style.cssText = "position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;background:rgba(20,20,20,.55);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);pointer-events:none;z-index:9;transition:left .45s ease,top .45s ease,transform .12s";
      document.body.appendChild(c);
    });
    const frame = page.frames().find((f) => f !== page.mainFrame());
    const zeigeAuf = async (locator) => {
      const b = await locator.boundingBox();
      const x = b.x + b.width / 2, y = b.y + b.height / 2;
      await page.evaluate(([x, y]) => Object.assign(document.getElementById("demo-cursor").style, { left: `${x - 9}px`, top: `${y - 9}px` }), [x, y]);
      await page.mouse.move(x, y, { steps: 12 });
      await page.waitForTimeout(500);
    };
    const klick = async (locator) => {
      await zeigeAuf(locator);
      await page.evaluate(() => { document.getElementById("demo-cursor").style.transform = "scale(.7)"; });
      await locator.click();
      await page.waitForTimeout(140);
      await page.evaluate(() => { document.getElementById("demo-cursor").style.transform = ""; });
    };

    await page.waitForTimeout(1800);
    if (s.ablauf === "struktur-gruppen-daten") {
      const gruppen = frame.locator("button.functional-group");
      const n = Math.min(await gruppen.count(), 3);
      for (let i = 0; i < n; i++) { await zeigeAuf(gruppen.nth(i)); await page.waitForTimeout(900); }
      await klick(frame.getByText("Data", { exact: true }));
      await frame.getByText("IUPAC name").first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(2600);
      await klick(frame.getByText("Structure", { exact: true }));
      await page.waitForTimeout(1500);
    } else if (s.ablauf === "drehen") {
      // Ziehen dreht das Modell; Strich neu ansetzen, die Drehung bleibt erhalten
      for (let zug = 0; zug < 3; zug++) {
        await page.evaluate(() => Object.assign(document.getElementById("demo-cursor").style, { left: "111px", top: "271px", transition: "none" }));
        await page.mouse.move(120, 280);
        await page.mouse.down();
        for (let x = 120; x <= 600; x += 12) {
          await page.mouse.move(x, 280);
          await page.evaluate((x) => { document.getElementById("demo-cursor").style.left = `${x - 9}px`; }, x);
          await page.waitForTimeout(30);
        }
        await page.mouse.up();
      }
      await page.waitForTimeout(800);
    } else if (s.ablauf === "schritte") {
      await klick(frame.getByText("Step by step", { exact: true }));
      await page.waitForTimeout(1200);
      const weiter = frame.getByRole("button", { name: /Next/ });
      for (let i = 0; i < 4 && (await weiter.isEnabled().catch(() => false)); i++) { await klick(weiter); await page.waitForTimeout(1400); }
    } else {
      await page.waitForTimeout(3500);
    }
    const video = page.video();
    await context.close();
    renameSync(await video.path(), join(outDir, `${name}.webm`));
    console.log(`✔ ${name}.webm`);
  }
} finally {
  await browser.close();
  await client.close();
}
