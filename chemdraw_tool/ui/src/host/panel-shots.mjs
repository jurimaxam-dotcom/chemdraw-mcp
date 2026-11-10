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
// [Datei, Tool, Argumente, iframe-Breite]; 930 px ≈ Panelbreite in Claude Desktop (Stand 10.11.2026).
const CASES = [
  // Die zwei Panelbilder der Nutzerdoku (docs/images/panel-molecule.png, panel-peptide.png = helle Fassung).
  ["doku-molekuel", "generate_molecule", { name_or_smiles: "thalidomide" }, 700],
  ["doku-peptid", "generate_molecule", { name_or_smiles: "Ala-Trp-Lys-Ser-Gly" }, 700],
  ["boc-abgekuerzt", "generate_molecule", { name_or_smiles: BOC, abbreviate_groups: true }, 930],
  ["aspirin-abgekuerzt", "generate_molecule", { name_or_smiles: "aspirin", abbreviate_groups: true }, 930],
  ["porphyrin-abgekuerzt", "generate_reaction", { ...PORPHYRIN, abbreviate_groups: true }, 930],
  ["porphyrin", "generate_reaction", PORPHYRIN, 930],
  ["knallgas", "generate_reaction", { reactants: ["H2", "O2"], products: ["H2O"], coefficients: [2, 1, 2] }, 930],
  ["veresterung", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" }, 930],
  ["veresterung-510", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" }, 510],
  ["mechanismus-kette", "generate_mechanism", { reaction_type: "fischer_ester", substrates: ["CCCCCCCCCCCCCCCCCC(=O)O", "CCO"] }, 930],
  ["vergleich", "compare_molecules", { structures: [BOC, "O=C(c1ccccc1)CC1CCNCC1"] }, 930],
  ["batch-abgekuerzt", "batch_generate", { molecules: [BOC, "aspirin"], abbreviate_groups: true }, 930],
  ["scope-abgekuerzt", "generate_scope_table", { entries: [{ structure: BOC }, { structure: "O=C(c1ccccc1)CC1CCN(S(=O)(=O)c2ccc(C)cc2)CC1" }], abbreviate_groups: true }, 930],
];

const only = process.env.SHOTS_ONLY?.split(",");
const tools = (await client.listTools()).tools;
const browser = await chromium.launch();
try {
  for (const [file, name, input, width] of CASES) {
    if (only && !only.includes(file)) continue;
    const tool = tools.find((t) => t.name === name);
    const result = await client.callTool({ name, arguments: input });
    if (result.isError) { console.log(`✘ ${file}: ${JSON.stringify(result.content).slice(0, 300)}`); continue; }
    const html = (await client.readResource({ uri: tool._meta.ui.resourceUri })).contents[0].text;
    for (const colorScheme of ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width: width + 20, height: 1400 }, colorScheme });
      await page.setContent('<body style="margin:0;background:#888"></body>');
      await page.addScriptTag({ path: out });
      await page.exposeFunction("__callTool", (req) => client.callTool(req));
      await page.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result });
      const iframe = page.locator("iframe").last();
      await iframe.evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1380px"; }, width);
      const frame = page.frames().at(-1);
      await frame.locator("svg").first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(600);
      // Bild nur so hoch wie der Inhalt: Panelhöhe aus dem iframe-Dokument.
      const h = await frame.evaluate(() => Math.ceil(document.getElementById("root").getBoundingClientRect().bottom) + 16);
      await page.setViewportSize({ width: width + 20, height: Math.min(1400, h + 20) });
      await iframe.evaluate((el, hh) => { el.style.height = `${hh}px`; }, h);
      await iframe.screenshot({ path: join(dest, `${file}-${colorScheme}.png`) });
      console.log(`✔ ${file}-${colorScheme}.png (${width}×${h})`);
      await page.close();
    }
  }
} finally {
  await browser.close();
  await client.close();
}
