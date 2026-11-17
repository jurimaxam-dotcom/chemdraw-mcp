// Bildschau für Lesbarkeit: dieselben Panel-Fälle im hellen UND dunklen Schema,
// über denselben sandboxed Host wie host.e2e.mjs und den echten Server (Wegwerf-HOME,
// nichts landet in ~/ChemDraw-Output). Kein Test — Bilder zum Ansehen, vorher/nachher.
// usage: node src/host/panel-shots.mjs <ordner>   (Netz für PubChem-Namen)
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const dest = process.argv[2] || join(tmpdir(), "chemdraw-panel-shots");
mkdirSync(dest, { recursive: true });
const out = join(mkdtempSync(join(tmpdir(), "panel-shots-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });

const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const client = new Client({ name: "panel-shots", version: "0.0.0" });
const wegwerfHome = mkdtempSync(join(tmpdir(), "panel-shots-home-"));
// Volles Profil: Scope und Batch gehören mit in die Schau.
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "full" }, cwd: repo }));

const BOC = "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1";
const PORPHYRIN = {
  reactants: ["CC1=C(CCC(=O)O)C2=CC3=C(CCC(=O)O)C(C)=C(N3)C=C4C(C)=C(C=C)C(=N4)C=C5C(C=C)=C(C)C(=N5)C=C1N2", "[Fe+2]"], products: ["CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)O)C)CCC(=O)O.[Fe+2]", "[H+]"], coefficients: [1, 1, 1, 2],
  conditions: "ferrochelatase", name: "Protoporphyrin IX → heme b",
};
const KOFF = { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" };
const ANKI = { deck_name: "Koffein und Paracetamol", cards: [
  { front: { structure: "caffeine" }, back: { text: "<b>Koffein</b> (Caffeine)<br>Methylxanthin, Adenosin-Antagonist" } },
  { front: { structure: "paracetamol" }, back: { text: "<b>Paracetamol</b><br>Analgetikum, Antipyretikum" } },
  { front: { text: "Welche funktionelle Gruppe trägt Aspirin neben der Carbonsäure?" }, back: { text: "Einen Phenylester (Acetylester)", structure: "aspirin" } },
] };
const ANKI_VIELE = { deck_name: "Lösungsmittel", cards: ["methanol", "ethanol", "acetone", "toluene", "hexane", "benzene", "phenol", "pyridine", "acetonitrile", "chloroform"]
  .map((s) => ({ front: { text: `Formel von ${s}?` }, back: { text: s } })) };
const CASES = [];
const C = [
  ["c-3d", "generate_3d", KOFF],
  ["c-protein", "generate_protein_or_antibody", { name: "trastuzumab" }],
  ["c-protein-schema", "generate_protein_or_antibody", { name: "trastuzumab" }, "[role='tab']:has-text('Scheme')"],
  ["c-antikoerper", "generate_protein_or_antibody", { name: "antibody" }],
  ["c-lysozym", "generate_protein_or_antibody", { name: "lysozyme" }],
  ["c-anki", "export_anki_deck", ANKI],
  ["c-anki-viele", "export_anki_deck", ANKI_VIELE],
];
CASES.push(["c-protein-ohne-webgl-chat1000", "generate_protein_or_antibody", { name: "lysozyme" }, 1000, undefined, undefined, true]);
CASES.push(["c-3d-600x1000", "generate_3d", KOFF, 600, 1000]);
for (const [file, name, input, klick] of C) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-chat860`, name, input, 860, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
const fixedCtx = (width, height) => ({ displayMode: "fullscreen", availableDisplayModes: ["inline", "fullscreen"],
  platform: "desktop", containerDimensions: { width, height } });

function plotMetrics() {
  const r = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height), b: Math.round(b.bottom) }; };
  const panel = document.querySelector("#root article, .panel-root > *");
  const stage = document.querySelector(".m3d-stage, [data-protein-viewer]");
  const svg = document.querySelector(".m3d-stage svg[role='img']");
  let bowl = null;
  if (svg) { const vb = svg.viewBox.baseVal, b = svg.getBoundingClientRect(); const k = Math.min(b.width / vb.width, b.height / vb.height); bowl = Math.round(vb.width * k); }
  const facts = document.querySelector(".panel-facts, .key-facts");
  const foot = document.querySelector("[data-testid='panel-footer']");
  const st = r(stage);
  const ctrl = st ? new Set([...document.querySelectorAll("[role=tablist], .seg, .stage-bar button, .rotate-row")].map((e) => e.getBoundingClientRect()).filter((b) => b.height && b.bottom <= st.y + 1 && b.top > 0).map((b) => Math.round(b.top))).size : null;
  const lastBeforeFoot = foot ? Math.max(...[...foot.parentElement.children].filter((c) => c !== foot && c.getBoundingClientRect().height).map((c) => c.getBoundingClientRect().bottom)) : null;
  const m3d = document.querySelector(".m3d-panel");
  const bb = document.querySelector("svg[data-backbone]");
  return { m3dPanelH: m3d ? Math.round(m3d.getBoundingClientRect().height) : undefined, viewer: stage?.getAttribute("data-protein-viewer") ?? undefined,
    spur: bb ? r(bb) : undefined, warn: document.querySelector(".hint-warn")?.textContent, panelH: Math.round(document.getElementById("root").getBoundingClientRect().bottom), panelW: r(panel)?.w, stage: st, bowl, facts: r(facts), foot: r(foot),
    gapVorFuss: foot && lastBeforeFoot ? Math.round(foot.getBoundingClientRect().top - lastBeforeFoot) : null, steuerzeilen: ctrl,
    rollen: document.documentElement.scrollHeight > innerHeight + 1, quer: document.documentElement.scrollWidth > innerWidth };
}

const only = process.env.SHOTS_ONLY?.split(",");
const tools = (await client.listTools()).tools;
const browser = await chromium.launch();
try {
  for (const [file, name, input, width, fixed, klick, noGl] of CASES) {
    if (only && !only.includes(file)) continue;
    const tool = tools.find((t) => t.name === name);
    const result = await client.callTool({ name, arguments: input });
    if (result.isError) { console.log(`✘ ${file}: ${JSON.stringify(result.content).slice(0, 300)}`); continue; }
    const html = (await client.readResource({ uri: tool._meta.ui.resourceUri })).contents[0].text;
    for (const colorScheme of ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width: width + 20, height: 1400 }, colorScheme });
      if (noGl) await page.addInitScript(() => { const o = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (t, ...a) { return /webgl/i.test(t) ? null : o.call(this, t, ...a); }; });
      await page.setContent('<body style="margin:0;background:#888"></body>');
      await page.addScriptTag({ path: out });
      await page.exposeFunction("__callTool", (req) => client.callTool(req));
      const hostContext = fixed ? fixedCtx(width, fixed) : undefined;
      await page.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result, hostContext });
      const iframe = page.locator("iframe").last();
      if (!fixed) await iframe.evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1380px"; }, width);
      const frame = page.frames().at(-1);
      await frame.locator("article.panel, [data-anki-card], svg:visible").first().waitFor({ timeout: 30000 });
      if (name === "generate_protein_or_antibody") await frame.locator('[data-protein-viewer="ready"], [data-protein-viewer="failed"]').first().waitFor({ timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(600);
      // Optionaler Klick vor dem Bild (Detailansicht); fehlt das Element, bleibt die Startansicht.
      if (klick && await frame.locator(klick).count()) {
        await frame.locator(klick).first().click();
        await page.waitForTimeout(2500);
      }
      if (fixed) {
        const m = await frame.evaluate(plotMetrics);
        await page.setViewportSize({ width: width + 20, height: fixed + 20 });
        await iframe.screenshot({ path: join(dest, `${file}-${colorScheme}.png`) });
        console.log(`✔ ${file}-${colorScheme}.png (${width}×${fixed}) ${JSON.stringify(m)}`);
        await page.close();
        continue;
      }
      // Bild nur so hoch wie der Inhalt: Panelhöhe aus dem iframe-Dokument.
      const h = await frame.evaluate(() => Math.ceil(document.getElementById("root").getBoundingClientRect().bottom) + 16);
      await page.setViewportSize({ width: width + 20, height: Math.min(1400, h + 20) });
      await iframe.evaluate((el, hh) => { el.style.height = `${hh}px`; }, h);
      await iframe.screenshot({ path: join(dest, `${file}-${colorScheme}.png`) });
      const m = await frame.evaluate(plotMetrics);
      console.log(`✔ ${file}-${colorScheme}.png (${width}×${h})${m ? ` ${JSON.stringify(m)}` : ""}`);
      await page.close();
    }
  }
} finally {
  await browser.close();
  await client.close();
}
