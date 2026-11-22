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
// Paket B (Umbau 17.11.2026): unversionierte Kopie von panel-shots.mjs, nur die Grafik-Fälle.
const CASES = [];
const SN2 = { reaction_type: "sn2", substrates: ["C[C@@H](Br)CC", "[C-]#N"] };
const B = [
  ["b-spektrum-ir", "generate_spectrum", { spectrum_type: "ir", title: "Aspirin IR", peaks: [
    { position: 1750, intensity: 1, label: "Ester-C=O" }, { position: 1690, intensity: 1, label: "Säure-C=O" }] }],
  ["b-spektrum-nmr", "generate_spectrum", { spectrum_type: "nmr_1h", title: "Toluene 1H NMR", peaks: [
    { position: 7.2, intensity: 5, label: "ArH" }, { position: 2.35, intensity: 3, label: "CH3" }] }],
  ["b-titration", "generate_titration_curve", { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1, v_acid_ml: 25, c_titrant: 0.1,
    indicator: { name: "Phenolphthalein", ph_range: [8.2, 10.0] } }],
  ["b-spezies", "generate_species_distribution", { substance: "Phosphoric acid", pka_values: [2.15, 7.2, 12.35] }],
  ["b-pk", "generate_pk_curve", { dose_mg: 500, vd_l: 40, half_life_h: 6, ka_per_h: 1.2, bioavailability: 0.8, tau_h: 8,
    mec_mg_per_l: 5, mtc_mg_per_l: 20, drug: "Beispiel" }],
  ["b-kalibrierung", "generate_calibration_curve", { concentrations: [0, 2, 4, 6, 8, 10], signals: [0.01, 0.21, 0.40, 0.62, 0.80, 1.01],
    unknown_signals: [0.47, 0.55], substance: "Paracetamol", x_label: "c [mg/L]", y_label: "A" }],
  ["b-dc", "generate_tlc", { title: "DC-Platte", lanes: [
    { name: "Edukt", spots: [{ rf: 0.3, label: "Edukt" }] }, { name: "Produkt", spots: [{ rf: 0.65, label: "Produkt" }] }] }],
  ["b-vergleich", "compare_molecules", { structures: ["CC(C)Cc1ccc(cc1)C(C)C(=O)O", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O"], labels: ["Ibuprofen", "Naproxen"] }],
  ["b-reaktion-bilanziert", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" }],
  ["b-reaktion-unbilanziert", "generate_reaction", { reactants: ["[H][H]", "O=O"], products: ["O"], name: "Oxyhydrogen" }],
  ["b-mech-uebersicht", "generate_mechanism", SN2],
  ["b-mech-schritt", "generate_mechanism", SN2, "[aria-label^='Open view 2']"],
  ["b-scope", "generate_scope_table", { entries: [{ structure: "CC(=O)c1ccccc1" }, { structure: "CC(=O)c1ccc(Cl)cc1" }, { structure: "CC(=O)c1ccc(OC)cc1" }, { structure: "CC(=O)c1ccc(F)cc1" }] }],
];
// Gegenproben zu host.e2e: U5 (Vollbild 1400×900, Figur > 600 px) und E5 Fischer (acht Schritte im Chat).
CASES.push(["b-u5-titration-1400x900", "generate_titration_curve", { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1, v_acid_ml: 25, c_titrant: 0.1 }, 1400, 900]);
CASES.push(["b-u5-vergleich3-1400x900", "compare_molecules", { structures: ["ibuprofen", "naproxen", "ketoprofen"] }, 1400, 900]);
CASES.push(["b-mech-fischer-chat1000", "generate_mechanism", { reaction_type: "fischer_ester", substrates: ["CCCCCCCCCCCCCCCCCC(=O)O", "CCO"] }, 1000]);
for (const [file, name, input, klick] of B) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
const fixedCtx = (width, height) => ({ displayMode: "fullscreen", availableDisplayModes: ["inline", "fullscreen"],
  platform: "desktop", containerDimensions: { width, height } });

// Maße der Diagrammfläche: Karte, gezeichnete Figur (viewBox, „meet“), Rollen ja/nein.
function plotMetrics() {
  const nav = [...document.querySelectorAll(".mech-nav .btn")].map((b) => { const r = b.getBoundingClientRect(); return `${b.textContent}:${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.left)}`; });
  const st = document.querySelector(".stage"); const sr = st?.getBoundingClientRect();
  const extra = { nav: nav.join(" "), stage: sr ? `${Math.round(sr.width)}x${Math.round(sr.height)}` : "", sw: document.documentElement.scrollWidth };
  const card = document.querySelector(".plot-svg, .spectrum-svg, .tlc-svg");
  const svg = card?.querySelector("svg");
  if (!svg) return { ...extra, rollen: document.documentElement.scrollHeight > innerHeight + 1, hoehe: document.documentElement.scrollHeight };
  const c = card.getBoundingClientRect(), r = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  const k = vb && vb.width ? Math.min(r.width / vb.width, r.height / vb.height) : 1;
  return { ...extra, karte: `${Math.round(c.width)}×${Math.round(c.height)}`, figur: `${Math.round(vb.width * k)}×${Math.round(vb.height * k)}`,
    massstab: +k.toFixed(2), rollen: document.documentElement.scrollHeight > innerHeight + 1,
    hintergrund: getComputedStyle(card).backgroundColor };
}

const only = process.env.SHOTS_ONLY?.split(",");
const tools = (await client.listTools()).tools;
const browser = await chromium.launch();
try {
  for (const [file, name, input, width, fixed, klick] of CASES) {
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
      const hostContext = fixed ? fixedCtx(width, fixed) : undefined;
      await page.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result, hostContext });
      const iframe = page.locator("iframe").last();
      if (!fixed) await iframe.evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1380px"; }, width);
      const frame = page.frames().at(-1);
      await frame.locator("svg").first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(600);
      // Optionaler Klick vor dem Bild (Detailansicht); fehlt das Element, bleibt die Startansicht.
      if (klick && await frame.locator(klick).count()) {
        await frame.locator(klick).first().click();
        await page.waitForTimeout(1500);
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
