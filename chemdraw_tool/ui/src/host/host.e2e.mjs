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
import { mkdtempSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const out = join(mkdtempSync(join(tmpdir(), "panel-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });

const client = new Client({ name: "panel-e2e", version: "0.0.0" });
// HOME zeigt auf einen Wegwerf-Ordner: der Server schreibt seine Dateien nach ~/ChemDraw-Output,
// und der Test soll den echten Ordner des Nutzers nicht füllen. Dafür direkt die venv-Binärdatei (uv bräuchte das echte HOME).
const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const wegwerfHome = mkdtempSync(join(tmpdir(), "panel-home-"));
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "mvp" }, cwd: repo }));
let browser;
try {
  const tools = (await client.listTools()).tools;
  browser = await chromium.launch();
  // Welle 1: echte Galerie-Antworten über denselben sandboxed Host wie Desktop.
  const check = (ok, message) => { if (!ok) throw new Error("ROT: " + message); console.log("✔", message); };
  const mount = async (p, name, input) => {
    const tool = tools.find((t) => t.name === name);
    check(tool?._meta?.ui?.resourceUri, `${name} ist als Panel-Tool registriert`);
    const result = await client.callTool({ name, arguments: input });
    check(!result.isError, `${name} liefert eine erfolgreiche echte Serverantwort`);
    const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
    await p.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: input, toolResult: result });
    const iframe = p.locator("iframe").last();
    await iframe.evaluate((el) => { el.style.width = "510px"; el.style.height = "560px"; });
    return p.frames().at(-1);
  };
  const gallery = await browser.newPage({ viewport: { width: 1530, height: 560 } });
  await gallery.setContent('<body style="margin:0;display:flex"></body>');
  await gallery.addScriptTag({ path: out });
  await gallery.exposeFunction("__callTool", (req) => client.callTool(req));
  for (const [type, substrates, example, count] of [
    ["sn1", ["CC(C)Br", "O"], "2-bromopropane + water", 5],
    ["sn2", ["CBr", "[OH-]"], "bromomethane + hydroxide", 3],
    ["fischer_ester", ["CC(=O)O", "CO"], "acetic acid + methanol", 6],
  ]) {
    const f = await mount(gallery, "generate_mechanism", { reaction_type: type, substrates });
    await f.getByRole("button", { name: "Overview", exact: true }).waitFor();
    const body = await f.locator("body").innerText();
    check(body.includes("textbook example") && body.includes(example), `${type}: sichtbarer Titel nennt das gezeichnete Lehrbuchbeispiel`);
    // Pfeile und Struktur kommen aus echten Renderer-SVGs, nicht aus einem Text-Platzhalter.
    check(await f.locator('svg path').count() > 0 && body.includes("Reactants"), `${type}: Übersicht enthält gezeichnete Strukturen und Schritte`);
    await f.getByRole("button", { name: "Step by step", exact: true }).click();
    await f.getByText(`Step 1 / ${count}`, { exact: true }).waitFor();
    check(await f.getByRole("button", { name: "← Back", exact: true }).isDisabled(), `${type}: erster Schritt sperrt Zurück`);
    const first = await f.locator(".mech-step-svg").innerHTML();
    await f.getByRole("button", { name: "Next →", exact: true }).click();
    await f.getByText(`Step 2 / ${count}`, { exact: true }).waitFor();
    check(await f.locator(".mech-step-svg").innerHTML() !== first, `${type}: Weiter zeigt eine andere Zeichnung`);

  }
  await gallery.waitForTimeout(200); // Übergänge der Schrittanzeige vor dem Bild abschließen.
  await gallery.screenshot({ path: join(tmpdir(), "panel-host-wave1-mechanisms.png") });
  await gallery.close();

  const spatial = await browser.newPage({ viewport: { width: 530, height: 560 } });
  await spatial.setContent('<body style="margin:0"></body>');
  await spatial.addScriptTag({ path: out });
  await spatial.exposeFunction("__callTool", (req) => client.callTool(req));
  const spatialFrame = await mount(spatial, "generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" });
  await spatialFrame.getByText("Caffeine", { exact: true }).waitFor();
  const canvas = spatialFrame.locator('svg[viewBox="0 0 480 480"]');
  await canvas.waitFor({ state: "visible" });
  check(await canvas.locator('circle[fill^="url(#atom-"]').count() === 24 && await canvas.locator("line").count() > 20,
    "3D: sichtbare SVG-Zeichenfläche enthält Caffeins 24 Atome und Bindungen");
  check((await spatialFrame.locator("body").innerText()).includes("drag to rotate"), "3D: Bedienhinweis sichtbar");
  const geometry = () => canvas.locator('circle[fill^="url(#atom-"]').evaluateAll((atoms) => atoms.map((a) => [a.getAttribute("cx"), a.getAttribute("cy")]));
  await spatial.screenshot({ path: join(tmpdir(), "panel-host-wave1-3d.png") });
  const before = JSON.stringify(await geometry());
  const box = await canvas.boundingBox();
  await spatial.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await spatial.mouse.down();
  await spatial.mouse.move(box.x + box.width / 2 + 85, box.y + box.height / 2 + 45, { steps: 8 });
  await spatial.mouse.up();
  check(JSON.stringify(await geometry()) !== before, "3D: Ziehen ändert die projizierten Atomkoordinaten");
  await spatial.close();

  // Welle 2: reale Spektren im sandboxed Panel, einschließlich Dateiausgabe.
  for (const [spectrum_type, title, peaks, axis] of [
    ["ir", "Aspirin IR", [
      { position: 1750, intensity: 1, label: "Ester C=O" },
      { position: 1690, intensity: 1, label: "Acid C=O" },
    ], "Wavenumber"],
    ["ms", "Mass spectrum", [
      { position: 180, intensity: 20, label: "M+" },
      { position: 120, intensity: 100, label: "Base peak" },
      { position: 138, intensity: 60, label: "Fragment" },
    ], "m/z"],
    ["nmr_1h", "Ethyl acetate 1H NMR", [
      { position: 1.25, intensity: 3, label: "CH3 triplet" },
      { position: 2.05, intensity: 3, label: "Acetyl singlet" },
      { position: 4.12, intensity: 2, label: "CH2 quartet" },
    ], "ppm"],
  ]) {
    const p = await browser.newPage({ viewport: { width: 530, height: 560 } });
    await p.setContent('<body style="margin:0"></body>');
    await p.addScriptTag({ path: out });
    const calls = [];
    await p.exposeFunction("__callTool", (req) => { calls.push(req); return client.callTool(req); });
    const f = await mount(p, "generate_spectrum", { spectrum_type, title, peaks });
    await f.locator(".spectrum-svg svg").waitFor();
    const labels = await f.locator(".spectrum-svg svg text").allTextContents();
    check(labels.some((t) => t.includes(axis)) && peaks.every((peak) => labels.includes(peak.label)),
      `${spectrum_type}: echte SVG mit Achseneinheit und allen Peakbeschriftungen`);
    if (spectrum_type !== "ms") {
      const [left, right] = spectrum_type === "ir" ? ["4000", "500"] : ["12", "0"];
      const tickX = async (label) => f.locator(".spectrum-svg svg text").filter({ hasText: new RegExp(`^${label}$`) }).first()
        .evaluate((el) => el.getBoundingClientRect().x);
      check(await tickX(left) < await tickX(right), `${spectrum_type}: Achse fällt von links nach rechts`);
    }
    if (spectrum_type === "ms") {
      const bars = await f.locator('.spectrum-svg g[id^="LineCollection"] path').evaluateAll((paths) => paths.map((path) => {
        const n = path.getAttribute("d").match(/-?[\d.]+/g).map(Number);
        return { x: n[0], height: Math.abs(n[3] - n[1]) };
      }));
      bars.sort((a, b) => a.x - b.x);
      check(bars.length === 3 && Math.abs(bars[1].height / bars[0].height - 0.6) < 0.001 &&
        Math.abs(bars[2].height / bars[0].height - 0.2) < 0.001,
        "MS: drei echte Balken; 120 ist Basispeak, 138 = 60 %, 180 = 20 %");
    }
    const png = f.locator('span[title$=".png"]');
    const path = await png.getAttribute("title");
    check(path.startsWith(join(wegwerfHome, "ChemDraw-Output", "spektren") + "/") &&
      readFileSync(path).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])),
      `${spectrum_type}: sichtbarer PNG-Pfad verweist auf echte PNG-Datei in spektren/`);
    await p.screenshot({ path: join(tmpdir(), `panel-host-wave2-${spectrum_type}.png`) });
    const exportButton = f.getByRole("button", { name: "Export as PNG" });
    check(await exportButton.count() === 1, `${spectrum_type}: PNG-Exportknopf sichtbar`);
    await exportButton.click();
    await f.getByRole("button", { name: /Saved:|Copied as image/ }).waitFor();
    check(calls.filter((r) => r.name === "save_png").length === 1,
      `${spectrum_type}: sandboxed Export ruft save_png genau einmal über die Bridge`);
    const savedTitle = await f.getByRole("button", { name: /Saved:/ }).getAttribute("title");
    const savedPath = savedTitle.replace(/^Saved: /, "");
    check(savedPath.startsWith(join(wegwerfHome, "ChemDraw-Output", "png") + "/") &&
      readFileSync(savedPath).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])),
      `${spectrum_type}: Export-Rückfall schreibt echte PNG-Datei in png/`);
    await p.close();
  }

  // Welle 2: drei DC-Eingaben, echte SVG-Geometrie und Export über die Bridge.
  for (const [title, solvent, lanes] of [
    ["Esterification TLC", "", [
      { name: "Starting material", spots: [{ rf: 0.3 }] },
      { name: "Product", spots: [{ rf: 0.65 }] },
      { name: "Co-spot", spots: [{ rf: 0.3 }, { rf: 0.65 }] },
    ]],
    ["Three lanes", "Hexane/ethyl acetate 7:3", [
      { name: "A", spots: [{ rf: 0.2 }] },
      { name: "B", spots: [{ rf: 0.45 }] },
      { name: "C", spots: [{ rf: 0.8 }] },
    ]],
    ["Distance ratios", "Ethyl acetate", [
      { name: "A", spots: [{ rf: 2.1 / 6 }] },
      { name: "B", spots: [{ rf: 4.2 / 6 }] },
    ]],
  ]) {
    const p = await browser.newPage({ viewport: { width: 530, height: 580 } });
    await p.setContent('<body style="margin:0"></body>');
    await p.addScriptTag({ path: out });
    const calls = [];
    await p.exposeFunction("__callTool", (req) => { calls.push(req); return client.callTool(req); });
    const f = await mount(p, "generate_tlc", { title, solvent, lanes });
    await f.locator(".tlc-svg svg").waitFor();
    const labels = await f.locator(".tlc-svg svg text").allTextContents();
    check(lanes.every((lane) => labels.includes(lane.name)), `${title}: jede Bahn in echter SVG beschriftet`);
    const rfs = lanes.flatMap((lane) => lane.spots.map((spot) => spot.rf.toFixed(2)));
    check(rfs.every((rf) => labels.some((label) => label.includes(rf))), `${title}: Rf-Werte an der Zeichnung sichtbar`);
    // Ellipsen enthalten kubische Kurven; Hintergrund, Platte und Pfeil nicht.
    const spots = await f.locator('.tlc-svg g[id^="patch_"] path').evaluateAll((paths) => paths
      .filter((path) => /C/.test(path.getAttribute("d")))
      .map((path) => { const b = path.getBBox(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }));
    check(spots.length === rfs.length, `${title}: ${rfs.length} echte Flecken statt Text-Platzhalter`);
    const xs = [...new Set(spots.map((spot) => spot.x.toFixed(2)))].sort((a, b) => Number(a) - Number(b));
    check(xs.length === lanes.length && lanes.every((lane, i) =>
      spots.filter((spot) => spot.x.toFixed(2) === xs[i]).length === lane.spots.length),
      `${title}: Flecken sind den richtigen Bahnen zugeordnet, einschließlich Co-Spot`);
    if (solvent) check(labels.some((label) => label.includes(solvent)), `${title}: Laufmittel steht auch in der exportierten SVG`);
    const path = await f.locator('span[title$=".png"]').getAttribute("title");
    check(path.startsWith(join(wegwerfHome, "ChemDraw-Output", "dc-platten") + "/") && existsSync(path),
      `${title}: echte PNG-Datei in dc-platten/`);
    const exportButton = f.getByRole("button", { name: "Export as PNG" });
    await exportButton.click();
    await f.getByRole("button", { name: /Saved:/ }).waitFor();
    check(calls.filter((req) => req.name === "save_png").length === 1, `${title}: Export über save_png-Bridge`);
    const savedPath = (await f.getByRole("button", { name: /Saved:/ }).getAttribute("title")).replace(/^Saved: /, "");
    check(readFileSync(savedPath).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])), `${title}: Exportdatei hat PNG-Magic-Bytes`);
    await p.screenshot({ path: join(tmpdir(), `panel-host-wave2-tlc-${lanes.length}-${rfs.length}.png`) });
    await p.close();
  }

  const gm = tools.find((t) => t.name === "generate_molecule");
    const toolInput = { name_or_smiles: "methylphenidate" };
  const toolResult = await client.callTool({ name: "generate_molecule", arguments: toolInput });
  if (toolResult.isError) throw new Error("generate_molecule: " + JSON.stringify(toolResult.content).slice(0, 300));
  const res = await client.readResource({ uri: gm._meta.ui.resourceUri });
  const html = res.contents[0].text;
  console.log("resource bytes:", html.length, "| result keys:", Object.keys(toolResult));

  const page = await browser.newPage({ viewport: { width: 700, height: 700 } });
  const serverCalls = [];
  const ankiCalls = [];
  await page.exposeFunction("__callTool", (p) => {
    serverCalls.push(p.name);
    if (p.name === "export_anki_deck") {
      ankiCalls.push(p.arguments);
      // Im Test nie Anki starten: der Knopf schickt "open", der Server bekommt "apkg".
      p = { ...p, arguments: { ...p.arguments, deliver: "apkg" } };
    }
    return client.callTool(p);
  });
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

  // 3b. Add to Anki: Panel → Host → echter Server schreibt genau eine Karte ins Deck „ChemDraw"
  await frame.locator("button.add-to-anki").click();
  await frame.locator("button.add-to-anki", { hasText: "Saved" }).waitFor({ timeout: 30000 });
  const anki = ankiCalls[0] ?? {};
  prüfe(ankiCalls.length === 1 && anki.deliver === "open" && anki.deck_name === "ChemDraw",
    "Anki-Knopf löst genau einen export_anki_deck (deliver=open, Deck ChemDraw) aus");
  prüfe(anki.cards?.length === 1 && anki.cards[0].front.structure && /Methylphenidate/i.test(anki.cards[0].back.text),
    "Eine Karte: Struktur per SMILES vorn, Name hinten");
  const apkg = join(wegwerfHome, "ChemDraw-Output", "anki", "chemdraw.apkg");
  prüfe(existsSync(apkg), `Server hat ${apkg} geschrieben`);

  // 3c. Show variants (Etappe 3): Panel → echter Server zählt die Stereoisomere auf,
  // ein Klick zeichnet eines davon mit Keilen
  await frame.getByText("Structure", { exact: true }).click();
  await frame.getByRole("button", { name: "Show variants" }).click();
  await frame.locator("button.candidate").first().waitFor({ timeout: 30000 });
  const labels = await frame.locator("button.candidate .candidate-label").allInnerTexts();
  prüfe(labels.length === 4 && labels.every((l) => /^\([RS],[RS]\)-methylphenidate$/i.test(l)),
    `Show variants zeigt 4 Stereoisomere: ${labels.join(" · ")}`);
  await page.screenshot({ path: join(tmpdir(), "panel-host-variants.png") });
  await frame.locator("button.candidate").first().click();
  await frame.getByRole("button", { name: "All candidates" }).waitFor({ timeout: 30000 });
  const drawnTitle = await frame.locator(".panel-title").first().innerText();
  prüfe(drawnTitle === labels[0] && !(await frame.locator("[data-testid='stereo-note']").count()),
    `Klick zeichnet ${drawnTitle} — ohne offenen Stereo-Hinweis`);
  await frame.getByRole("button", { name: "All candidates" }).click();
  await frame.getByRole("button", { name: "Back to the structure" }).click();
  prüfe((await text()).includes("CID 4158"), "Zurück zeigt wieder Methylphenidate");

  // 3d. Zusatzansichten erst auf Klick (Jay 26.10.): Antwort schlank, All H kommt per Bridge in < 1 s
  // Gezählt wird der Text, den das Modell liest (Desktop verwirft structuredContent).
  const antwortKB = toolResult.content.map((c) => c.text || "").join("").length / 1024;
  prüfe(antwortKB < 15, `Modell liest ${antwortKB.toFixed(1)} KB statt vorher 29,4 KB`);
  const vorher = serverCalls.length;
  const tAllH = Date.now();
  await frame.getByRole("button", { name: "All H" }).click();
  await frame.locator('button[aria-pressed="true"]', { hasText: "All H" }).waitFor({ timeout: 5000 });
  const msAllH = Date.now() - tAllH;
  prüfe(serverCalls.slice(vorher).join() === "generate_molecule" && msAllH < 1000, `All H holt die Zeichnung per Klick in ${msAllH} ms`);
  await frame.getByRole("button", { name: "All H" }).click();
  await frame.getByRole("button", { name: "All H" }).click();
  prüfe(serverCalls.length === vorher + 1, "Zweiter All-H-Klick kommt aus dem Cache");
  await frame.getByRole("button", { name: "All H" }).click();

  // 3e. Fischer/Haworth (Etappe 4): Knopf nur bei passenden Stoffen, Zeichnung per Klick
  prüfe(!(await frame.getByRole("button", { name: "Fischer" }).count()) && !(await frame.getByRole("button", { name: "Haworth" }).count()),
    "Methylphenidate hat keinen Projektionsknopf");
  for (const [stoff, knopf, fehlt, soll] of [["D-glucose", "Fischer", "Haworth", "CHO"], ["beta-D-glucose", "Haworth", "Fischer", "CH2OH"]]) {
    const input = { name_or_smiles: stoff };
    const result = await client.callTool({ name: "generate_molecule", arguments: input });
    if (result.isError) throw new Error(`generate_molecule ${stoff}: ` + JSON.stringify(result.content).slice(0, 300));
    const p = await browser.newPage({ viewport: { width: 700, height: 700 } });
    await p.exposeFunction("__callTool", (req) => client.callTool(req));
    await p.setContent("<body></body>");
    await p.addScriptTag({ path: out });
    await p.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result });
    await p.locator("iframe").evaluate((el) => { el.style.width = "680px"; el.style.height = "660px"; });
    const f = p.frames().find((x) => x !== p.mainFrame());
    await f.getByRole("button", { name: knopf }).click();
    await f.locator(".structure-drawing svg text").first().waitFor({ timeout: 5000 });
    const labels = await f.locator(".structure-drawing svg text").allTextContents();
    prüfe(labels.includes(soll) && !(await f.getByRole("button", { name: fehlt }).count()),
      `${stoff}: ${knopf} zeigt ${labels.length} Beschriftungen (${soll} dabei), kein ${fehlt}-Knopf`);
    if (knopf === "Haworth") prüfe((await f.locator("body").innerText()).includes("open-chain"), `${stoff}: Hinweis zur offenen Form`);
    await p.emulateMedia({ colorScheme: "dark" });
    const fill = await f.evaluate(() => getComputedStyle(document.querySelector(".structure-drawing svg text")).fill);
    prüfe(fill !== "rgb(0, 0, 0)", `${stoff}: Beschriftung im Dunkelmodus hell (${fill})`);
    await p.screenshot({ path: join(tmpdir(), `panel-host-${knopf.toLowerCase()}.png`) });
    await p.close();
  }

  // 3f. Modell setzt view selbst (Befund Desktop 26.10.): Panel startet auf Haworth, mit Titel, Knöpfen, Hinweis
  {
    const input = { name_or_smiles: "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O", label: "β-D-Glucopyranose", view: "haworth" };
    const result = await client.callTool({ name: "generate_molecule", arguments: input });
    const p = await browser.newPage({ viewport: { width: 700, height: 700 } });
    await p.exposeFunction("__callTool", (req) => client.callTool(req));
    await p.setContent("<body></body>");
    await p.addScriptTag({ path: out });
    await p.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result });
    await p.locator("iframe").evaluate((el) => { el.style.width = "680px"; el.style.height = "660px"; });
    const f = p.frames().find((x) => x !== p.mainFrame());
    await f.locator('button[aria-pressed="true"]', { hasText: "Haworth" }).waitFor({ timeout: 10000 });
    const body = await f.locator("body").innerText();
    prüfe(body.includes("β-D-Glucopyranose") && body.includes("open-chain") && await f.getByRole("button", { name: "All H" }).count() === 1,
      "view=haworth vom Modell: Panel startet auf Haworth, mit Titel, All-H-Knopf und Hinweis");
    await p.screenshot({ path: join(tmpdir(), "panel-host-model-view.png") });
    await p.close();
  }

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
