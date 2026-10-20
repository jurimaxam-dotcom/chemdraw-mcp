// Panel-Test gegen einen nachgebauten Host (AppBridge) und den ECHTEN MCP-Server.
// Deckt, was in-process-Tests nicht sehen: das sandboxed iframe, den Nachrichtenweg
// Panel → Host → Server (callServerTool) und die Tool-Antwort, die das Panel wirklich füllt.
// usage: node src/host/host.e2e.mjs      (Netz nötig für den Data-Knopf: PubChem)
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const out = join(mkdtempSync(join(tmpdir(), "panel-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });

const client = new Client({ name: "panel-e2e", version: "0.0.0" });
// HOME zeigt auf einen Wegwerf-Ordner: der Server schreibt seine Dateien nach ~/ChemDraw-Output,
// und der Test soll Jays echten Ordner nicht füllen. Dafür direkt die venv-Binärdatei (uv bräuchte das echte HOME).
const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const wegwerfHome = mkdtempSync(join(tmpdir(), "panel-home-"));
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome }, cwd: repo }));
let browser;
try {
  const tools = (await client.listTools()).tools;
  const gm = tools.find((t) => t.name === "generate_molecule");
    const toolInput = { name_or_smiles: "methylphenidate" };
  const toolResult = await client.callTool({ name: "generate_molecule", arguments: toolInput });
  if (toolResult.isError) throw new Error("generate_molecule: " + JSON.stringify(toolResult.content).slice(0, 300));
  const res = await client.readResource({ uri: gm._meta.ui.resourceUri });
  const html = res.contents[0].text;
  console.log("resource bytes:", html.length, "| result keys:", Object.keys(toolResult));

  browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 700, height: 700 } });
  const serverCalls = [];
  await page.exposeFunction("__callTool", (p) => { serverCalls.push(p.name); return client.callTool(p); });
  await page.setContent("<body></body>");
  await page.addScriptTag({ path: out });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput, toolResult });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: join(tmpdir(), "panel-host.png") });
  const frame = page.frames().find((f) => f !== page.mainFrame());
  const text = async () => (await frame.locator("body").innerText()).replace(/\s+/g, " ");
  const prüfe = (ok, was) => { if (!ok) throw new Error("ROT: " + was); console.log("✔", was); };

  // 1. Strukturansicht: Panel hat das echte Tool-Ergebnis angenommen
  let t = await text();
  prüfe(t.includes("Methylphenidate") && t.includes("CID 4158"), "Panel zeigt Methylphenidate (CID 4158) im sandboxed iframe");
  prüfe(!serverCalls.includes("lookup_molecule_data"), "Strukturansicht ruft den Server noch nicht (lokal, kein Spinner)");

  // Reale Geometrie statt CSS-Snapshot: schmal/breit, hell/dunkel.
  for (const colorScheme of ["light", "dark"]) {
    await page.emulateMedia({ colorScheme });
    for (const width of [360, 980]) {
      await page.setViewportSize({ width, height: 900 });
      await page.locator("iframe").evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "820px"; }, width - 16);
      await frame.getByRole("button", { name: "Export as PNG" }).waitFor();
      const geometry = await frame.evaluate(() => {
        const panel = document.querySelector('[data-view="structure"]');
        const canvas = panel.querySelector(".structure-canvas").getBoundingClientRect();
        const info = panel.querySelector(".key-facts").getBoundingClientRect();
        const title = document.querySelector(".panel-title");
        return { overflow: document.documentElement.scrollWidth > innerWidth, canvas: canvas.toJSON(), info: info.toJSON(),
          titleSize: title ? parseFloat(getComputedStyle(title).fontSize) : 0,
          exportLabel: document.querySelector('[title="Export as PNG"]').textContent };
      });
      prüfe(!geometry.overflow && geometry.titleSize >= 15 && geometry.exportLabel.includes("PNG"), `${colorScheme} ${width}px: readable title, explicit export, no horizontal overflow`);
      if (width === 360) prüfe(geometry.info.top >= geometry.canvas.bottom - 1, "Schmale Ansicht stapelt Struktur und Steckbrief");
      else prüfe(geometry.info.left >= geometry.canvas.right - 1, "Breite Ansicht ordnet Steckbrief neben Struktur an");
      await page.screenshot({ path: join(tmpdir(), `chem-ui-${colorScheme}-${width}.png`) });
      // Hover auf die erste Gruppe: Bindungen leuchten, darunter stehen Name und Kurzformel.
      await frame.locator("button.functional-group").first().hover();
      await page.waitForTimeout(250); // Ueberblendung der Toenung (160 ms) abwarten, sonst zeigt das Foto Grau
      const glow = await frame.evaluate(() => ({
        lines: document.querySelectorAll(".group-glow line, .group-glow circle").length,
        note: document.querySelector(".group-note.is-active")?.textContent ?? "",
      }));
      prüfe(glow.lines > 0 && glow.note.length > 0, `${colorScheme} ${width}px: Gruppen-Hover leuchtet und nennt die Gruppe`);
      await page.screenshot({ path: join(tmpdir(), `chem-ui-${colorScheme}-${width}-hover.png`) });
      await frame.locator(".panel-title").hover();
    }
  }

  // 2. Data-Knopf: callServerTool → Host → echter Server → Datenblatt
  await frame.getByText("Data", { exact: true }).click();
  const t0 = Date.now();
  // „IUPAC name" und „CAS No." gibt es nur im Datenblatt — die Strukturansicht hat schon „CAS 113-45-1"
  await frame.getByText("IUPAC name").first().waitFor({ timeout: 30000 });
  console.log(`Datenblatt nach ${Date.now() - t0} ms`);
  t = await text();
  prüfe(serverCalls.filter((n) => n === "lookup_molecule_data").length === 1, "Data-Knopf löst genau einen lookup_molecule_data über die Bridge aus");
  prüfe(t.includes("CAS No. 113-45-1") && t.includes("PubChem CID 4158"), "Datenblatt (nicht Strukturansicht) zeigt CAS No. 113-45-1 und PubChem CID 4158");
  await page.screenshot({ path: join(tmpdir(), "panel-host-data.png") });

  for (const colorScheme of ["light", "dark"]) {
    await page.emulateMedia({ colorScheme });
    for (const width of [360, 980]) {
      await page.setViewportSize({ width, height: 1100 });
      await page.locator("iframe").evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1040px"; }, width - 16);
      prüfe(await frame.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${colorScheme} ${width}px: Datenblatt ohne horizontales Abschneiden`);
      await page.screenshot({ path: join(tmpdir(), `chem-ui-data-${colorScheme}-${width}.png`) });
    }
  }
  // Der Host darf ein anderes Theme als das Betriebssystem setzen.
  await page.emulateMedia({ colorScheme: "light" });
  await frame.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  prüfe(await frame.evaluate(() => getComputedStyle(document.body).backgroundColor === "rgb(32, 39, 36)"), "Explizites Host-Dunkeltheme überstimmt helles Systemtheme");
  await page.emulateMedia({ colorScheme: "dark" });
  await frame.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
  prüfe(await frame.evaluate(() => getComputedStyle(document.body).backgroundColor === "rgb(250, 251, 249)"), "Explizites Host-Helltheme überstimmt dunkles Systemtheme");
  await frame.evaluate(() => document.documentElement.removeAttribute("data-theme"));

  // 3. Zurück zur Struktur, wieder Data: Cache, kein zweiter Serveraufruf
  await frame.getByText("Structure", { exact: true }).click();
  await frame.getByText("Data", { exact: true }).click();
  await page.waitForTimeout(300);
  prüfe(serverCalls.filter((n) => n === "lookup_molecule_data").length === 1, "Zweiter Wechsel kommt aus dem Cache");

  // 4. Spalten-Ansicht (Vergleich → PlotView): Die Überschrift darf nicht in die Höhe wachsen,
  // sonst schrumpft das Bild auf einen Streifen (Regression aus adccc04, gefunden per Demo-Aufnahme)
  const cmpInput = { structures: ["ibuprofen", "naproxen", "ketoprofen"] };
  const cmpResult = await client.callTool({ name: "compare_molecules", arguments: cmpInput });
  const cmpUri = tools.find((x) => x.name === "compare_molecules")._meta.ui.resourceUri;
  const cmpHtml = (await client.readResource({ uri: cmpUri })).contents[0].text;
  const cmpPage = await browser.newPage({ viewport: { width: 720, height: 600 } });
  await cmpPage.setContent("<body></body>");
  await cmpPage.addScriptTag({ path: out });
  await cmpPage.evaluate((a) => window.__startHost(a), { html: cmpHtml, toolInput: cmpInput, toolResult: cmpResult });
  await cmpPage.locator("iframe").evaluate((el) => { el.style.width = "700px"; el.style.height = "560px"; });
  const cmpFrame = cmpPage.frames().find((f) => f !== cmpPage.mainFrame());
  await cmpFrame.locator(".plot-svg svg").waitFor();
  const cmp = await cmpFrame.evaluate(() => ({
    heading: document.querySelector(".panel-heading").getBoundingClientRect().height,
    box: document.querySelector(".plot-svg").getBoundingClientRect().width,
    svg: document.querySelector(".plot-svg svg").getBoundingClientRect().width,
  }));
  prüfe(cmp.heading < 100 && cmp.svg >= 0.8 * cmp.box, `Vergleich: Überschrift ${Math.round(cmp.heading)} px, Bild ${Math.round(cmp.svg)} von ${Math.round(cmp.box)} px breit`);
} finally {
  await browser?.close();
  await client.close();
}
