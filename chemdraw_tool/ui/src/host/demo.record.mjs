// Demo-Aufnahme: dasselbe Setup wie host.e2e.mjs (sandboxed iframe, echte AppBridge,
// echter MCP-Server), aber als Video mit sichtbarem Mauszeiger. Keine Attrappe von
// Claude Desktop: gezeigt wird nur das Panel, so wie der Server es ausliefert.
// usage: node src/host/demo.record.mjs <ausgabeordner> [--hires] [--clicks] [szene …]
//   --hires: doppelte Aufnahmeauflösung (1440×1120), ohne Click-Log oder höheres Layout
//   --clicks: zusätzlich <szene>.clicks.json (Datenvertrag ClickLog, Format siehe Shorts-Montage)
//             und höhere Aufnahme in doppelter Größe (1440×1440) für die Shorts-Montage
//   Szenen: molecule (Standard), compare, reaction, 3d, mechanism
//   (3d und mechanism gibt es nur im vollen Profil — der Recorder startet den Server deshalb mit CHEMDRAW_PROFILE=full)
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, renameSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { recordingOptions } from "./demo-options.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const outDir = resolve(process.argv[2] ?? join(tmpdir(), "chemdraw-demo"));
const { mitKlicks, szenen, zoom: ZOOM, width: W, height: H } = recordingOptions(process.argv.slice(3));
// Shorts zoomen bis ~1,7× in eine 1080 breite Spur: 720-px-Video wäre dort matschig.
// deviceScaleFactor hilft nicht — recordVideo nimmt in CSS-Pixeln auf und polstert nur
// auf (gemessen 20.10.2026). Deshalb bleibt das Panel 720×560 CSS-px groß und wird als
// Vektor per transform ×2 in ein doppelt so großes Fenster gezeichnet.
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

// Shorts-Modus: Panel höher, damit Gruppen-Karte und Datenblatt ganz ins Bild passen.
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

    const context = await browser.newContext({ viewport: { width: W * ZOOM, height: H * ZOOM }, recordVideo: { dir: outDir, size: { width: W * ZOOM, height: H * ZOOM } }, colorScheme: "light" });
    const page = await context.newPage();
    // Nullpunkt des Click-Logs: das Video beginnt mit der Seite
    const t0 = Date.now();
    const jetzt = () => Date.now() - t0;
    const klicks = [];
    const rectVon = (b) => ({ x: b.x, y: b.y, w: b.width, h: b.height });
    // content = der Bereich, den die Kamera mitrahmen soll (ClickLog-Feld)
    const vereint = async (...locs) => {
      const bs = (await Promise.all(locs.map((l) => l.boundingBox()))).filter(Boolean);
      const x0 = Math.min(...bs.map((b) => b.x)), y0 = Math.min(...bs.map((b) => b.y));
      const x1 = Math.max(...bs.map((b) => b.x + b.width)), y1 = Math.min(Math.max(...bs.map((b) => b.y + b.height)), H * ZOOM);
      return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
    };
    await page.exposeFunction("__callTool", (p) => client.callTool(p));
    await page.setContent(`<body style="margin:0;background:#fafbf9"></body>`);
    await page.addScriptTag({ path: hostJs });
    await page.evaluate((a) => window.__startHost(a), { html, toolInput: s.args, toolResult });
    await page.locator("iframe").evaluate((el, [w, h, z]) => {
      el.style.width = `${w}px`; el.style.height = `${h}px`;
      if (z !== 1) { el.style.transform = `scale(${z})`; el.style.transformOrigin = "0 0"; }
    }, [W, H, ZOOM]);
    // Zeiger im Elternfenster: Playwright-Videos zeigen den echten Mauszeiger nicht
    await page.evaluate((z) => {
      const c = document.createElement("div");
      c.id = "demo-cursor";
      c.style.cssText = "position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;background:rgba(20,20,20,.55);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);pointer-events:none;z-index:9;transition:left .45s ease,top .45s ease,transform .12s";
      if (z !== 1) c.style.scale = String(z);
      document.body.appendChild(c);
    }, ZOOM);
    const frame = page.frames().find((f) => f !== page.mainFrame());
    // Hover = Ereignis ohne tDownMs (Fokus-Beat), Klick = mit tDownMs
    const zeigeAuf = async (locator, label, content) => {
      const b = await locator.boundingBox();
      const x = b.x + b.width / 2, y = b.y + b.height / 2;
      const ereignis = { label, tDepartMs: jetzt(), tMs: 0, x, y, rect: rectVon(b), ...(content && { content }) };
      await page.evaluate(([x, y]) => Object.assign(document.getElementById("demo-cursor").style, { left: `${x - 9}px`, top: `${y - 9}px` }), [x, y]);
      await page.mouse.move(x, y, { steps: 12 });
      ereignis.tMs = jetzt();
      klicks.push(ereignis);
      await page.waitForTimeout(500);
      return ereignis;
    };
    const klick = async (locator, label) => {
      const ereignis = await zeigeAuf(locator, label);
      await page.evaluate(() => { document.getElementById("demo-cursor").style.transform = "scale(.7)"; });
      ereignis.tDownMs = jetzt();
      await locator.click();
      ereignis.tMs = jetzt();
      await page.waitForTimeout(140);
      await page.evaluate(() => { document.getElementById("demo-cursor").style.transform = ""; });
    };
    let trimBeforeMs = 0, endeMs = null;

    await page.waitForTimeout(1800);
    if (s.ablauf === "struktur-gruppen-daten") {
      const gruppen = frame.locator("button.functional-group");
      await gruppen.first().waitFor();
      trimBeforeMs = jetzt() - 600;
      const n = Math.min(await gruppen.count(), 3);
      const strukturUndGruppen = mitKlicks ? await vereint(frame.locator(".structure-canvas"), gruppen.first(), gruppen.nth(n - 1)) : undefined;
      for (let i = 0; i < n; i++) { await zeigeAuf(gruppen.nth(i), `group ${i + 1}`, strukturUndGruppen); await page.waitForTimeout(900); }
      await klick(frame.getByText("Data", { exact: true }), "data");
      const datenKlick = klicks.at(-1);
      const iupac = frame.getByText("IUPAC name").first();
      await iupac.waitFor({ timeout: 30000 });
      // Datenblatt als Beat, damit die Kamera das Ergebnis rahmt statt den Knopf
      if (mitKlicks) {
        // Beschriftungen + Werte (ohne Kopier-Knöpfe), damit die Kamera lesbar nah rangeht
        const zeilen = frame.locator(".source-row");
        const blatt = await vereint(zeilen.first().locator("dt"), zeilen.last().locator("dt"), zeilen.filter({ hasText: "InChIKey" }).locator("dd > span"));
        // tDepartMs: Kamera verlässt den Knopf 0,7 s nach dem Druck (upstream ACTION_WATCH_S)
        // und fährt über „Loading…" raus, statt erst zu starten, wenn das Blatt schon steht
        klicks.push({ label: "data sheet", tDepartMs: datenKlick.tDownMs + 700, tMs: jetzt(), x: blatt.x + blatt.w / 2, y: blatt.y + blatt.h / 2, rect: blatt, content: blatt });
      }
      // Shorts: die Kamera braucht ~1,2 s zum Rausfahren, danach soll das Blatt lesbar stehen
      await page.waitForTimeout(mitKlicks ? 3800 : 2600);
      endeMs = jetzt();
      await klick(frame.getByText("Structure", { exact: true }), "structure");
      await page.waitForTimeout(1500);
    } else if (s.ablauf === "drehen") {
      // Ziehen dreht das Modell; Strich neu ansetzen, die Drehung bleibt erhalten
      for (let zug = 0; zug < 3; zug++) {
        await page.evaluate((z) => Object.assign(document.getElementById("demo-cursor").style, { left: `${120 * z - 9}px`, top: `${280 * z - 9}px`, transition: "none" }), ZOOM);
        await page.mouse.move(120 * ZOOM, 280 * ZOOM);
        await page.mouse.down();
        for (let x = 120; x <= 600; x += 12) {
          await page.mouse.move(x * ZOOM, 280 * ZOOM);
          await page.evaluate((x) => { document.getElementById("demo-cursor").style.left = `${x - 9}px`; }, x * ZOOM);
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
    if (mitKlicks) {
      const log = {
        name,
        viewport: { width: W * ZOOM, height: H * ZOOM },
        durationMs: (endeMs ?? jetzt()) - trimBeforeMs,
        trimBeforeMs,
        offsetMs: 0,
        speed: 1,
        clicks: klicks,
      };
      writeFileSync(join(outDir, `${name}.clicks.json`), JSON.stringify(log, null, 2));
      console.log(`✔ ${name}.clicks.json`);
    }
  }
} finally {
  await browser.close();
  await client.close();
}
