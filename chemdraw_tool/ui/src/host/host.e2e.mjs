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
import { mkdtempSync, mkdirSync, existsSync, readFileSync } from "node:fs";
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
  const mount = async (p, name, input, prelude = "", patch = null) => {
    const tool = tools.find((t) => t.name === name);
    check(tool?._meta?.ui?.resourceUri, `${name} ist als Panel-Tool registriert`);
    const result = await client.callTool({ name, arguments: input });
    // patch: echte Antwort gezielt abwandeln (eine Variante, die kein Lehrbuchname liefert)
    if (patch) { patch(result.structuredContent); result.content = [{ type: "text", text: JSON.stringify(result.structuredContent) }]; }
    check(!result.isError, `${name} liefert eine erfolgreiche echte Serverantwort`);
    const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
    await p.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: input, toolResult: result, prelude });
    const iframe = p.locator("iframe").last();
    await iframe.evaluate((el) => { el.style.width = "510px"; el.style.height = "560px"; });
    return p.frames().at(-1);
  };
  // U2 (M10, 11.11.2026): Layout nach dem Host-Kontext. Claude Desktop meldet im
  // Seitenpanel/Vollbild `fullscreen` + {width, height}, im Chat `inline` + {width, maxHeight}.
  // Nur eine feste Höhe lässt das Panel füllen; der Chat-Weg bleibt wie bisher.
  // LAYOUT_ONLY=1 lässt nur diesen Block laufen; LAYOUT_SHOTS=<ordner> legt die Bilder ab.
  {
    const layoutShots = process.env.LAYOUT_SHOTS || join(tmpdir(), "chemdraw-layout");
    mkdirSync(layoutShots, { recursive: true });
    const MORPHIN = "CN1CC[C@]23c4c5ccc(O)c4O[C@H]2[C@@H](O)C=C[C@H]3[C@H]1C5";
    const MODES = ["inline", "fullscreen"];
    const full = (width, height) => ({ displayMode: "fullscreen", availableDisplayModes: MODES, platform: "desktop", containerDimensions: { width, height } });
    const chat = (width) => ({ displayMode: "inline", availableDisplayModes: MODES, platform: "desktop", containerDimensions: { width, maxHeight: 6000 } });
    // `host`: weitere Optionen für __startHost (Fähigkeiten, messageMode, holdResult …)
    const open = async (name, input, hostContext, { colorScheme = "light", viewport, host = {} } = {}) => {
      const page = await browser.newPage({ viewport: viewport || { width: hostContext.containerDimensions.width, height: 1300 }, colorScheme });
      await page.setContent('<body style="margin:0"></body>');
      await page.addScriptTag({ path: out });
      await page.exposeFunction("__callTool", (req) => client.callTool(req));
      const tool = tools.find((t) => t.name === name);
      const result = await client.callTool({ name, arguments: input });
      check(!result.isError, `U2 ${name}: echte Serverantwort`);
      const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
      await page.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: input, toolResult: result, hostContext, ...host });
      return [page, page.frames().at(-1), result];
    };
    // Im Chat übernimmt Desktop die gemeldete Höhe des Panels.
    const fitChat = async (page) => {
      await page.waitForTimeout(300);
      const size = await page.evaluate(() => window.__panelSizes.at(-1));
      if (size) await page.locator("iframe").last().evaluate((el, h) => { el.style.height = `${h}px`; }, size.height);
      await page.waitForTimeout(150);
    };
    const geo = (f) => f.evaluate(() => {
      const r = (sel) => { const el = document.querySelector(sel); if (!el) return null; const b = el.getBoundingClientRect(); return { top: Math.round(b.top), bottom: Math.round(b.bottom), w: Math.round(b.width), h: Math.round(b.height) }; };
      const de = document.documentElement;
      return { canvas: r('[data-view="structure"] .structure-canvas'), footer: r("[data-testid='panel-footer']"),
        sh: de.scrollHeight, ih: innerHeight, sw: de.scrollWidth, iw: innerWidth, fixed: de.hasAttribute("data-host-height") };
    });
    const lage = (g) => `Fläche ${g.canvas?.w}×${g.canvas?.h}, Fußzeile bis ${g.footer?.bottom}, Dokument ${g.sw}×${g.sh} in ${g.iw}×${g.ih}`;
    const settle = async (f) => { await f.getByRole("button", { name: "Export as PNG" }).waitFor(); await f.page().waitForTimeout(300); };
    const messwerte = {};

    // (a) Morphin im Vollbild 1000×1200, hell und dunkel
    for (const colorScheme of ["light", "dark"]) {
      const [page, f] = await open("generate_molecule", { name_or_smiles: MORPHIN, label: "Morphine" }, full(1000, 1200), { colorScheme });
      await settle(f);
      const g = await geo(f);
      messwerte[`a-${colorScheme}`] = lage(g);
      check(g.fixed && g.ih === 1200, `U2 (a) ${colorScheme}: Panel kennt die feste Höhe (${g.ih} px)`);
      check(g.canvas.h > 600, `U2 (a) ${colorScheme}: Zeichenfläche deutlich höher als 320 px (${g.canvas.h})`);
      check(g.footer.bottom >= 1200 - 40 && g.footer.bottom <= 1200, `U2 (a) ${colorScheme}: Fußzeile unten am Bereich (${g.footer.bottom} von 1200)`);
      check(g.sh <= g.ih && g.sw <= g.iw, `U2 (a) ${colorScheme}: keine Scrollleiste (${lage(g)})`);
      check(await f.getByRole("button", { name: "Expand" }).count() === 0, `U2 (a) ${colorScheme}: im Vollbild kein Expand-Knopf`);
      await page.screenshot({ path: join(layoutShots, `a-morphin-fullscreen-1000x1200-${colorScheme}.png`) });
      if (colorScheme === "light") {
        // 3D hinter dem Knopf nutzt die Höhe ebenfalls statt des 720-px-Quadrats
        await f.getByRole("button", { name: "3D", exact: true }).click();
        await f.locator("[data-view-3d] svg").waitFor({ timeout: 30000 });
        await page.waitForTimeout(300);
        const g3 = await geo(f);
        messwerte["a-3d"] = lage(g3);
        check(g3.canvas.h > 700 && g3.sh <= g3.ih, `U2 (a) 3D: Kuhle füllt die Höhe, nichts scrollt (${lage(g3)})`);
        await page.screenshot({ path: join(layoutShots, "a-morphin-fullscreen-3d-light.png") });
      }
      await page.close();
    }
    // Chat-Einstieg 3D (generate_3d) im Seitenpanel: Bildfläche füllt die Höhe statt 500 px
    {
      const [page, f] = await open("generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" }, full(600, 1000));
      await f.locator(".m3d-panel svg").first().waitFor();
      await page.waitForTimeout(300);
      const m = await f.evaluate(() => ({ h: Math.round(document.querySelector(".m3d-panel").getBoundingClientRect().height),
        sh: document.documentElement.scrollHeight, ih: innerHeight }));
      messwerte["3d-view"] = JSON.stringify(m);
      check(m.h > 900 && m.sh <= m.ih, `U2 generate_3d fullscreen: Panel füllt die Höhe (${JSON.stringify(m)})`);
      await page.close();
    }
    // (b) derselbe Fall im Chat: 320 px wie bisher
    {
      const [page, f] = await open("generate_molecule", { name_or_smiles: MORPHIN, label: "Morphine" }, chat(1000));
      await settle(f);
      await fitChat(page);
      const g = await geo(f);
      messwerte.b = lage(g);
      check(!g.fixed && g.canvas.h === 320, `U2 (b): im Chat bleibt die Zeichenfläche 320 px (${g.canvas.h})`);
      check(g.sh <= g.ih + 1, `U2 (b): Chat-Panel inhaltsgroß, gemeldete Höhe reicht (${g.sh} in ${g.ih})`);
      await page.screenshot({ path: join(layoutShots, "b-morphin-inline-1000.png"), fullPage: true });
      // (e) Expand: Anfrage landet beim Host, danach Vollbild ohne Knopf
      const expand = f.getByRole("button", { name: "Expand" });
      check(await expand.count() === 1, "U2 (e): im Chat mit angebotenem fullscreen steht ein Expand-Knopf");
      await page.evaluate(() => { window.__fullscreenHeight = 1100; });
      await expand.click();
      await expand.waitFor({ state: "detached" });
      await page.waitForTimeout(300);
      const req = await page.evaluate(() => window.__displayModeRequests);
      const ge = await geo(f);
      messwerte.e = `Anfragen ${JSON.stringify(req)}; danach ${lage(ge)}`;
      check(req.length === 1 && req[0].mode === "fullscreen", `U2 (e): Klick landet als Anfrage beim Host (${JSON.stringify(req)})`);
      check(ge.fixed && ge.canvas.h > 500, `U2 (e): nach dem Wechsel füllt das Panel die Höhe, Knopf weg (${ge.canvas.h})`);
      await page.close();
    }
    // (c) inline → fullscreen → inline ohne Neuladen
    {
      const [page, f] = await open("generate_molecule", { name_or_smiles: MORPHIN, label: "Morphine" }, chat(1000));
      await settle(f);
      await f.evaluate(() => { window.__ohneNeuladen = 1; });
      const h0 = (await geo(f)).canvas.h;
      await page.evaluate((c) => window.__setHostContext(c), full(1000, 1200));
      await page.waitForTimeout(300);
      const h1 = (await geo(f)).canvas.h;
      await page.evaluate((c) => window.__setHostContext(c), chat(1000));
      await page.waitForTimeout(300);
      const h2 = (await geo(f)).canvas.h;
      const same = await f.evaluate(() => window.__ohneNeuladen === 1);
      messwerte.c = `${h0} → ${h1} → ${h2}`;
      check(h0 === 320 && h1 > 600 && h2 === 320 && same, `U2 (c): Wechsel ändert die Fläche ohne Neuladen (${h0} → ${h1} → ${h2})`);
      await page.close();
    }
    // (d) 320 px breit, feste Höhe: nichts scrollt waagrecht, kein Knopf abgeschnitten
    const schmal = async (f) => f.evaluate(() => {
      const de = document.documentElement;
      const iw = de.clientWidth;
      const raus = [...document.querySelectorAll("button")].filter((b) => b.getClientRects().length > 0)
        .map((b) => [b.textContent.trim().slice(0, 20), b.getBoundingClientRect()])
        .filter(([, r]) => r.left < -0.5 || r.right > iw + 0.5).map(([t, r]) => `${t}@${Math.round(r.left)}–${Math.round(r.right)}`);
      // Scroll-Container (auto/scroll): Inhalt breiter als die Box heißt waagrecht scrollen.
      // Abschneidende Boxen (hidden): ein sichtbarer Nachfahre ragt über die Kante hinaus.
      // scrollWidth allein taugt dort nicht — skalierte Zeilen (transform) runden um 1–3 px.
      const scroller = [];
      for (const el of document.querySelectorAll("body *")) {
        if (el instanceof SVGElement && !(el instanceof SVGSVGElement)) continue;
        const cs = getComputedStyle(el);
        if (cs.textOverflow === "ellipsis" || el.clientWidth === 0) continue;
        if (/auto|scroll/.test(cs.overflowX) && el.scrollWidth > el.clientWidth + 1) scroller.push(`${el.tagName} ${el.className} ${el.scrollWidth}>${el.clientWidth}`);
        if (cs.overflowX === "hidden") {
          const box = el.getBoundingClientRect();
          const out = [...el.querySelectorAll("*")].filter((c) => (!(c instanceof SVGElement) || c instanceof SVGSVGElement)
            && c.getClientRects().length > 0 && getComputedStyle(c).textOverflow !== "ellipsis"
            && (c.getBoundingClientRect().right > box.right + 1 || c.getBoundingClientRect().left < box.left - 1));
          if (out.length) scroller.push(`${el.tagName} ${el.className} schneidet ${out.slice(0, 3).map((c) => c.tagName + "." + (c.className?.baseVal ?? c.className)).join(", ")}`);
        }
      }
      return { sw: de.scrollWidth, cw: de.clientWidth, raus, scroller };
    });
    for (const [tag, name, input, ready] of [
      ["molecule", "generate_molecule", { name_or_smiles: MORPHIN, label: "Morphine" }, (f) => f.getByRole("button", { name: "Export as PNG" }).waitFor()],
      ["reaction", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" },
        (f) => f.locator('[data-testid="balance-badge"]').waitFor()],
      ["mechanism", "generate_mechanism", { reaction_type: "sn2", substrates: ["C[C@@H](Br)CC", "[C-]#N"] },
        (f) => f.getByRole("button", { name: "Overview", exact: true }).waitFor()],
      ["protein", "generate_protein_or_antibody", { name: "trastuzumab" }, (f) => f.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 })],
    ]) {
      const [page, f] = await open(name, input, full(320, 900));
      await ready(f);
      await page.waitForTimeout(500);
      const views = tag === "mechanism" ? ["Overview", "Step by step"] : tag === "protein" ? ["Structure", "Scheme"] : [null];
      for (const v of views) {
        if (v) await f.getByRole(tag === "protein" ? "tab" : "button", { name: v, exact: true }).click();
        await page.waitForTimeout(300);
        const s = await schmal(f);
        messwerte[`d-${tag}${v ? `-${v}` : ""}`] = `${s.sw}≤${s.cw}`;
        await page.screenshot({ path: join(layoutShots, `d-${tag}${v ? `-${v.replace(/\s+/g, "-").toLowerCase()}` : ""}-320.png`), fullPage: true });
        check(s.sw <= s.cw && s.raus.length === 0 && s.scroller.length === 0,
          `U2 (d) ${tag}${v ? ` ${v}` : ""} 320 px: kein waagrechtes Scrollen, kein Knopf abgeschnitten (${JSON.stringify(s)})`);
      }
      await page.close();
    }
    // Übrige Views bei fester Höhe und breitem Bereich (1400 px, #root bis 1600):
    // nichts ragt seitlich heraus; Stapel bleibt inhaltsgroß, je Karte 320 px, ohne Expand.
    for (const [tag, name, input, ready] of [
      ["spectrum", "generate_spectrum", { spectrum_type: "ir", title: "Aspirin IR", peaks: [{ position: 1750, intensity: 1, label: "Ester C=O" }] }, (f) => f.locator(".spectrum-svg svg").waitFor()],
      ["tlc", "generate_tlc", { title: "Three lanes", lanes: [{ name: "A", spots: [{ rf: 0.2 }] }, { name: "B", spots: [{ rf: 0.6 }] }] }, (f) => f.locator("svg").first().waitFor()],
      ["titration", "generate_titration_curve", { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1, v_acid_ml: 25, c_titrant: 0.1 }, (f) => f.locator("svg").first().waitFor()],
      ["compare", "compare_molecules", { structures: ["ibuprofen", "naproxen", "ketoprofen"] }, (f) => f.locator("svg").first().waitFor()],
      ["batch", "batch_generate", { molecules: ["benzene", "toluene", "phenol"] }, (f) => f.locator(".panel-title").nth(2).waitFor()],
    ]) {
      const [page, f] = await open(name, input, full(1400, 900), { viewport: { width: 1400, height: 900 } });
      await ready(f);
      await page.waitForTimeout(500);
      const s = await schmal(f);
      await page.screenshot({ path: join(layoutShots, `w-${tag}-1400x900.png`), fullPage: true });
      messwerte[`w-${tag}`] = `${s.sw}≤${s.cw}`;
      check(s.sw <= s.cw && s.raus.length === 0 && s.scroller.length === 0, `U2 breit ${tag} 1400 px: nichts ragt heraus (${JSON.stringify(s)})`);
      if (tag === "titration" || tag === "compare") {
        // U5-Befund 12.11.2026: das Diagramm blieb im Vollbild 480 px hoch, darunter leere Fläche.
        const p = await f.evaluate(() => {
          const box = document.querySelector(".plot-svg").getBoundingClientRect();
          const svg = document.querySelector(".plot-svg svg").getBoundingClientRect();
          return { box: Math.round(box.height), svg: Math.round(svg.height), sh: document.documentElement.scrollHeight, ih: innerHeight };
        });
        messwerte[`w-${tag}-höhe`] = JSON.stringify(p);
        check(p.box > 600 && p.svg > 0.6 * p.box && p.sh <= p.ih, `U5 ${tag} 1400×900: Diagramm füllt die Höhe (${JSON.stringify(p)})`);
      }
      if (tag === "batch") {
        const hs = await f.locator(".structure-canvas").evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().height)));
        messwerte["w-batch-flächen"] = hs.join(",");
        check(hs.length === 3 && hs.every((h) => h === 320), `U2 batch: Stapel bleibt inhaltsgroß, je Karte 320 px (${hs.join(", ")})`);
      }
      await page.close();
    }
    // Isomer-Auswahl (Glucose): das gewählte Molekül füllt die Höhe wie die direkte Ansicht.
    {
      const [page, f] = await open("generate_molecule", { name_or_smiles: "glucose" }, full(1000, 1100));
      const first = f.locator("button.candidate").first();
      await first.waitFor({ timeout: 30000 });
      await first.click();
      await settle(f);
      const g = await geo(f);
      messwerte.isomer = lage(g);
      check(g.canvas.h > 500 && g.sh <= g.ih, `U2 Isomer-Auswahl: gewähltes Molekül füllt die Höhe (${lage(g)})`);
      await page.close();
    }
    // Diagnose im echten Chromium: Dreifachklick auf den Titel blendet den Block ein und aus.
    {
      const [page, f] = await open("generate_molecule", { name_or_smiles: MORPHIN, label: "Morphine" }, chat(700));
      await settle(f);
      await f.locator(".panel-title").click({ clickCount: 3 });
      const block = f.locator("[data-testid='host-diagnostics']");
      await block.waitFor();
      const text = await block.innerText();
      check(/"serverTools"/.test(text) && /"displayMode": "inline"/.test(text) && /"maxHeight": 6000/.test(text) && /"platform": "desktop"/.test(text),
        "U2 Diagnose: Dreifachklick zeigt Fähigkeiten und Kontext");
      await page.screenshot({ path: join(layoutShots, "diagnose-inline-700.png"), fullPage: true });
      await f.locator(".panel-title").click({ clickCount: 3 });
      await block.waitFor({ state: "detached" });
      check(true, "U2 Diagnose: zweiter Dreifachklick blendet aus");
      await page.close();
    }

    // U3/U4/U4b (11.11.2026): Arbeitsplatz-Panel — Weiter-Zeile (ui/message), Auswahl
    // per Klick (ui/update-model-context), Lernmodus, Platzhalter aus toolinput.
    // UI_SHOTS=<ordner> legt die Bilder ab.
    {
      const uiShots = process.env.UI_SHOTS || join(tmpdir(), "chemdraw-ui-etappe");
      mkdirSync(uiShots, { recursive: true });
      const NO_MESSAGE = { serverTools: {}, updateModelContext: { text: {} } };
      const log = (page) => page.evaluate(() => window.__bridgeLog || []);
      const lastContext = async (page) => (await log(page)).filter(([k]) => k === "context").at(-1)?.[1] ?? "";
      const row = (f) => f.locator("[data-testid='continue-row']");
      const morphine = { name_or_smiles: MORPHIN, label: "Morphine" };

      // Ohne Host-Fähigkeit `message` keine Zeile, auch kein leerer Kasten
      {
        const [page, f] = await open("generate_molecule", morphine, full(1000, 1200), { host: { hostCapabilities: NO_MESSAGE } });
        await settle(f);
        check(await row(f).count() === 0 && !/Continue in chat/.test(await f.locator("body").innerText()),
          "U3: ohne `message` keine Weiter-Zeile");
        await page.close();
      }
      // Vollbild 1000×1200 hell und dunkel, Gruppe festgehalten: Kontext nennt sie, Knopf → ui/message
      for (const colorScheme of ["light", "dark"]) {
        const [page, f] = await open("generate_molecule", morphine, full(1000, 1200), { colorScheme });
        await settle(f);
        const chip = f.locator("button.functional-group").first();
        const label = (await chip.locator("span").nth(1).innerText()).trim();
        await chip.click();
        await f.page().waitForTimeout(700);
        const ctx = await lastContext(page);
        check(await chip.getAttribute("aria-pressed") === "true", `U4 ${colorScheme}: Klick hält die Gruppe fest (${label})`);
        check(ctx.includes(`Pinned selection: the ${label} group`) && ctx.includes("Morphine"),
          `U4 ${colorScheme}: ui/update-model-context enthält die Gruppe (${ctx.split("\n").find((l) => l.startsWith("Pinned")) || ctx.slice(0, 120)})`);
        // Maus über die Zeichnung und wieder weg: Auswahl bleibt
        await f.locator(".structure-canvas").first().hover();
        await page.mouse.move(5, 5);
        check(await chip.getAttribute("aria-pressed") === "true", `U4 ${colorScheme}: Hover löscht die Auswahl nicht`);
        const g = await geo(f);
        check(g.sh <= g.ih && g.sw <= g.iw && g.canvas.h > 500, `U3 ${colorScheme}: Vollbild mit Weiter-Zeile ohne Scrollleiste (${lage(g)})`);
        await page.screenshot({ path: join(uiShots, `molecule-fullscreen-1000x1200-pinned-${colorScheme}.png`) });
        if (colorScheme === "light") {
          const want = `Explain the ${label.toLowerCase()} group in Morphine`;
          await row(f).getByRole("button", { name: `Explain this ${label.toLowerCase()}` }).click();
          await f.page().waitForTimeout(400);
          const entries = await log(page);
          const msgAt = entries.findIndex(([k]) => k === "message");
          check(msgAt > 0 && entries[msgAt][1].startsWith(want), `U3: Klick kommt als ui/message an (${entries[msgAt]?.[1]})`);
          check(entries[msgAt - 1][0] === "context" && entries[msgAt - 1][1].includes(`the ${label} group`),
            "U3: direkt vor der Nachricht ging der aktuelle Kontext raus");
        }
        await page.close();
      }
      // Host lehnt ab: ruhiger Hinweis in der Zeile, Knopf bleibt bedienbar
      {
        const [page, f] = await open("generate_molecule", morphine, full(1000, 1200), { host: { messageMode: "isError" } });
        await settle(f);
        const b = row(f).getByRole("button", { name: "Predict the IR bands" });
        await b.click();
        await row(f).getByText("did not take the message").waitFor();
        check(await b.isEnabled(), "U3: Ablehnung zeigt Hinweis, Knopf bleibt bedienbar");
        await page.close();
      }
      // Lernmodus: Name nirgends im DOM (Text und Attribute), auch nicht im gesendeten Satz
      {
        const [page, f] = await open("generate_molecule", { name_or_smiles: "aspirin" }, full(1000, 1200));
        await settle(f);
        await f.getByRole("tab", { name: "Study" }).click();
        await f.locator("[data-view='study']").waitFor();
        await page.waitForTimeout(300);
        const leak = await f.evaluate(() => {
          const attrs = [...document.querySelectorAll("*")].flatMap((el) => [...el.attributes].map((a) => a.value));
          const all = `${document.body.innerText} ${document.body.textContent} ${attrs.join(" ")} ${document.title}`;
          return ["aspirin", "acetylsalicyl", "50-78-2", "ChemDraw-Output"].filter((w) => all.toLowerCase().includes(w.toLowerCase()));
        });
        check(leak.length === 0, `U4b: Lernmodus verrät nichts im DOM (${leak.join(", ") || "keine Treffer"})`);
        await page.screenshot({ path: join(uiShots, "study-covered-1000x1200.png") });
        await row(f).getByRole("button", { name: "Give me a hint" }).click();
        await page.waitForTimeout(400);
        const msg = (await log(page)).filter(([k]) => k === "message").at(-1)?.[1] ?? "";
        const ctx = await lastContext(page);
        check(msg && !/aspirin/i.test(msg) && /SMILES/.test(msg), `U4b: Hinweis-Satz nennt SMILES statt Namen (${msg})`);
        check(/Study mode/.test(ctx) && /aspirin/i.test(ctx) && /Still covered/.test(ctx), "U4b: Kontext nennt Stoff und Verdecktes für Claude");
        await f.getByRole("button", { name: "Reveal all" }).click();
        await page.waitForTimeout(300);
        const text = await f.locator("body").innerText();
        check(/aspirin/i.test(text) && /Everything revealed/.test(text), "U4b: Reveal all deckt Name und Werte auf");
        await page.screenshot({ path: join(uiShots, "study-revealed-1000x1200.png") });
        await page.close();
      }
      // 320×900: Weiter-Zeile untereinander, nichts waagrecht; Fußzeile per senkrechtem Scrollen erreichbar
      {
        const [page, f] = await open("generate_molecule", morphine, full(320, 900));
        await settle(f);
        await f.locator("button.functional-group").first().click();
        await page.waitForTimeout(300);
        const s = await schmal(f);
        const inRow = await row(f).locator("button").evaluateAll((bs) => bs.map((b) => {
          const r = b.getBoundingClientRect();
          return { t: b.textContent.trim(), l: Math.round(r.left), r: Math.round(r.right), h: Math.round(r.height) };
        }));
        const iw = await f.evaluate(() => document.documentElement.clientWidth);
        check(s.sw <= s.cw && s.raus.length === 0 && s.scroller.length === 0, `U3 320: kein waagrechtes Scrollen (${JSON.stringify(s)})`);
        check(inRow.length >= 3 && inRow.every((b) => b.l >= 0 && b.r <= iw && b.h >= 40), `U3 320: alle Weiter-Knöpfe innerhalb der Breite, ≥ 40 px hoch (${JSON.stringify(inRow)})`);
        await page.screenshot({ path: join(uiShots, "molecule-320x900-continue.png") });
        const reach = await f.evaluate(() => {
          const de = document.scrollingElement || document.documentElement;
          const out = {};
          for (const name of ["Export as PNG", "Add to Anki"]) {
            const b = [...document.querySelectorAll("button")].find((x) => `${x.getAttribute("aria-label") || ""} ${x.textContent}`.includes(name));
            if (!b) { out[name] = "fehlt"; continue; }
            b.scrollIntoView({ block: "center" });
            const r = b.getBoundingClientRect();
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            out[name] = { top: Math.round(r.top), bottom: Math.round(r.bottom), scrolled: Math.round(de.scrollTop), sh: de.scrollHeight, ih: innerHeight, hit: Boolean(hit && b.contains(hit)) };
          }
          return out;
        });
        const ok = Object.values(reach).every((v) => typeof v === "object" && v.hit && v.top >= 0 && v.bottom <= v.ih);
        check(ok, `U3 320×900: Export PNG/Add to Anki per senkrechtem Scrollen erreichbar, nicht abgeschnitten (${JSON.stringify(reach)})`);
        await page.screenshot({ path: join(uiShots, "molecule-320x900-scrolled-footer.png") });
        await page.close();
      }
      // Chat-Weg (inline) mit Weiter-Zeile
      {
        const [page, f] = await open("generate_molecule", morphine, chat(700));
        await settle(f);
        await fitChat(page);
        const g = await geo(f);
        check(await row(f).count() === 1 && g.sh <= g.ih + 1, `U3 inline: Weiter-Zeile im Chat, gemeldete Höhe reicht (${lage(g)})`);
        await page.screenshot({ path: join(uiShots, "molecule-inline-700-continue.png"), fullPage: true });
        await page.close();
      }
      // Platzhalter aus toolinput (Stapel), dann das Ergebnis; Abbruch beendet den Ladezustand
      {
        const input = { molecules: ["benzene", "toluene", "phenol"] };
        const [page, f, result] = await open("batch_generate", input, full(1000, 900), { host: { holdResult: true } });
        const ph = f.locator("[data-testid='tool-placeholder']");
        await ph.waitFor();
        const labels = await f.locator(".placeholder-card").allInnerTexts();
        check(labels.join(",") === "benzene,toluene,phenol" && !/Waiting for data/.test(await f.locator("body").innerText()),
          `toolinput: beschriftete Platzhalter statt „Waiting for data…“ (${labels.join(", ")})`);
        await page.screenshot({ path: join(uiShots, "placeholder-toolinput-batch.png") });
        await page.evaluate((r) => window.__sendToolResult(r), result);
        await f.locator(".panel-title").nth(2).waitFor();
        check(await ph.count() === 0, "toolinput: das Ergebnis ersetzt den Platzhalter");
        await page.close();
      }
      {
        const [page, f] = await open("generate_molecule", { name_or_smiles: "caffeine" }, full(1000, 900), { host: { holdResult: true } });
        await f.locator("[data-testid='tool-placeholder']").waitFor();
        check(/caffeine/.test(await f.locator("body").innerText()), "toolinput: Platzhalter nennt den Stoff");
        await page.screenshot({ path: join(uiShots, "placeholder-toolinput-molecule.png") });
        await page.evaluate(() => window.__cancelTool("user action"));
        await f.getByText("The request was cancelled").waitFor();
        check(await f.locator("[aria-busy='true']").count() === 0, "toolcancelled: ein Satz, kein Ladezustand");
        await page.close();
      }
    }
    console.log("U2 Messwerte:", JSON.stringify(messwerte, null, 1));
  }
  if (process.env.LAYOUT_ONLY) {
    console.log("LAYOUT_ONLY: übrige Fälle übersprungen");
    await browser.close();
    await client.close();
    process.exit(0);
  }

  const gallery = await browser.newPage({ viewport: { width: 1530, height: 560 } });
  await gallery.setContent('<body style="margin:0;display:flex"></body>');
  await gallery.addScriptTag({ path: out });
  await gallery.exposeFunction("__callTool", (req) => client.callTool(req));
  for (const [type, substrates, example, count] of [
    // Gezeichnet werden die Substrate; der Titel nennt sie mit Namen statt rohem SMILES
    // (Server: _substrate_label, gebunden in tests/test_server_mechanism.py).
    // Schrittzahlen seit den Lehrbuch-Konventionen (CHANGELOG Unreleased): SN1 6, SN2 3, Fischer 8.
    ["sn1", ["CC(C)(C)Cl", "O"], "tert-butyl chloride + water", 6],
    ["sn2", ["C[C@@H](Br)CC", "[C-]#N"], "(R)-2-bromobutane + cyanide", 3],
    ["fischer_ester", ["CCC(=O)O", "CCO"], "propionic acid + ethanol", 8],
  ]) {
    const f = await mount(gallery, "generate_mechanism", { reaction_type: type, substrates });
    await f.getByRole("button", { name: "Overview", exact: true }).waitFor();
    const body = await f.locator("body").innerText();
    check(!body.includes("textbook example") && body.includes(example), `${type}: sichtbarer Titel nennt die gezeichneten Substrate`);
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
  // E2: Einblend-Drehung — die Lage ändert sich ohne Zutun und kommt dann zur Ruhe.
  const ersteLage = JSON.stringify(await geometry());
  await spatial.waitForTimeout(1600);
  const ruhe = JSON.stringify(await geometry());
  await spatial.waitForTimeout(200);
  check(ruhe !== ersteLage && JSON.stringify(await geometry()) === ruhe, "3D: Einblend-Drehung läuft an und kommt zur Ruhe");
  await spatial.screenshot({ path: join(tmpdir(), "panel-host-wave1-3d.png") });
  const before = JSON.stringify(await geometry());
  const box = await canvas.boundingBox();
  await spatial.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await spatial.mouse.down();
  await spatial.mouse.move(box.x + box.width / 2 + 85, box.y + box.height / 2 + 45, { steps: 8 });
  await spatial.mouse.up();
  check(JSON.stringify(await geometry()) !== before, "3D: Ziehen ändert die projizierten Atomkoordinaten");
  await spatial.close();

  // E8/E13: Proteine — Cartoon (Mol*-Engine, WebGL) statt Strukturformel, über
  // beide Einstiege, in der Sandbox mit Standard-CSP. PROTEIN_SHOTS=<ordner>
  // legt zusätzlich die Bildschau aller Laborfälle ab.
  const shots = process.env.PROTEIN_SHOTS || join(tmpdir(), "chemdraw-protein");
  mkdirSync(shots, { recursive: true });
  // generate_protein_or_antibody (10.11.2026) ist der eigene Eingang; die beiden alten
  // bleiben mit je einem Fall drin, weil sie Proteinnamen weiter zeichnen.
  const proteinCases = [
    ["generate_protein_or_antibody", "lysozyme", /Lysozyme C, Gallus gallus \(hen egg white\)/],
    ["generate_3d", "trypsin", /Bos taurus/],
    ["generate_protein_or_antibody", "trastuzumab", /Trastuzumab Fab fragment/],
    // Genkürzel ohne PDB-Eintrag → AlphaFold-Modell (gemessen 10.11.: E. coli CsrD, P13518)
    ["generate_molecule", "CsrD", /RNase E specificity factor CsrD, Escherichia coli/],
    ["generate_molecule", "hemoglobin", /Hemoglobin/],
    ["generate_protein_or_antibody", "antibody", /Architecture of an intact IgG/],
  ];
  if (process.env.PROTEIN_SHOTS) {
    proteinCases.push(
      ["generate_molecule", "insulin", /Insulin/],
      ["generate_molecule", "GFP", /Green fluorescent protein/],
      ["generate_molecule", "IgG", /Architecture of an intact IgG antibody/],
      ["generate_molecule", "carbonic anhydrase", /Carbonic anhydrase/],
      ["generate_molecule", "myoglobin", /Myoglobin/],
    );
  }
  // Pixel der Zeichenfläche, die sich vom Hintergrund (Ecke) abheben, und davon
  // die farbigen; dazu die Helligkeit des Hintergrunds (WebGL-Puffer bleibt
  // dank preserveDrawingBuffer lesbar)
  const inked = (f) => f.locator("[data-cartoon-host] canvas").evaluate((c) => {
    const t = document.createElement("canvas");
    t.width = 160; t.height = 120;
    const g = t.getContext("2d");
    g.drawImage(c, 0, 0, 160, 120);
    const d = g.getImageData(0, 0, 160, 120).data;
    const bg = [d[0], d[1], d[2]];
    let n = 0, colored = 0, sum = 0;
    for (let i = 0; i < d.length; i += 4) {
      sum = (sum * 31 + d[i] + d[i + 1] + d[i + 2]) % 1000003;
      if (Math.abs(d[i] - bg[0]) + Math.abs(d[i + 1] - bg[1]) + Math.abs(d[i + 2] - bg[2]) > 60) n++;
      if (Math.max(d[i], d[i + 1], d[i + 2]) - Math.min(d[i], d[i + 1], d[i + 2]) > 40) colored++;
    }
    return { n, colored, sum, bgLum: (bg[0] + bg[1] + bg[2]) / 3 };
  });
  // Lesbarkeit im Farbschema: Kontrast von Titel, Legende und Quellenzeile zum Panelgrund
  const contrast = (f) => f.locator("body").evaluate(() => {
    const lum = (c) => {
      const [r, g, b] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map((v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const bg = lum(getComputedStyle(document.body).backgroundColor);
    const ratio = (el) => {
      const l = lum(getComputedStyle(el).color);
      return (Math.max(l, bg) + 0.05) / (Math.min(l, bg) + 0.05);
    };
    const els = [document.querySelector(".panel-title"), ...document.querySelectorAll("[data-protein-viewer] ~ div")];
    return Math.min(...els.filter(Boolean).map(ratio));
  });
  // Wie Desktop: iframe auf die gemeldete Panelhöhe (E19: das Bild ist größer als
  // die alten 560 px; ohne das scrollte das Rad den iframe-Inhalt statt der Seite)
  const fitFrame = async (page) => {
    await page.waitForTimeout(250);
    const size = await page.evaluate(() => window.__panelSizes.at(-1));
    if (size) await page.locator("iframe").last().evaluate((el, h) => { el.style.height = `${h}px`; }, size.height);
    await page.waitForTimeout(150);
  };
  for (const colorScheme of ["light", "dark"])
  for (const [tool, name, title] of proteinCases) {
    const page = await browser.newPage({ viewport: { width: 530, height: 1000 }, colorScheme });
    const tag = `${name} (${colorScheme})`;
    await page.setContent('<body style="margin:0"></body>');
    await page.addScriptTag({ path: out });
    await page.exposeFunction("__callTool", (req) => client.callTool(req));
    const f = await mount(page, tool, tool === "generate_protein_or_antibody" ? { name } : { name_or_smiles: name });
    await f.locator("[data-protein-viewer]").waitFor({ timeout: 30000 });
    check(title.test(await f.locator(".panel-title").innerText()), `Protein ${tag}: Titel nennt Protein und Organismus`);
    // Antikörper: IgG-Schema im Panel (allgemein: Startansicht; Fab: Umschalter, ein Arm markiert)
    const schemeShot = async (expect) => {
      const svg = f.locator("svg[data-igg-scheme]");
      check(await svg.isVisible() && (await svg.getAttribute("data-igg-scheme")) === expect,
        `Protein ${tag}: IgG-Schema im Panel (Markierung ${expect})`);
      const worst = await svg.evaluate((el) => {
        const rgb = (c) => c.match(/\d+/g).slice(0, 3).map(Number);
        const bg = rgb(getComputedStyle(document.body).backgroundColor);
        return Math.min(...[...el.querySelectorAll("text")].filter((t) => !t.closest("g[transform]"))
          .map((t) => rgb(getComputedStyle(t).fill).reduce((a, v, i) => a + Math.abs(v - bg[i]), 0)));
      });
      check(worst > 200, `Protein ${tag}: Schema-Beschriftung hebt sich vom Grund ab (Abstand ${worst})`);
      await fitFrame(page);
      await page.screenshot({ path: join(shots, `panel-${name}-scheme-${colorScheme}.png`) });
    };
    if (name === "antibody" || name === "IgG") {
      await schemeShot("none");
      await f.getByRole("tab", { name: "Structure" }).click();
    }
    if (name === "trastuzumab") {
      await f.getByRole("tab", { name: "Scheme" }).click();
      await schemeShot("fab");
      await f.getByRole("tab", { name: "Structure" }).click();
    }
    await f.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 });
    await fitFrame(page);
    await page.waitForTimeout(1700); // Einblend-Drehung (1,2 s) abwarten
    const vorher = await inked(f);
    // Untergrenze: es ist etwas gezeichnet; Obergrenze: der Hintergrund ist hell
    // (ein schwarzer Hintergrund — Farbe als rgb() statt Hex — bestand sonst)
    // Untergrenze 1000 seit E19: die Fläche ist jetzt quadratisch statt quer — ein
    // langgestrecktes Modell (CsrD) füllt davon weniger (1455 Pixel, Bild geprüft)
    check(vorher.n > 1000 && vorher.n < 12000 && vorher.colored > 800,
      `Protein ${tag}: Cartoon gezeichnet (${vorher.n} von 19200 Pixeln Struktur, ${vorher.colored} farbig)`);
    check(colorScheme === "dark" ? vorher.bgLum < 90 : vorher.bgLum > 200,
      `Protein ${tag}: Zeichengrund folgt dem Farbschema (Helligkeit ${Math.round(vorher.bgLum)})`);
    const k = await contrast(f);
    check(k >= 4.5, `Protein ${tag}: Titel, Legende und Quellen lesbar (Kontrast ≥ ${k.toFixed(1)})`);
    await page.screenshot({ path: join(shots, `panel-${name.split(" ")[0]}-${colorScheme}.png`) });
    const box = await f.locator("[data-cartoon-host] canvas").boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 70, box.y + box.height / 2 + 30, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(300);
    check((await inked(f)).sum !== vorher.sum, `Protein ${tag}: Ziehen dreht den Cartoon`);
    const pfad = await f.locator("[data-testid='panel-footer'] .panel-footer-path").first().getAttribute("title");
    check(pfad?.endsWith(".png") && existsSync(pfad), `Protein ${tag}: Fußzeile zeigt die echte PNG-Datei`);
    if (name === "lysozyme" && colorScheme === "light") {
      // Bedienung mit der echten Engine: bloßes Rad scrollt den Chat (Bild bleibt),
      // Strg+Rad zoomt, Rechtsziehen verschiebt, Reset kehrt zurück, Umschalter wirken
      const mitte = [box.x + box.width / 2, box.y + box.height / 2];
      const stand = async () => { await page.waitForTimeout(450); return inked(f); };
      const ruhe = await stand();
      await page.mouse.move(...mitte);
      await page.mouse.wheel(0, -400);
      check((await stand()).sum === ruhe.sum, `Protein ${tag}: bloßes Mausrad zoomt nicht (Chat scrollt weiter)`);
      await page.keyboard.down("Control");
      await page.mouse.wheel(0, -400);
      await page.keyboard.up("Control");
      const zoom = await stand();
      check(zoom.n > ruhe.n * 1.15, `Protein ${tag}: Strg+Rad zoomt (${ruhe.n} → ${zoom.n} Pixel Struktur)`);
      await page.mouse.move(...mitte);
      await page.mouse.down({ button: "right" });
      await page.mouse.move(mitte[0] + 80, mitte[1], { steps: 6 });
      await page.mouse.up({ button: "right" });
      check((await stand()).sum !== zoom.sum, `Protein ${tag}: Rechtsziehen verschiebt`);
      await f.getByRole("button", { name: "Reset" }).click();
      const zurück = await stand();
      check(Math.abs(zurück.n - vorher.n) < vorher.n * 0.1, `Protein ${tag}: Reset stellt die Ausgangsansicht her (${vorher.n} ↔ ${zurück.n})`);
      let bild = zurück.sum;
      for (const [rolle, text] of [["tab", "Trace"], ["tab", "Cartoon"], ["tab", "Rainbow N→C"], ["tab", "Secondary"]]) {
        await f.getByRole(rolle, { name: text }).click();
        const jetzt = await stand();
        check(jetzt.sum !== bild && await f.locator('[data-protein-viewer="ready"]').count() === 1,
          `Protein ${tag}: „${text}“ ändert das Bild, Engine bleibt bereit`);
        bild = jetzt.sum;
      }
    }
    if (name === "CsrD") {
      const vorFarbe = (await inked(f)).sum;
      await f.getByRole("tab", { name: "Confidence" }).click();
      await page.waitForTimeout(300);
      check((await f.locator("body").innerText()).includes("pLDDT > 90") && (await inked(f)).sum !== vorFarbe,
        `Protein ${tag}: Konfidenz-Ansicht des AlphaFold-Modells färbt um`);
    }
    if (name === "hemoglobin") {
      check((await f.locator("body").innerText()).includes("heme b (HEM) ×4"), `Protein ${tag}: Legende nennt die vier Häm-Gruppen`);
      await f.getByRole("button", { name: "Export as PNG" }).click();
      await f.getByRole("button", { name: /Saved:/ }).waitFor({ timeout: 15000 });
      const savedPath = (await f.getByRole("button", { name: /Saved:/ }).getAttribute("title")).replace(/^Saved: /, "");
      const png = readFileSync(savedPath);
      // PNG-Kopf, dann Breite (Bytes 16–19): das Cartoon-Bild in dreifacher Auflösung, nicht die 480-px-Spur
      check(png.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) && png.readUInt32BE(16) > 1200,
        `Protein hemoglobin: Export schreibt das Cartoon-Bild als PNG (${png.readUInt32BE(16)} px breit)`);
    }
    await page.close();
  }
  // Rückfall in der echten Sandbox: ohne WebGL-Kontext bleibt die SVG-Spur stehen
  for (const colorScheme of ["light", "dark"]) {
    const page = await browser.newPage({ viewport: { width: 530, height: 1000 }, colorScheme });
    await page.setContent('<body style="margin:0"></body>');
    await page.addScriptTag({ path: out });
    await page.exposeFunction("__callTool", (req) => client.callTool(req));
    const noGl = "HTMLCanvasElement.prototype.getContext=(o=>function(t,...a){return /webgl/i.test(t)?null:o.call(this,t,...a)})(HTMLCanvasElement.prototype.getContext);";
    const f = await mount(page, "generate_molecule", { name_or_smiles: "lysozyme" }, noGl);
    await f.locator('[data-protein-viewer="failed"]').waitFor({ timeout: 30000 });
    await fitFrame(page);
    const trace = f.locator("svg[data-backbone]");
    check(await trace.isVisible() && await trace.locator("path[data-residue-ss]").count() > 100,
      `Protein ohne WebGL (${colorScheme}): SVG-Spur als Rückfall gezeichnet, keine leere Fläche`);
    check((await f.locator("body").innerText()).includes("3D cartoon unavailable here"), `Protein ohne WebGL (${colorScheme}): Panel sagt, warum`);
    const marken = await f.locator("svg[data-backbone] text").evaluateAll((ts) => {
      const rgb = (c) => c.match(/\d+/g).slice(0, 3).map(Number);
      const bg = rgb(getComputedStyle(document.body).backgroundColor);
      return ts.map((t) => rgb(getComputedStyle(t).fill).reduce((a, v, i) => a + Math.abs(v - bg[i]), 0));
    });
    check(marken.length >= 2 && Math.min(...marken) > 200, `Protein ohne WebGL (${colorScheme}): N-/C-Marken heben sich vom Grund ab (${marken.join(", ")})`);
    await page.screenshot({ path: join(shots, `panel-fallback-lysozyme-${colorScheme}.png`) });
    await page.close();
  }

  // E19: Bildgröße im Proteinpanel am Maßstab des Molekül-3D-Knopfs
  // (styles.css, `.structure-layout[data-layout-3d] .structure-canvas`: Quadrat,
  // höchstens 720 px). Wie Desktop: das iframe bekommt die Höhe, die das Panel
  // per size-changed meldet — dann darf im Panel nichts scrollen oder abschneiden.
  const sizeShots = process.env.PROTEIN_SIZE_SHOTS || join(tmpdir(), "chemdraw-protein-size");
  mkdirSync(sizeShots, { recursive: true });
  const fitted = async (page, width, tool, name, prelude = "", patch = null) => {
    await page.setContent('<body style="margin:0"></body>');
    await page.addScriptTag({ path: out });
    await page.exposeFunction("__callTool", (req) => client.callTool(req));
    const f = await mount(page, tool, { name_or_smiles: name }, prelude, patch);
    await page.locator("iframe").last().evaluate((el, w) => { el.style.width = `${w}px`; }, width);
    const fit = async () => {
      await page.waitForTimeout(250); // ResizeObserver + rAF der Größenmeldung
      const size = await page.evaluate(() => window.__panelSizes.at(-1));
      check(size && size.height > 0, `E19 ${name} ${width}px: Panel meldet seine Höhe (${size?.height} px)`);
      await page.locator("iframe").last().evaluate((el, h) => { el.style.height = `${h}px`; }, size.height);
      await page.waitForTimeout(150);
      const doc = await f.evaluate(() => ({ sh: document.documentElement.scrollHeight, ih: innerHeight,
        sw: document.documentElement.scrollWidth, iw: innerWidth }));
      check(doc.sh <= doc.ih + 1 && doc.sw <= doc.iw,
        `E19 ${name} ${width}px: gemeldete Höhe reicht, nichts scrollt oder ragt seitlich heraus (${doc.sw}×${doc.sh} in ${doc.iw}×${doc.ih})`);
      return size;
    };
    return { f, fit };
  };
  // Fläche des Bildes: Box des Viewers und die tatsächlich gemalte Größe einer
  // SVG-Zeichnung (viewBox mit „meet“ eingepasst)
  const stageOf = (f) => f.evaluate(() => {
    const r = (el) => { const b = el.getBoundingClientRect(); return { w: Math.round(b.width), h: Math.round(b.height) }; };
    const painted = (svg) => {
      if (!svg) return null;
      const vb = svg.viewBox.baseVal, b = svg.getBoundingClientRect();
      const s = Math.min(b.width / vb.width, b.height / vb.height);
      return { w: Math.round(vb.width * s), h: Math.round(vb.height * s) };
    };
    const stage = document.querySelector("[data-protein-viewer]");
    const canvas = document.querySelector("[data-cartoon-host] canvas");
    return { stage: r(stage), canvas: canvas && getComputedStyle(canvas.parentElement).visibility !== "hidden" ? r(canvas) : null,
      backbone: painted(document.querySelector("svg[data-backbone]")),
      scheme: painted(document.querySelector("svg[data-igg-scheme]")) };
  });
  // Eigener Browser für die großen WebGL-Flächen: danach konnte der gemeinsame
  // Browser in Welle 2 keine Screenshots mehr aufnehmen (Page.captureScreenshot,
  // zweimal in Folge, 10.11.)
  const e19Browser = await chromium.launch();
  const groß = {};
  for (const width of [860, 360]) {
    const page = await e19Browser.newPage({ viewport: { width: width + 40, height: 1300 } });
    const { f, fit } = await fitted(page, width, "generate_molecule", "lysozyme");
    await f.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 });
    await fit();
    const m = await stageOf(f);
    groß[`cartoon-${width}`] = m;
    const inhalt = width - 64; // body 16 + Panel 16 je Seite
    check(m.stage.w >= inhalt - 2 && Math.abs(m.stage.h - Math.min(m.stage.w, 720)) <= 1,
      `E19 lysozyme ${width}px: Bildfläche volle Breite, Höhe wie der 3D-Knopf (Quadrat, höchstens 720) — ${m.stage.w}×${m.stage.h}`);
    check(m.canvas && m.canvas.w === m.stage.w && m.canvas.h === m.stage.h, `E19 lysozyme ${width}px: Cartoon füllt die Fläche (${m.canvas?.w}×${m.canvas?.h})`);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: join(sizeShots, `e19-cartoon-lysozyme-${width}.png`), fullPage: true });
    if (width === 860) {
      // Das große Bild fängt das Rad nicht ein: bloßes Rad über der Bildmitte
      // scrollt die Seite (den Chat), das Bild bleibt, wie es war
      await page.setViewportSize({ width: 900, height: 600 });
      await page.evaluate(() => window.scrollTo(0, 0));
      const box = await f.locator("[data-cartoon-host] canvas").boundingBox();
      const vorRad = await inked(f);
      await page.mouse.move(box.x + box.width / 2, Math.min(box.y + box.height / 2, 560));
      await page.mouse.wheel(0, 300);
      await page.waitForTimeout(450);
      const y = await page.evaluate(() => window.scrollY);
      check(y > 0 && (await inked(f)).sum === vorRad.sum, `E19 lysozyme 860px: Rad über dem großen Bild scrollt die Seite (${y} px), Bild unverändert`);
    }
    await page.close();
  }
  {
    const noGl = "HTMLCanvasElement.prototype.getContext=(o=>function(t,...a){return /webgl/i.test(t)?null:o.call(this,t,...a)})(HTMLCanvasElement.prototype.getContext);";
    const page = await e19Browser.newPage({ viewport: { width: 900, height: 1300 } });
    const { f, fit } = await fitted(page, 860, "generate_molecule", "lysozyme", noGl);
    await f.locator('[data-protein-viewer="failed"]').waitFor({ timeout: 30000 });
    await fit();
    const m = await stageOf(f);
    const c = groß["cartoon-860"];
    check(m.stage.w === c.stage.w && m.stage.h === c.stage.h,
      `E19 Rückfall: SVG-Spur in derselben Fläche wie der Cartoon (${m.stage.w}×${m.stage.h} ↔ ${c.stage.w}×${c.stage.h})`);
    check(m.backbone && m.backbone.w >= m.stage.w - 2 && m.backbone.h >= m.stage.h - 2,
      `E19 Rückfall: Spur malt die ganze Fläche aus, kein Briefkasten (${m.backbone?.w}×${m.backbone?.h})`);
    await page.screenshot({ path: join(sizeShots, "e19-fallback-lysozyme-860.png"), fullPage: true });
    await page.close();
  }
  // Varianten: Fab-Arm markiert (Trastuzumab), ganzes IgG markiert (dieselbe
  // Antwort, Markierung auf „igg“ umgestellt), allgemeine Architektur ohne Markierung
  const toIgg = (sc) => { sc.protein.scheme.highlight = "igg"; };
  for (const [width, name, patch, shot] of [
    [860, "trastuzumab", null, "trastuzumab"], [360, "trastuzumab", null, "trastuzumab"],
    [860, "trastuzumab", toIgg, "igg-highlight"], [860, "antibody", null, "antibody-general"],
  ]) {
    const page = await e19Browser.newPage({ viewport: { width: width + 40, height: 1300 } });
    const { f, fit } = await fitted(page, width, "generate_molecule", name, "", patch);
    await f.locator("[data-protein-viewer]").waitFor({ timeout: 30000 });
    if (name !== "antibody") await f.getByRole("tab", { name: "Scheme" }).click();
    await fit();
    const m = await stageOf(f);
    if (width === 860 && !patch && name === "trastuzumab") {
      const c = groß["cartoon-860"];
      check(m.stage.w === c.stage.w && m.stage.h === c.stage.h, `E19 Schema: dieselbe Fläche wie der Cartoon (${m.stage.w}×${m.stage.h})`);
      check(m.scheme && m.scheme.h >= 700, `E19 Schema 860px: gemalt ${m.scheme?.w}×${m.scheme?.h} (vorher ~330×300)`);
    }
    // Beschriftung „antigen-binding site“ frei: kein Schnitt mit dem gestrichelten
    // Rahmen des Fab-Arms, keine Überlappung mit anderen Texten, innerhalb der viewBox
    const frei = await f.evaluate(() => {
      const svg = document.querySelector("svg[data-igg-scheme]");
      const texts = [...svg.querySelectorAll("text")].filter((t) => !t.closest("g[transform]"));
      const label = texts.find((t) => t.textContent === "antigen-binding site");
      const b = label.getBBox(), pad = 2;
      const inBox = ([x, y], q) => x > q.x - pad && x < q.x + q.width + pad && y > q.y - pad && y < q.y + q.height + pad;
      const poly = svg.querySelector("[data-highlight] polygon");
      const rect = svg.querySelector("[data-highlight] rect");
      const num = (el, a) => Number(el.getAttribute(a));
      const pts = poly ? poly.getAttribute("points").trim().split(/\s+/).map((p) => p.split(",").map(Number))
        : rect ? [[num(rect, "x"), num(rect, "y")], [num(rect, "x") + num(rect, "width"), num(rect, "y")],
          [num(rect, "x") + num(rect, "width"), num(rect, "y") + num(rect, "height")], [num(rect, "x"), num(rect, "y") + num(rect, "height")]]
        : [];
      let rahmen = false;
      for (let i = 0; i < pts.length; i++) {
        const [a, c] = [pts[i], pts[(i + 1) % pts.length]];
        for (let k = 0; k <= 200; k++) if (inBox([a[0] + (c[0] - a[0]) * k / 200, a[1] + (c[1] - a[1]) * k / 200], b)) rahmen = true;
      }
      const überlappt = texts.filter((t) => t !== label).map((t) => [t.textContent, t.getBBox()])
        .filter(([, q]) => q.x < b.x + b.width && b.x < q.x + q.width && q.y < b.y + b.height && b.y < q.y + q.height).map(([s]) => s);
      const vb = svg.viewBox.baseVal;
      const drin = b.x >= vb.x && b.y >= vb.y && b.x + b.width <= vb.x + vb.width && b.y + b.height <= vb.y + vb.height;
      return { markierung: svg.getAttribute("data-igg-scheme"), rahmen, überlappt, drin };
    });
    check(!frei.rahmen && frei.überlappt.length === 0 && frei.drin,
      `E19 Schema ${shot} ${width}px: „antigen-binding site“ frei von Rahmen und Texten, ganz sichtbar (${JSON.stringify(frei)})`);
    await page.screenshot({ path: join(sizeShots, `e19-scheme-${shot}-${width}.png`), fullPage: true });
    await page.close();
  }
  await e19Browser.close();
  console.log("E19 Maße:", JSON.stringify(groß));

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

  // Welle 2: pH-Kurven und Speziesverteilung im echten Panel-Host.
  for (const [name, input, expectedLabels, curveCount] of [
    ["generate_titration_curve", { substance: "Phosphoric acid", pka_values: [2.15, 7.2, 12.35], c_acid: 0.1,
      v_acid_ml: 25, c_titrant: 0.1, indicator: { name: "Phenolphthalein", ph_range: [8.2, 10] } },
    ["EP 1", "EP 2", "EP 3", "Phenolphthalein", "pH 2.29 (pKa1 = 2.15)", "pH 11.86 (pKa3 = 12.35)"], 1],
    ["generate_titration_curve", { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1,
      v_acid_ml: 25, c_titrant: 0.1 }, ["EP", "pH = pKa = 4.76"], 1],
    ["generate_species_distribution", { substance: "Ibuprofen", pka_values: [4.4], labels: ["HA", "A−"] },
    ["HA", "A−"], 2],
    ["generate_species_distribution", { substance: "Phosphoric acid", pka_values: [2.15, 7.2, 12.35],
      labels: ["H3PO4", "H2PO4−", "HPO4²−", "PO4³−"] }, ["H3PO4", "H2PO4−", "HPO4²−", "PO4³−"], 4],
  ]) {
    const p = await browser.newPage({ viewport: { width: 530, height: 560 } });
    await p.setContent('<body style="margin:0"></body>');
    await p.addScriptTag({ path: out });
    const calls = [];
    await p.exposeFunction("__callTool", (req) => { calls.push(req); return client.callTool(req); });
    const f = await mount(p, name, input);
    await f.locator(".plot-svg svg").waitFor();
    const labels = await f.locator(".plot-svg svg text").allTextContents();
    check(expectedLabels.every((label) => labels.includes(label)), `${input.substance} ${name}: EP/Puffer/Indikator oder Spezies in echter SVG`);
    const curves = f.locator('.plot-svg g[id="axes_1"] > g[id^="line2d_"] > path[style*="stroke-width: 1.6"]');
    check(await curves.count() === curveCount, `${input.substance} ${name}: ${curveCount} echte Datenkurven`);
    if (input.indicator) check(await f.locator('.plot-svg path[style*="fill: #9467bd"]').count() > 0,
      "Phosphorsäure: Indikatorband ist als gefüllte Fläche gezeichnet");
    if (input.substance === "Acetic acid") {
      const centerX = (label) => f.locator(".plot-svg svg text").filter({ hasText: new RegExp(`^${label}$`) }).first()
        .evaluate((el) => { const b = el.getBoundingClientRect(); return b.x + b.width / 2; });
      check(Math.abs(await centerX("EP") - await centerX("25")) < 1, "Essigsäure: EP-Linie bei 25 mL");
    }
    const path = await f.locator('span[title$=".png"]').getAttribute("title");
    check(path.startsWith(join(wegwerfHome, "ChemDraw-Output", "diagramme") + "/") && existsSync(path),
      `${input.substance} ${name}: echte PNG-Datei in diagramme/`);
    await f.getByRole("button", { name: "Export as PNG" }).click();
    await f.getByRole("button", { name: /Saved:/ }).waitFor();
    check(calls.filter((req) => req.name === "save_png").length === 1, `${input.substance} ${name}: Export über save_png-Bridge`);
    const savedPath = (await f.getByRole("button", { name: /Saved:/ }).getAttribute("title")).replace(/^Saved: /, "");
    check(readFileSync(savedPath).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])), `${input.substance}: Exportdatei ist PNG`);
    await p.screenshot({ path: join(tmpdir(), `panel-host-wave2-ph-${name}-${input.substance.replaceAll(" ", "-")}.png`) });
    await p.close();
  }

  // Fund (b), Durchsicht 09.11.: ein echter Tool-Fehler (kaputtes SMILES) muss im
  // Panel lesbar landen, statt es auf „Waiting for data…“ stehen zu lassen.
  {
    const errorPage = await browser.newPage({ viewport: { width: 640, height: 400 } });
    await errorPage.setContent('<body style="margin:0"></body>');
    await errorPage.addScriptTag({ path: out });
    await errorPage.exposeFunction("__callTool", (req) => client.callTool(req));
    const gmTool = tools.find((t) => t.name === "generate_molecule");
    const input = { name_or_smiles: "C1CC" };
    const result = await client.callTool({ name: "generate_molecule", arguments: input });
    check(result.isError, "generate_molecule mit kaputtem SMILES liefert eine echte Fehlerantwort");
    const serverText = result.content.filter((b) => b.type === "text").map((b) => b.text).join(" ");
    const resource = await client.readResource({ uri: gmTool._meta.ui.resourceUri });
    await errorPage.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: input, toolResult: result });
    const ef = errorPage.frames().at(-1);
    const alert = ef.getByRole("alert");
    await alert.waitFor({ timeout: 5000 }).catch(() => {});
    const shown = (await ef.locator("body").innerText()).replace(/\s+/g, " ");
    const kern = serverText.replace(/^Error executing tool \S+: /, "").slice(0, 40);
    check(await alert.count() === 1 && shown.includes(kern),
      `Tool-Fehler steht lesbar im Panel („${kern}…“), Panel zeigte: „${shown.slice(0, 80)}“`);
    await errorPage.screenshot({ path: join(tmpdir(), "panel-host-tool-error.png") });
    // Fehler nach einem Erfolg ersetzt das alte Bild; Erfolg nach dem Fehler räumt die Meldung weg.
    const ok = await client.callTool({ name: "generate_molecule", arguments: { name_or_smiles: "CCO" } });
    check(!ok.isError, "generate_molecule CCO liefert eine echte Erfolgsantwort");
    await errorPage.evaluate((r) => window.__sendToolResult(r), ok);
    await ef.locator(".panel-title").first().waitFor({ timeout: 5000 }).catch(() => {});
    check(await ef.getByRole("alert").count() === 0 && await ef.locator(".panel-title").count() > 0,
      "Erfolg nach Tool-Fehler: Meldung weg, Struktur da");
    await errorPage.evaluate((r) => window.__sendToolResult(r), result);
    await ef.getByRole("alert").waitFor({ timeout: 5000 }).catch(() => {});
    check(await ef.getByRole("alert").count() === 1 && await ef.locator(".panel-title").count() === 0,
      "Tool-Fehler nach Erfolg: Meldung ersetzt das alte Ergebnis");
    await errorPage.close();
  }

  // Welle 2: calculate_ph ist absichtlich ein Text-Tool ohne Panel. Diese drei
  // echten MCP-Aufrufe prüfen pH, abwägbaren Pufferansatz und Ionisationsanteile.
  const calculatePh = tools.find((tool) => tool.name === "calculate_ph");
  check(calculatePh && !calculatePh._meta?.ui?.resourceUri,
    "calculate_ph ist registriert und bleibt ein Text-Tool ohne Panel-Ressource");
  for (const [topic, input, expected] of [
    ["weak_acid", { concentration: 0.1, pka: 4.76 },
      ["**pH = 2.88**", "Exact (charge balance)", "Textbook approximation", "pKa used: 4.76"]],
    ["buffer_recipe", { target_ph: 7.4, pka: 7.2, total_concentration: 0.1, volume_ml: 100 },
      ["Ratio base : acid = 1.58 : 1", "0.003869 mol", "0.006131 mol", "make up to 100 mL"]],
    ["ionisation", { pka: 4.4, target_ph: 6.5, drug_type: "acid" },
      ["Charged: 99.21 %", "Uncharged: 0.79 %", "10^(6.5 − 4.4)"]],
  ]) {
    const result = await client.callTool({ name: "calculate_ph", arguments: { topic, ...input } });
    check(!result.isError, `calculate_ph ${topic}: echter MCP-Aufruf erfolgreich`);
    const answer = result.content.filter((part) => part.type === "text").map((part) => part.text).join("\n");
    check(expected.every((text) => answer.includes(text)),
      `calculate_ph ${topic}: Textantwort enthält ${expected.join(", ")}`);
    check(!result.content.some((part) => part.type === "image") && !result._meta?.ui?.resourceUri,
      `calculate_ph ${topic}: Antwort bleibt Text ohne Panel oder eingebettetes Bild`);
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

  // 3d2. 3D-Knopf (Plan Punkt 6, 07.11.): generate_3d per Bridge, Viewer ersetzt die Zeichnung, Rückweg per Klick
  const vor3d = serverCalls.length;
  const breite2d = (await frame.locator(".structure-canvas").boundingBox())?.width ?? 0;
  await frame.getByRole("button", { name: "3D", exact: true }).click();
  await frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 15000 });
  // Jay 07.11.: 3D größer — die Kuhle nimmt die volle Panelbreite, die Kernwerte rutschen darunter
  const box3d = (await frame.locator("[data-view-3d]").boundingBox()) ?? { width: 0, height: 0 };
  prüfe(await frame.locator(".structure-layout[data-layout-3d]").count() === 1 && box3d.width >= breite2d && box3d.height > 320 * 1.3,
    `3D-Kuhle nutzt die Panelbreite als Quadrat (2D ${Math.round(breite2d)}×320 px → 3D ${Math.round(box3d.width)}×${Math.round(box3d.height)} px)`);
  prüfe(serverCalls.slice(vor3d).join() === "generate_3d", "3D-Knopf ruft generate_3d über die Bridge");
  prüfe(await frame.locator("[data-view-3d] svg circle").count() > 10 && await frame.locator(".structure-drawing").count() === 0,
    "3D-Viewer mit Atomen steht an Stelle der 2D-Zeichnung");
  // E3 (Design-Kritik 3.14), bewusst umgedreht: hier stand „Export PNG pausiert im 3D-Modus“ —
  // der Knopf hätte die 2D-Zeichnung exportiert. Jetzt rastert er das Kuhlen-SVG in der aktuellen
  // Drehlage. Nur dieser Lauf kann zeigen, dass die Theme-Variablen (var(--bowl-*)) im Export
  // aufgelöst sind: jsdom rechnet kein var(). Ungelöst wäre die Kuhle schwarz.
  prüfe(await frame.getByRole("button", { name: "Export as PNG" }).count() === 1, "Export PNG bleibt im 3D-Modus");
  prüfe(await frame.locator("[data-testid='panel-footer'] .panel-footer-path").first().getAttribute("title").then((t) => t?.endsWith(".sdf")),
    "3D-Fußzeile zeigt den SDF-Pfad des Konformers");
  await page.emulateMedia({ colorScheme: "light" });
  const vorExport3d = serverCalls.length;
  await frame.getByRole("button", { name: "Export as PNG" }).click();
  await frame.getByRole("button", { name: /Saved:/ }).waitFor({ timeout: 15000 });
  prüfe(serverCalls.slice(vorExport3d).join() === "save_png", "3D-Export ruft save_png genau einmal über die Bridge");
  const pfad3d = (await frame.getByRole("button", { name: /Saved:/ }).getAttribute("title")).replace(/^Saved: /, "");
  const png3d = readFileSync(pfad3d);
  prüfe(pfad3d.startsWith(join(wegwerfHome, "ChemDraw-Output", "png") + "/") && png3d.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])),
    `3D-Export schreibt eine echte PNG-Datei nach png/ (${pfad3d})`);
  const rückmeldung3d = await frame.locator("[data-testid='panel-footer'] .export-feedback").innerText();
  prüfe(rückmeldung3d.startsWith("Saved: ") && rückmeldung3d.includes("ChemDraw-Output/png/"), `Fußzeile meldet sichtbar: ${rückmeldung3d}`);
  // Pixel am linken Kuhlenrand (x = 20/480, y = Mitte): heller Verlauf, nicht Schwarz.
  const randLum = await page.evaluate(async (b64) => {
    const img = new Image();
    img.src = `data:image/png;base64,${b64}`;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.width; c.height = img.height;
    const ctx = c.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const [r, g, b] = ctx.getImageData(Math.round(img.width * 20 / 480), Math.round(img.height / 2), 1, 1).data;
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  }, png3d.toString("base64"));
  prüfe(randLum > 0.6, `3D-Export: Kuhle mit aufgelösten Theme-Farben (Rand-Luminanz ${randLum.toFixed(2)})`);
  await page.screenshot({ path: join(tmpdir(), "panel-host-3d-export.png") });
  await page.emulateMedia({ colorScheme: "dark" }); // Folgebilder wie bisher im dunklen Schema
  // E2 (Design-Kritik Rang 3): eine Ansicht-Achse direkt unter der Kuhle, Stereo und Gruppen in 3D aus
  const achse = (await frame.locator("[data-view-axis]").boundingBox()) ?? { y: Infinity };
  const kuhle = (await frame.locator("[data-view-3d]").boundingBox()) ?? { y: 0, height: 0 };
  const fakten = (await frame.locator(".key-facts").boundingBox()) ?? { y: 0 };
  const abstand = achse.y - (kuhle.y + kuhle.height);
  prüfe(await frame.locator("[data-view-axis]").count() === 1 && await frame.locator(".structure-tools").count() === 0
    && abstand >= 0 && abstand <= 24 && achse.y < fakten.y,
    `Ansicht-Achse sitzt ${Math.round(abstand)} px unter der Kuhle, vor den Kernwerten — genau eine Reihe`);
  prüfe(await frame.locator("[data-testid='stereo-note']").count() === 0 && await frame.locator(".group-section").count() === 0,
    "3D blendet Stereo-Zeile und Gruppen-Chips aus");
  await page.waitForTimeout(1300); // Einblend-Drehung abgeschlossen, Bild zeigt die Ruhelage
  await page.screenshot({ path: join(tmpdir(), "panel-host-3d-button.png") });
  await frame.getByRole("button", { name: "3D", exact: true }).click();
  await frame.locator(".structure-drawing").waitFor({ timeout: 5000 });
  prüfe(await frame.locator("[data-testid='stereo-note']").count() === 1 && await frame.locator(".group-section").count() === 1,
    "Zurück in 2D: Stereo-Zeile und Gruppen-Chips wieder da");
  prüfe(await frame.locator(".structure-layout[data-layout-3d]").count() === 0, "Zurück in 2D: Kernwerte wieder neben der Zeichnung");
  await frame.getByRole("button", { name: "3D", exact: true }).click();
  await frame.locator("[data-view-3d]").waitFor({ timeout: 5000 });
  prüfe(serverCalls.slice(vor3d).filter((n) => n === "generate_3d").length === 1, "Zweiter 3D-Klick kommt aus dem Cache (save_png des 3D-Exports zählt nicht)");
  await frame.getByRole("button", { name: "3D", exact: true }).click();
  await frame.locator(".structure-drawing").waitFor({ timeout: 5000 });

  // 3e. Fischer/Haworth (Etappe 4): Knopf nur bei passenden Stoffen, Zeichnung per Klick
  prüfe(!(await frame.getByRole("button", { name: "Fischer", exact: true }).count()) && !(await frame.getByRole("button", { name: "Haworth" }).count()),
    "Methylphenidate hat keinen Projektionsknopf");
  // Seit 41da7c4 (OPSIN-Treffer gegen PubChem geprüft) liefert "D-glucose" den PubChem-Record,
  // also den Pyranosering → Haworth; die offene Kette (Fischer) heißt jetzt "aldehydo-D-glucose".
  // Seit E17 (10.11.2026) hat auch der Ringzucker einen Fischer-Knopf: die lokal hergeleitete offene Form.
  for (const [stoff, knopf, fehlt, soll] of [["aldehydo-D-glucose", "Fischer", "Haworth", "CHO"], ["beta-D-glucose", "Haworth", null, "CH2OH"]]) {
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
    await f.getByRole("button", { name: knopf, exact: true }).click();
    await f.locator(".structure-drawing svg text").first().waitFor({ timeout: 5000 });
    const labels = await f.locator(".structure-drawing svg text").allTextContents();
    prüfe(labels.includes(soll) && (fehlt === null || !(await f.getByRole("button", { name: fehlt, exact: true }).count())),
      `${stoff}: ${knopf} zeigt ${labels.length} Beschriftungen (${soll} dabei)${fehlt ? `, kein ${fehlt}-Knopf` : ""}`);
    if (knopf === "Haworth") {
      // Befund 10.11.2026: der Satz zur offenen Kette gehört unter Fischer, nicht unter Haworth.
      // „anomeric configuration“ steht nur im Satz, nicht in der Unterschrift der Zeichnung.
      prüfe(!(await f.locator("body").innerText()).includes("anomeric configuration"), `${stoff}: unter Haworth kein Fischer-Satz`);
      await f.getByRole("button", { name: "Fischer", exact: true }).click();
      await f.locator(".structure-drawing svg text", { hasText: "open-chain form" }).waitFor({ timeout: 5000 });
      const offen = await f.locator(".structure-drawing svg text").allTextContents();
      prüfe(offen.includes("CHO") && offen.includes("open-chain form"), `${stoff}: Fischer zeigt die offene Form (CHO, Unterschrift)`);
      prüfe((await f.locator("body").innerText()).includes("anomeric configuration"), `${stoff}: Satz zur offenen Form steht unter Fischer`);
      await f.getByRole("button", { name: "Haworth" }).click();
      await f.locator(".structure-drawing svg text", { hasText: "CH2OH" }).first().waitFor({ timeout: 5000 }).catch(() => {});
    }
    await p.emulateMedia({ colorScheme: "dark" });
    const fill = await f.evaluate(() => getComputedStyle(document.querySelector(".structure-drawing svg text")).fill);
    prüfe(fill !== "rgb(0, 0, 0)", `${stoff}: Beschriftung im Dunkelmodus hell (${fill})`);
    await p.screenshot({ path: join(tmpdir(), `panel-host-${knopf.toLowerCase()}.png`) });
    await p.close();
  }

  // 3f. Modell setzt view selbst (Befund Desktop 26.10.): Panel startet auf Haworth, mit Titel und Knöpfen;
  // der Satz zur offenen Kette steht seit 10.11.2026 unter Fischer (der Knopf ist seit E17 da)
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
    prüfe(body.includes("β-D-Glucopyranose") && !body.includes("anomeric configuration")
      && await f.getByRole("button", { name: "All H" }).count() === 1 && await f.getByRole("button", { name: "Fischer", exact: true }).count() === 1,
      "view=haworth vom Modell: Panel startet auf Haworth, mit Titel, All-H- und Fischer-Knopf, ohne Fischer-Satz");
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
  await cmpPage.close();

  // Desktop-Befund 02.11.2026: im Dunkelmodus färbte die globale RDKit-Umfärbung
  // das gemeinsame Gerüst hell — auf dem bewusst weißen Bildgrund fast unsichtbar.
  const cmpDark = await browser.newPage({ viewport: { width: 720, height: 600 }, colorScheme: "dark" });
  await cmpDark.setContent("<body></body>");
  await cmpDark.addScriptTag({ path: out });
  await cmpDark.evaluate((a) => window.__startHost(a), { html: cmpHtml, toolInput: cmpInput, toolResult: cmpResult });
  const darkFrame = cmpDark.frames().find((f) => f !== cmpDark.mainFrame());
  await darkFrame.locator(".plot-svg svg").waitFor();
  const scaffold = await darkFrame.evaluate(() => {
    const lum = (c) => { const m = c.match(/\d+(\.\d+)?/g); if (!m) return 1; const [r, g, b] = m.map(Number); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; };
    const paths = [...document.querySelectorAll('.plot-svg svg path[style*="stroke:#000000"]')];
    const texts = [...document.querySelectorAll('.plot-svg svg text[fill="#000000"], .plot-svg svg path[fill="#000000"]')];
    return {
      n: paths.length,
      maxStroke: Math.max(0, ...paths.map((p) => lum(getComputedStyle(p).stroke))),
      maxFill: Math.max(0, ...texts.map((t) => lum(getComputedStyle(t).fill))),
      bg: lum(getComputedStyle(document.querySelector(".plot-svg")).backgroundColor),
    };
  });
  check(scaffold.n > 0 && scaffold.bg > 0.9 && scaffold.maxStroke < 0.5 && scaffold.maxFill < 0.5,
    `Vergleich dunkel: Gerüst dunkel auf weißem Grund (${scaffold.n} Pfade, Strich ${scaffold.maxStroke.toFixed(2)}, Schrift ${scaffold.maxFill.toFixed(2)})`);
  await cmpDark.close();

  // E16 (10.11.2026): (1) Abkürzungs-Labels (Boc, Ph, CO2H) standen im dunklen
  // Schema fast schwarz auf dunklem Grund — RDKit zeichnet Dummy-Atome in #191919.
  // (2) Große Strukturen im Reaktions-Panel waren so klein, dass man N/O nicht lesen konnte.
  // Gemessen wird, was der Nutzer sieht: berechnete Farbe gegen den Kartengrund und die
  // gerenderte Glyphenhöhe in CSS-px, bei Desktop-Panelbreite (≈930 px).
  {
    const PORPHYRIN = {
      reactants: ["CC1=C(CCC(=O)O)C2=CC3=C(CCC(=O)O)C(C)=C(N3)C=C4C(C)=C(C=C)C(=N4)C=C5C(C=C)=C(C)C(=N5)C=C1N2", "[Fe+2]"], products: ["CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)O)C)CCC(=O)O.[Fe+2]", "[H+]"], coefficients: [1, 1, 1, 2],
      conditions: "ferrochelatase", name: "Protoporphyrin IX → heme b",
    };
    const open = async (name, input, colorScheme, width = 930) => {
      const p = await browser.newPage({ viewport: { width: width + 20, height: 1400 }, colorScheme });
      await p.setContent('<body style="margin:0"></body>');
      await p.addScriptTag({ path: out });
      await p.exposeFunction("__callTool", (req) => client.callTool(req));
      const f = await mount(p, name, input);
      await p.locator("iframe").last().evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1380px"; }, width);
      await f.locator("svg").first().waitFor();
      await p.waitForTimeout(400);
      return [p, f];
    };
    // Kontrast der Kürzel: mittlere Helligkeit der Label-Glyphen gegen den Grund ihrer Karte.
    const labelContrast = (f) => f.evaluate(() => {
      const lum = (c) => { const m = c.match(/\d+(\.\d+)?/g); if (!m) return 0; const [r, g, b] = m.map(Number); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; };
      const glyphs = [...document.querySelectorAll('svg path[fill="#191919"]')].filter((el) => el.getAttribute("d"));
      const bgOf = (el) => { for (let n = el; n; n = n.parentElement) { const c = getComputedStyle(n).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return lum(c); } return 1; };
      const vals = glyphs.map((g) => Math.abs(lum(getComputedStyle(g).fill) - bgOf(g)));
      return { n: glyphs.length, min: Math.min(...vals) };
    });
    for (const colorScheme of ["light", "dark"]) {
      for (const [what, name, input] of [
        ["Boc/Ph", "generate_molecule", { name_or_smiles: "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1", abbreviate_groups: true }],
        ["CO2H (Porphyrin)", "generate_reaction", { ...PORPHYRIN, abbreviate_groups: true }],
      ]) {
        const [p, f] = await open(name, input, colorScheme);
        const c = await labelContrast(f);
        check(c.n > 0 && c.min > 0.45, `${colorScheme}: Kürzel ${what} heben sich vom Grund ab (${c.n} Glyphen, Kontrast min ${c.min.toFixed(2)})`);
        await p.close();
      }
    }
    // Lesbare Atomlabels in großen Reaktionen: kleinste gerenderte N-Glyphe ≥ 9 px hoch.
    const [p, f] = await open("generate_reaction", PORPHYRIN, "dark");
    const labelPx = await f.evaluate(() => Math.min(...[...document.querySelectorAll('.reaction-panel svg path[fill="#0000FF"]')]
      .filter((el) => el.getAttribute("d")).map((el) => el.getBoundingClientRect().height)));
    check(labelPx >= 9, `Reaktion Porphyrin: N-Labels ${labelPx.toFixed(1)} px hoch (≥ 9 px)`);
    check(await f.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Reaktion Porphyrin: kein horizontales Abschneiden");
    await p.close();
    // Gestapelt ↔ nebeneinander darf nicht pendeln: ohne Bedingungen ist der senkrechte Pfeil
    // ~116 px schmaler als der waagrechte — misst die Entscheidung den gerade gezeigten Pfeil,
    // gibt es ein Breitenband, in dem jeder Zustand für den anderen stimmt.
    {
      const [sp, sf] = await open("generate_reaction", { reactants: [PORPHYRIN.reactants[0]], products: [PORPHYRIN.products[0]] }, "light");
      const iframe = sp.locator("iframe").last();
      const flips = [];
      for (let w = 700; w <= 1100; w += 10) {
        await iframe.evaluate((el, px) => { el.style.width = `${px}px`; }, w);
        await sp.waitForTimeout(120);
        const seen = new Set();
        for (let i = 0; i < 4; i++) {
          seen.add(await sf.evaluate(() => Boolean(document.querySelector("[data-stacked]"))));
          await sp.waitForTimeout(40);
        }
        if (seen.size > 1) flips.push(w);
      }
      check(flips.length === 0, `Reaktion ohne Bedingungen: Stapeln pendelt nicht (${flips.length ? flips.join(", ") + " px" : "700–1100 px stabil"})`);
      await sp.close();
    }
  }

  // Release 0.7.0 (02.11.2026): die beiden Panel-Tools ohne Host-Fall.
  const rxnPage = await browser.newPage({ viewport: { width: 720, height: 600 } });
  await rxnPage.setContent('<body style="margin:0"></body>');
  await rxnPage.addScriptTag({ path: out });
  await rxnPage.exposeFunction("__callTool", (req) => client.callTool(req));
  const rxn = await mount(rxnPage, "generate_reaction", {
    reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification",
  });
  await rxn.locator('[data-testid="balance-badge"]').waitFor();
  check(await rxn.locator(".reaction-panel").getByText("Fischer esterification").count() > 0, "Reaktion: Titel sichtbar");
  check(await rxn.locator(".reaction-panel svg").count() >= 5, "Reaktion: vier Strukturen und ein Pfeil gezeichnet");
  check(await rxn.locator('[data-testid="balance-badge"]').getAttribute("data-state") === "balanced", "Reaktion: Bilanz ausgeglichen");
  check((await rxn.locator("body").innerText()).includes("H2SO4") || (await rxn.locator("body").innerText()).includes("H₂SO₄"), "Reaktion: Bedingung am Pfeil");
  // E3: Reaktion hat jetzt Pfad und Export in der Fußzeile; exportiert wird die zusammengesetzte Gleichung.
  // Fund (c), Durchsicht 09.11.: nach Verkleinern und wieder Verbreitern des Panels muss
  // die Reaktionszeile zur alten Größe zurückwachsen, nicht geschrumpft stehen bleiben.
  {
    const rowScale = () => rxn.evaluate(() => {
      const row = [...document.querySelectorAll(".reaction-panel div")].find((el) => el.style.transformOrigin.includes("left"));
      const m = /scale\(([\d.]+)\)/.exec(row?.style.transform ?? "");
      // transform "none" heißt Scroll-Modus (unter MIN_SCALE) — als 0 melden, nicht als 1.
      return m ? Number(m[1]) : (row ? 0 : NaN);
    });
    const setWidth = async (w) => {
      await rxnPage.locator("iframe").last().evaluate((el, px) => { el.style.width = `${px}px`; }, w);
      await rxnPage.waitForTimeout(400);
    };
    await setWidth(510);
    const vorher = await rowScale();
    await setWidth(420);
    const schmal = await rowScale();
    await setWidth(510);
    const zurueck = await rowScale();
    await setWidth(1400);
    const breit = await rowScale();
    console.log(`Reaktion-Skalierung: 510px ${vorher} → 420px ${schmal} → 510px ${zurueck} → 1400px ${breit}`);
    check(schmal > 0 && schmal < vorher, `Reaktion: schmaleres Panel verkleinert die Zeile (${vorher} → ${schmal})`);
    check(Math.abs(zurueck - vorher) < 0.01, `Reaktion: zurück auf 510px wächst die Zeile zurück (${schmal} → ${zurueck}, erwartet ${vorher})`);
    check(breit >= vorher, `Reaktion: im breiten Panel nicht kleiner als vorher (${breit})`);
    await setWidth(510);
  }
  const rxnPfad = await rxn.locator("[data-testid='panel-footer'] .panel-footer-path").first().getAttribute("title");
  check(rxnPfad?.endsWith(".png") && existsSync(rxnPfad), "Reaktion: Fußzeile zeigt die echte PNG-Datei");
  await rxnPage.screenshot({ path: join(tmpdir(), "panel-host-reaction-footer.png") });
  await rxn.getByRole("button", { name: "Export as PNG" }).click();
  await rxn.getByRole("button", { name: /Saved:/ }).waitFor({ timeout: 15000 });
  const rxnExport = (await rxn.getByRole("button", { name: /Saved:/ }).getAttribute("title")).replace(/^Saved: /, "");
  check(readFileSync(rxnExport).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])), "Reaktion: Export schreibt eine echte PNG-Datei");
  check((await rxn.locator("[data-testid='panel-footer'] .export-feedback").innerText()).startsWith("Saved: "), "Reaktion: sichtbare Rückmeldung nach Export");
  await rxnPage.screenshot({ path: join(tmpdir(), "panel-host-reaction-export.png") });
  await rxnPage.close();

  // M2 (12.11.2026): Claude Desktop zeigt kein Panel, wenn ein Ergebnis rund
  // 150.000 Zeichen überschreitet. Der Server hält bei großen Ergebnissen die
  // Bilder zurück (result_budget.py), das Panel lädt sie per load_panel_part nach —
  // auch dann, wenn der Host structuredContent weglässt (Desktop, Juli 2026).
  {
    const ARZNEISTOFFE = [
      "CC(=O)Oc1ccccc1C(=O)O", "Cn1c(=O)c2c(ncn2C)n(C)c1=O", "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
      "COc1ccc2cc(ccc2c1)C(C)C(=O)O", "CC(=O)Nc1ccc(O)cc1", "CN1CCC[C@H]1c1cccnc1",
      "CN1C2CCC1C(C(=O)OC)C(OC(=O)c1ccccc1)C2", "CC(C)NCC(O)COc1cccc2ccccc12",
      "CN1CCC23C4C1CC5=C2C(=C(C=C5)OC)OC3C(C=C4)O", "CN(C)CCCN1c2ccccc2CCc2ccccc21",
      "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl", "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21",
      "NC(=O)N1c2ccccc2C=Cc2ccccc21", "CC12CCC3C(CCC4=CC(=O)CCC34C)C1CCC2O",
      "CC(C)(C)NCC(O)c1ccc(O)c(CO)c1", "COc1ccc(cc1)C(=O)c1ccccc1", "Clc1ccc(cc1)C(c1ccccc1)N1CCN(CC1)CCOCC(=O)O",
      "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O", "CN1CCN(CC1)C1=Nc2ccccc2Nc2ccc(C)cc21",
      "OCC(O)C1OC(=O)C(O)=C1O",
    ];
    const VANCOMYCIN = "C[C@H]1[C@H]([C@@](C[C@@H](O1)O[C@@H]2[C@H]([C@@H]([C@H](O[C@H]2OC3=C4C=C5C=C3OC6=C(C=C(C=C6)"
      + "[C@H]([C@H](C(=O)N[C@H](C(=O)N[C@H]5C(=O)N[C@@H]7C8=CC(=C(C=C8)O)C9=C(C=C(C=C9O)O)[C@H]"
      + "(NC(=O)[C@H]([C@@H](C1=CC(=C(O4)C=C1)Cl)O)NC7=O)C(=O)O)CC(=O)N)NC(=O)[C@@H](CC(C)C)NC)O)Cl)"
      + "CO)O)O)(C)N)O";
    const faelle = [
      { label: "Stapel mit 20 Arzneistoffen, ohne structuredContent", tool: "batch_generate",
        input: { molecules: ARZNEISTOFFE }, strip: true, karten: 20 },
      { label: "Vancomycin", tool: "generate_molecule", input: { name_or_smiles: VANCOMYCIN }, strip: false, karten: 1 },
    ];
    for (const fall of faelle) {
      const p = await browser.newPage({ viewport: { width: 720, height: 900 } });
      await p.setContent('<body style="margin:0"></body>');
      await p.addScriptTag({ path: out });
      const calls = [];
      await p.exposeFunction("__callTool", (req) => { calls.push(req.name); return client.callTool(req); });
      const result = await client.callTool({ name: fall.tool, arguments: fall.input });
      const groesse = JSON.stringify(result).length;
      check(!result.isError && result.structuredContent?._deferred && groesse <= 120000,
        `${fall.label}: Ergebnis hält Bilder zurück und bleibt bei ${groesse.toLocaleString("de-DE")} Zeichen`);
      const toolResult = fall.strip ? { content: result.content, isError: result.isError } : result;
      const tool = tools.find((t) => t.name === fall.tool);
      const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
      await p.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: fall.input, toolResult });
      const f = p.frames().at(-1);
      await f.locator(".panel-title").nth(fall.karten - 1).waitFor({ timeout: 30000 }).catch(() => {});
      const bilder = await f.locator(".panel-title").count();
      const pfade = await f.locator("svg path").count();
      check(bilder === fall.karten && pfade > 50 * fall.karten && calls.includes("load_panel_part")
        && calls.every((n) => n === "load_panel_part"),
        `${fall.label}: Panel lädt ${calls.length}× nach und zeigt ${bilder} Karte(n) mit ${pfade} Pfaden`);
      await p.screenshot({ path: join(tmpdir(), `panel-host-m2-${fall.tool}.png`) });
      await p.close();
    }
  }

  const batchPage = await browser.newPage({ viewport: { width: 720, height: 900 } });
  await batchPage.setContent('<body style="margin:0"></body>');
  await batchPage.addScriptTag({ path: out });
  await batchPage.exposeFunction("__callTool", (req) => client.callTool(req));
  const batch = await mount(batchPage, "batch_generate", { molecules: ["benzene", "toluene", "phenol"] });
  await batch.locator(".panel-title").nth(2).waitFor();
  const titles = (await batch.locator(".panel-title").allInnerTexts()).map((t) => t.toLowerCase());
  check(["benzene", "toluene", "phenol"].every((n) => titles.some((t) => t.includes(n))), `Batch: drei Molekülkarten (${titles.join(", ")})`);
  check(await batch.locator("button.export-png").count() === 3, "Batch: je Molekül ein Export-Knopf");
  await batchPage.close();
} finally {
  await browser?.close();
  await client.close();
}
