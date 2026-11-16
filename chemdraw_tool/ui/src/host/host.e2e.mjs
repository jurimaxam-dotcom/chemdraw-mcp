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

    // Etappe 5 (16.11.2026): Mechanismus-Übersicht ohne Rollbereich im Rollbereich. Vorher eine
    // Spalte in einer Karte mit eigenem Rollbalken — im Chat bei 1000 px waren zwei von drei
    // SN2-Schritten zu sehen. Jetzt nebeneinander, Maßstab ≥ 0,62 px je viewBox-Einheit.
    {
      const SN2 = { reaction_type: "sn2", substrates: ["C[C@@H](Br)CC", "[C-]#N"] };
      const FISCHER = { reaction_type: "fischer_ester", substrates: ["CCCCCCCCCCCCCCCCCC(=O)O", "CCO"] };
      const uebersicht = (f) => f.evaluate(() => {
        const tiles = [...document.querySelectorAll("[aria-label^='Open step']")].map((t) => {
          const b = t.getBoundingClientRect(), svg = t.querySelector("svg"), vb = svg.viewBox.baseVal;
          return { top: Math.round(b.top), bottom: Math.round(b.bottom), left: Math.round(b.left), right: Math.round(b.right),
            massstab: +(svg.getBoundingClientRect().width / vb.width).toFixed(2) };
        });
        const stage = document.querySelector(".mech-stage").getBoundingClientRect();
        const inner = [...document.querySelectorAll(".mechanism-panel *")].filter((el) => {
          const cs = getComputedStyle(el);
          return /auto|scroll/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 1;
        }).map((el) => el.className);
        const de = document.documentElement;
        return { tiles, inner, stageBottom: Math.round(stage.bottom), sh: de.scrollHeight, ih: innerHeight, sw: de.scrollWidth, iw: innerWidth,
          sub: document.querySelector(".panel-subtitle")?.textContent };
      });
      {
        const [page, f] = await open("generate_mechanism", SN2, chat(1000), { viewport: { width: 1000, height: 1300 } });
        await f.getByRole("tab", { name: "Overview", exact: true }).waitFor();
        await fitChat(page);
        const u = await uebersicht(f);
        const h = await page.evaluate(() => window.__panelSizes.at(-1)?.height);
        messwerte["e5-mech-chat1000"] = JSON.stringify({ ...u, h });
        check(u.tiles.length === 3 && new Set(u.tiles.map((t) => t.top)).size === 1, `E5 Mechanismus Chat 1000: drei Schritte nebeneinander (${JSON.stringify(u.tiles)})`);
        check(u.tiles.every((t) => t.massstab >= 0.62 && t.bottom <= u.stageBottom), `E5 Mechanismus Chat 1000: jeder Schritt ganz sichtbar, Maßstab ≥ 0,62 (${JSON.stringify(u.tiles)})`);
        check(u.inner.length === 0 && h <= 700, `E5 Mechanismus Chat 1000: kein innerer Rollbereich, Panel ${h} ≤ 700 px (${u.inner})`);
        check(u.sub === "3 steps", `E5 Mechanismus: Untertitel lesbar statt Rohwert („${u.sub}“)`);
        await f.locator("[aria-label^='Open step 2']").click();
        check(await f.getByRole("tab", { name: "Step by step", exact: true }).getAttribute("aria-selected") === "true"
          && /Step 2 \/ 3/.test(await f.locator("body").innerText()), "E5 Mechanismus: Klick auf Schritt 2 öffnet ihn in Step by step");
        await page.close();
      }
      for (const [w, h] of [[1000, 700], [320, 700]]) {
        const [page, f] = await open("generate_mechanism", SN2, full(w, h), { viewport: { width: w, height: h } });
        await f.getByRole("tab", { name: "Overview", exact: true }).waitFor();
        await page.waitForTimeout(400);
        const u = await uebersicht(f);
        messwerte[`e5-mech-${w}x${h}`] = JSON.stringify(u);
        if (w === 1000) {
          check(new Set(u.tiles.map((t) => t.top)).size === 1 && u.tiles.every((t) => t.massstab >= 0.62) && u.sh <= u.ih,
            `E5 Mechanismus 1000×700: nebeneinander, lesbar, ohne Rollen (${JSON.stringify(u)})`);
        } else {
          check(u.tiles.every((t, i) => i === 0 || t.top > u.tiles[i - 1].bottom) && u.sw <= u.iw && u.inner.length === 0,
            `E5 Mechanismus 320×700: untereinander, nichts ragt seitlich heraus, kein innerer Rollbereich (${JSON.stringify(u)})`);
        }
        await page.close();
      }
      // Fischer, acht Schritte: passt lesbar nicht in 700 px — mehrere je Zeile, das Panel wächst statt zu rollen.
      {
        const [page, f] = await open("generate_mechanism", FISCHER, chat(1000), { viewport: { width: 1000, height: 1300 } });
        await f.getByRole("tab", { name: "Overview", exact: true }).waitFor();
        await page.waitForTimeout(500);
        await fitChat(page);
        const u = await uebersicht(f);
        u.gemeldet = await page.evaluate(() => window.__panelSizes.map((s) => s.height));
        messwerte["e5-mech-fischer-chat1000"] = JSON.stringify(u);
        check(u.tiles.length === 8 && new Set(u.tiles.map((t) => t.top)).size < 8 && u.tiles.every((t) => t.massstab >= 0.62 && t.bottom <= u.stageBottom)
          && u.inner.length === 0 && u.sh <= u.ih + 1, `E5 Fischer Chat 1000: alle acht Schritte ganz sichtbar, mehrere je Zeile, kein innerer Rollbereich (${JSON.stringify(u)})`);
        check(await f.locator("[data-arrow='equilibrium']").count() === 7, "E5 Fischer: sieben ⇌ zwischen acht Schritten");
        await page.close();
      }
    }

    // Etappe 5: Anki-Panel mit Kartenvorschau — Bilder als data-URI laden unter der CSP des Hosts,
    // der Pfad hat einen Kopierknopf, und es gibt keinen Knopf, der Anki startet oder ändert.
    {
      const DECK = { deck_name: "Koffein und Paracetamol", deliver: "apkg", cards: [
        { front: { structure: "Cn1c(=O)c2c(ncn2C)n(C)c1=O" }, back: { text: "<b>Koffein</b><br>Methylxanthin" } },
        { front: { text: "Welcher Wirkstoff?" }, back: { text: "Paracetamol", structure: "CC(=O)Nc1ccc(O)cc1" } }] };
      const [page, f] = await open("export_anki_deck", DECK, chat(1000), { viewport: { width: 1000, height: 1300 } });
      await f.locator("[data-anki-card]").first().waitFor();
      await fitChat(page);
      const a = await f.evaluate(() => ({
        karten: document.querySelectorAll("[data-anki-card]").length,
        bilder: [...document.querySelectorAll("[data-anki-card] img")].map((i) => i.complete && i.naturalWidth > 0),
        sub: document.querySelector(".panel-subtitle")?.textContent,
        knoepfe: [...document.querySelectorAll("button")].map((b) => b.getAttribute("aria-label") || b.textContent.trim()),
        fuss: document.querySelector("[data-testid='panel-footer']")?.textContent,
      }));
      messwerte["e5-anki"] = JSON.stringify(a);
      check(a.karten === 2 && a.bilder.length === 2 && a.bilder.every(Boolean), `E5 Anki: zwei Karten mit Vorder-/Rückseite, beide Bilder geladen (${JSON.stringify(a.bilder)})`);
      check(/^2 cards/.test(a.sub) && /APKG/.test(a.fuss) && /ChemDraw-Output\/anki\//.test(a.fuss), `E5 Anki: Kartenzahl und .apkg-Pfad (${a.sub})`);
      check(a.knoepfe.every((k) => ["Copy path", "Expand"].includes(k)), `E5 Anki: nur Kopieren/Expand, kein Knopf, der Anki startet (${a.knoepfe})`);
      await page.close();
    }

    // Etappe 5: Protein im Chat ≤ 700 px (vorher 1171 px, die Fläche ein Quadrat bis 720 px),
    // bei 1000×700 kein Rollen (vorher 11 px); der Bedienhinweis steht unter der Fläche, nicht im Kopf.
    {
      const TRASTUZUMAB = { name: "trastuzumab" };
      const [page, f] = await open("generate_protein_or_antibody", TRASTUZUMAB, chat(1000), { viewport: { width: 1000, height: 1300 } });
      await f.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 });
      await fitChat(page);
      const h = await page.evaluate(() => window.__panelSizes.at(-1)?.height);
      const p = await f.evaluate(() => ({ sub: document.querySelector(".panel-subtitle")?.textContent,
        hinweis: document.querySelector("[data-protein-viewer] + .protein-hint")?.textContent,
        sh: document.documentElement.scrollHeight, ih: innerHeight }));
      messwerte["e5-protein-chat1000"] = JSON.stringify({ h, ...p });
      check(h <= 700 && p.sh <= p.ih + 1, `E5 Protein Chat 1000: Panel ${h} ≤ 700 px`);
      check(!/drag/i.test(p.sub) && /^Drag to rotate/.test(p.hinweis || ""), `E5 Protein: Untertitel ohne Bedienhinweis, Hinweis unter der Fläche (${p.sub} | ${p.hinweis})`);
      await page.close();
      const [page2, f2] = await open("generate_protein_or_antibody", TRASTUZUMAB, full(1000, 700), { viewport: { width: 1000, height: 700 } });
      await f2.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 });
      await page2.waitForTimeout(400);
      const g = await f2.evaluate(() => ({ sh: document.documentElement.scrollHeight, ih: innerHeight,
        stage: Math.round(document.querySelector("[data-protein-viewer]").getBoundingClientRect().height) }));
      messwerte["e5-protein-1000x700"] = JSON.stringify(g);
      check(g.sh <= g.ih && g.stage >= 240, `E5 Protein 1000×700: kein Rollen, Fläche ${g.stage} px (${JSON.stringify(g)})`);
      await page2.close();
    }

    // Etappe 5: Datenblatt bei 1000×700 ohne Rollen (vorher 713 px).
    {
      const [page, f] = await open("lookup_molecule_data", { name: "paracetamol" }, full(1000, 700), { viewport: { width: 1000, height: 700 } });
      await f.getByText("103-90-2").first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(300);
      const g = await f.evaluate(() => ({ sh: document.documentElement.scrollHeight, ih: innerHeight }));
      messwerte["e5-datenblatt-1000x700"] = JSON.stringify(g);
      check(g.sh <= g.ih, `E5 Datenblatt 1000×700: kein Rollen (${g.sh} in ${g.ih})`);
      await page.close();
    }

    // Etappe 6 (16.11.2026, Handlauf in Desktop): nach Expand stand im Study-Reiter statt der
    // Zeichnung ein ~10 px hoher leerer Rahmen. Die Zeichenfläche muss dort so groß sein wie im
    // Structure-Reiter — für generate_molecule, das Datenblatt und die Detailansicht im Batch.
    {
      const flaeche = (f, v) => f.evaluate((sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const b = el.getBoundingClientRect();
        return { w: Math.round(b.width), h: Math.round(b.height),
          rollen: document.documentElement.scrollHeight > innerHeight + 1 };
      }, `[data-view="${v}"] .structure-canvas`);
      const faelle = [
        ["molecule", "generate_molecule", { name_or_smiles: "aspirin" }, async () => {}],
        ["datenblatt", "lookup_molecule_data", { name: "paracetamol" }, async (f) => {
          await f.getByText("103-90-2").first().waitFor({ timeout: 30000 });
        }],
        ["batch", "batch_generate", { molecules: ["benzene", "toluene", "phenol"] }, async (f) => {
          await f.locator(".batch-card").nth(2).click();
          await f.getByRole("button", { name: "Back to all structures" }).waitFor();
        }],
      ];
      for (const [tag, name, input, vorbereiten] of faelle) {
        for (const [w, h] of [[740, 1040], [1000, 700]]) {
          if (tag !== "molecule" && w === 740) continue;
          const [page, f] = await open(name, input, full(w, h), { viewport: { width: w, height: h } });
          await vorbereiten(f);
          await f.getByRole("tab", { name: "Study", exact: true }).waitFor({ timeout: 30000 });
          await f.getByRole("tab", { name: "Structure", exact: true }).click();
          await f.locator('[data-view="structure"] .structure-canvas').waitFor();
          await page.waitForTimeout(300);
          const s = await flaeche(f, "structure");
          await f.getByRole("tab", { name: "Study", exact: true }).click();
          await f.locator('[data-view="study"]').waitFor();
          await page.waitForTimeout(300);
          const l = await flaeche(f, "study");
          messwerte[`e6-study-${tag}-${w}x${h}`] = JSON.stringify({ structure: s, study: l });
          // Gleiche Breite; die Höhe darf um die Zeilen abweichen, die nur Study trägt (Überschrift
          // „Functional groups: N to find“ als eigene Zeile, „Reveal all · Cover again“) — bei 1000×700
          // ~50 px. Vorher (Desktop 16.11.) war es ein Rahmen von ~10 px.
          check(l && l.h >= 200 && l.w === s.w && l.h >= 0.8 * s.h && l.rollen === s.rollen,
            `E6 Study ${tag} ${w}×${h}: Zeichenfläche wie im Structure-Reiter (Structure ${s?.w}×${s?.h}${s?.rollen ? " rollt" : ""}, Study ${l?.w}×${l?.h}${l?.rollen ? " rollt" : ""})`);
          await page.close();
        }
      }
    }

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
    // (f) Etappe 3: der 2D/3D-Schalter sitzt über der Zeichenfläche und bleibt beim Umschalten
    // stehen; die 3D-Fläche passt bei 1000×700 samt Kopf und Fußzeile ohne Rollen — im Chat
    // (gemeldete Höhe) wie im Vollbild — und im 320-px-Seitenpanel in die Breite.
    {
      const KOFFEIN = { name_or_smiles: "caffeine" };
      const achse = (f) => f.evaluate(() => {
        const a = document.querySelector("[data-view-axis]")?.getBoundingClientRect();
        const c = document.querySelector('[data-view="structure"] .structure-canvas')?.getBoundingClientRect();
        return a && c ? { top: Math.round(a.top), left: Math.round(a.left), ueber: a.bottom <= c.top + 1 } : null;
      });
      const zu3d = async (f) => {
        await f.getByRole("button", { name: "3D", exact: true }).click();
        await f.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 });
        await f.page().waitForTimeout(300);
      };
      {
        const [page, f] = await open("generate_molecule", KOFFEIN, chat(1000), { viewport: { width: 1000, height: 700 } });
        await settle(f);
        await fitChat(page);
        const a2 = await achse(f);
        const g2 = await geo(f);
        await zu3d(f);
        await fitChat(page);
        const a3 = await achse(f);
        const g3 = await geo(f);
        const h3 = await page.evaluate(() => window.__panelSizes.at(-1)?.height);
        messwerte["f-chat"] = `Achse 2D ${JSON.stringify(a2)} → 3D ${JSON.stringify(a3)}; 3D ${lage(g3)}; gemeldet ${h3}`;
        check(a2?.ueber && a3?.ueber, `E3 (f) Chat: Schalter über der Zeichenfläche (2D ${JSON.stringify(a2)}, 3D ${JSON.stringify(a3)})`);
        check(a2 && a3 && a2.top === a3.top && a2.left === a3.left, `E3 (f) Chat: Schalter bleibt beim Umschalten stehen (${a2?.top}/${a2?.left} → ${a3?.top}/${a3?.left})`);
        // Etappe 6, bewusst zurückgedreht (Jay 16.11.2026: „3D ist zu klein, das muss wieder größer
        // werden“): vorher (Etappe 3) teilte 3D die 320-px-Fläche der 2D-Zeichnung und das Panel blieb
        // ≤ 700 px. Jetzt wieder volle Breite wie am 07.11., Kernwerte darunter; die 700-px-Grenze
        // im Chat gilt für 3D nicht mehr.
        const inhalt = await f.evaluate(() => Math.round(document.querySelector('[data-view="structure"] .structure-layout').getBoundingClientRect().width));
        check(g3.canvas && g3.canvas.h >= 500 && g3.canvas.w >= 0.9 * inhalt,
          `E6 Chat 1000 px: 3D-Modell groß, volle Breite (${g3.canvas?.w}×${g3.canvas?.h} bei Inhaltsbreite ${inhalt}, 2D ${g2.canvas?.w}×${g2.canvas?.h}, Panel ${h3})`);
        await page.screenshot({ path: join(layoutShots, "f-koffein-chat-3d-1000.png"), fullPage: true });
        await page.close();
      }
      for (const [w, h] of [[1000, 700], [320, 700]]) {
        const [page, f] = await open("generate_molecule", KOFFEIN, full(w, h));
        await settle(f);
        const a2 = await achse(f);
        await zu3d(f);
        const a3 = await achse(f);
        const g3 = await geo(f);
        messwerte[`f-${w}x${h}`] = `Achse ${JSON.stringify(a2)} → ${JSON.stringify(a3)}; 3D ${lage(g3)}`;
        check(a2 && a3 && a2.top === a3.top && a3.ueber, `E3 (f) ${w}×${h}: Schalter über der Fläche, bleibt stehen (${a2?.top} → ${a3?.top})`);
        check(g3.sw <= g3.iw, `E3 (f) ${w}×${h}: 3D passt in die Breite (${lage(g3)})`);
        // Etappe 6: schmal hält die Kuhle die Mindesthöhe der Zeichenfläche (260 px), nur ab 620 px darf sie für die Kernwerte schrumpfen.
        if (w === 320) check(g3.canvas.h >= 260, `E6 ${w}×${h}: 3D-Modell nicht kleiner als die 2D-Fläche (${lage(g3)})`);
        if (w === 1000) check(g3.sh <= g3.ih, `E3 (f) ${w}×${h}: 3D ohne Rollen (${lage(g3)})`);
        await page.screenshot({ path: join(layoutShots, `f-koffein-3d-${w}x${h}.png`) });
        await page.close();
      }
      // Expand füllt beim Mechanismus den Bereich (Scope: Vollprofil, siehe panel:shots e3-scope), ohne dass der Inhalt die Höhe vorgibt.
      for (const [name, input, sel] of [
        ["generate_mechanism", { reaction_type: "sn2", substrates: ["C[C@@H](Br)CC", "[C-]#N"] }, ".mechanism-panel"],
      ]) {
        const [page, f] = await open(name, input, full(1000, 700));
        await f.locator(`${sel} svg`).first().waitFor();
        await page.waitForTimeout(300);
        const m = await f.evaluate((q) => ({ h: Math.round(document.querySelector(q).getBoundingClientRect().height),
          sh: document.documentElement.scrollHeight, ih: innerHeight }), sel);
        messwerte[`f-${name}`] = JSON.stringify(m);
        check(m.sh <= m.ih && m.h > 560, `E3 (f) ${name} 1000×700: füllt den Bereich ohne Rollen (${JSON.stringify(m)})`);
        await page.close();
      }
      // generate_3d: das quadratische SVG darf die Höhe nicht vorgeben (vorher 1095 px in 700).
      {
        const [page, f] = await open("generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" }, full(1000, 700));
        await f.locator(".m3d-panel svg").first().waitFor();
        await page.waitForTimeout(300);
        const g = await geo(f);
        messwerte["f-generate_3d"] = lage(g);
        check(g.sh <= g.ih, `E3 (f) generate_3d 1000×700: ohne Rollen (${lage(g)})`);
        await page.close();
      }
      // Etappe 6 (Jay 16.11.2026: „3D ist zu klein, das muss wieder größer werden“): im Chat war die
      // Modellfläche 864×329 px (Panel 500 px hoch). Jetzt ein Quadrat über die Inhaltsbreite, höchstens 640 px;
      // 320×700 im Seitenpanel skaliert weiter ohne Abschneiden.
      for (const [w, h] of [[1000, 0], [320, 700]]) {
        const [page, f] = await open("generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" },
          h ? full(w, h) : chat(w), { viewport: { width: w, height: h || 1300 } });
        await f.locator(".m3d-panel svg circle").first().waitFor();
        if (!h) await fitChat(page);
        await page.waitForTimeout(300);
        const m = await f.evaluate(() => {
          const b = document.querySelector(".m3d-stage").getBoundingClientRect();
          const p = document.querySelector(".m3d-panel"), cs = getComputedStyle(p);
          const inhalt = p.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
          const de = document.documentElement;
          return { w: Math.round(b.width), h: Math.round(b.height), inhalt: Math.round(inhalt), sh: de.scrollHeight, ih: innerHeight, sw: de.scrollWidth, iw: innerWidth };
        });
        messwerte[`e6-generate_3d-${w}x${h || "chat"}`] = JSON.stringify(m);
        if (!h) check(m.h >= 500 && m.w >= 0.9 * m.inhalt && m.sh <= m.ih + 1,
          `E6 generate_3d Chat ${w}: Modellfläche groß (${JSON.stringify(m)})`);
        else check(m.sh <= m.ih && m.sw <= m.iw && m.h >= 240, `E6 generate_3d ${w}×${h}: passt ohne Rollen (${JSON.stringify(m)})`);
        await page.close();
      }
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
        (f) => f.getByRole("tab", { name: "Overview", exact: true }).waitFor()],
      ["protein", "generate_protein_or_antibody", { name: "trastuzumab" }, (f) => f.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 30000 })],
    ]) {
      const [page, f] = await open(name, input, full(320, 900));
      await ready(f);
      await page.waitForTimeout(500);
      const views = tag === "mechanism" ? ["Overview", "Step by step"] : tag === "protein" ? ["Structure", "Scheme"] : [null];
      for (const v of views) {
        if (v) await f.getByRole("tab", { name: v, exact: true }).click();
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
      ["batch", "batch_generate", { molecules: ["benzene", "toluene", "phenol"] }, (f) => f.locator(".batch-card").nth(2).waitFor()],
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
        // Etappe 2: Raster statt Stapel — drei Karten in einer Reihe, jede mit Zeichnung.
        const k = await f.locator(".batch-card").evaluateAll((els) => els.map((e) => {
          const b = e.getBoundingClientRect(), s = e.querySelector(".batch-card-structure svg")?.getBoundingClientRect();
          return { top: Math.round(b.top), svg: s ? Math.round(s.height) : 0 };
        }));
        messwerte["w-batch-karten"] = JSON.stringify(k);
        check(k.length === 3 && k.every((c) => c.top === k[0].top && c.svg > 80), `U2 batch: drei Karten in einer Reihe mit Zeichnung (${JSON.stringify(k)})`);
      }
      await page.close();
    }
    // Etappe 2 (16.11.2026): batch_generate als Raster. Vorher standen sechs volle Karten
    // untereinander (4920 px im Chat bei 1000 px); jetzt Übersicht, Detail auf Klick.
    {
      const SECHS = { molecules: ["benzene", "toluene", "phenol", "aspirin", "caffeine", "ibuprofen"] };
      const karten = (f) => f.locator(".batch-card").evaluateAll((els) => els.map((e) => {
        const b = e.getBoundingClientRect();
        return { left: Math.round(b.left), top: Math.round(b.top), w: Math.round(b.width) };
      }));
      {
        const [page, f] = await open("batch_generate", SECHS, chat(1000), { viewport: { width: 1000, height: 1300 } });
        await f.locator(".batch-card").nth(5).waitFor();
        await fitChat(page);
        const k = await karten(f);
        const panel = await f.evaluate(() => Math.ceil(document.getElementById("root").getBoundingClientRect().bottom) + 16);
        const spalten = new Set(k.map((c) => c.left)).size;
        messwerte["e2-batch6-chat1000"] = JSON.stringify({ panel, spalten });
        check(k.length === 6 && spalten >= 3 && panel <= 900, `E2 batch 6 Stoffe Chat 1000: ${spalten} Spalten, Panel ${panel} px ≤ 900`);
        await page.close();
      }
      {
        const [page, f] = await open("batch_generate", SECHS, full(320, 700), { viewport: { width: 320, height: 700 } });
        await f.locator(".batch-card").nth(5).waitFor();
        await page.waitForTimeout(300);
        const k = await karten(f);
        const de = await f.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth }));
        const spalten = new Set(k.map((c) => c.left)).size;
        check(spalten === 2 && de.sw <= de.iw, `E2 batch Seitenpanel 320×700: zwei Spalten, nichts ragt heraus (${spalten}, ${de.sw}≤${de.iw})`);
        // Rollposition: zur letzten Karte rollen, öffnen, zurück — die Übersicht steht wieder dort.
        const letzte = f.locator(".batch-card").nth(5);
        await f.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await page.waitForTimeout(150);
        const vorher = await f.evaluate(() => scrollY);
        await letzte.click();
        await f.getByRole("button", { name: "Back to all structures" }).waitFor();
        const imDetail = await f.evaluate(() => scrollY);
        await page.screenshot({ path: join(layoutShots, "e2-batch-detail-320x700.png") });
        await f.getByRole("button", { name: "Back to all structures" }).click();
        await letzte.waitFor();
        const nachher = await f.evaluate(() => scrollY);
        check(vorher > 100 && imDetail === 0 && Math.abs(nachher - vorher) <= 2,
          `E2 batch 320×700: Detail beginnt oben, zurück an derselben Stelle (${vorher} → ${imDetail} → ${nachher})`);
        await page.close();
      }
    }
    // Etappe 1 (16.11.2026): Diagramme lesbar. Vorher saß die Figur im Chat bei 1000 px
    // 330 px breit in einer 936-px-Karte (feste 480 px Panelhöhe, Continue-Zeile darunter),
    // Spektrum und DC füllten das Vollbild nicht, und im Dunkeln stand eine weiße Fläche.
    {
      const plotFigure = (f) => f.evaluate(() => {
        const card = document.querySelector(".plot-svg");
        const svg = card?.querySelector("svg");
        if (!svg) return null;
        const c = card.getBoundingClientRect(), r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
        const k = Math.min(r.width / vb.width, r.height / vb.height);
        const de = document.documentElement;
        return { card: Math.round(c.width), cardH: Math.round(c.height), w: Math.round(vb.width * k), h: Math.round(vb.height * k),
          hoch: vb.height > vb.width, sh: de.scrollHeight, ih: innerHeight, sw: de.scrollWidth, iw: innerWidth,
          panel: Math.ceil(document.getElementById("root").getBoundingClientRect().bottom) + 16 };
      });
      const PLOTS = [
        ["spectrum", "generate_spectrum", { spectrum_type: "ir", title: "Aspirin IR", peaks: [
          { position: 1750, intensity: 1, label: "Ester-C=O" }, { position: 1690, intensity: 1, label: "Säure-C=O" }] }],
        ["tlc", "generate_tlc", { title: "DC", lanes: [{ name: "Edukt", spots: [{ rf: 0.3, label: "Edukt" }] }, { name: "Produkt", spots: [{ rf: 0.65 }] }] }],
        ["titration", "generate_titration_curve", { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1, v_acid_ml: 25, c_titrant: 0.1 }],
        ["species", "generate_species_distribution", { substance: "Phosphoric acid", pka_values: [2.15, 7.2, 12.35] }],
        ["compare", "compare_molecules", { structures: ["CC(C)Cc1ccc(cc1)C(C)C(=O)O", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O"], labels: ["Ibuprofen", "Naproxen"] }],
      ];
      for (const [tag, name, input] of PLOTS) {
        // Chat 1000 px: die Figur nutzt die Breite, bis die Höchsthöhe greift; das Panel passt in 700 px.
        {
          const [page, f] = await open(name, input, chat(1000), { viewport: { width: 1000, height: 1300 } });
          await f.locator(".plot-svg svg").waitFor();
          await fitChat(page);
          const p = await plotFigure(f);
          messwerte[`e1-${tag}-chat1000`] = JSON.stringify(p);
          const voll = p.hoch ? p.h >= 360 : p.w >= 0.6 * p.card;
          check(voll && p.panel <= 700, `E1 ${tag} Chat 1000: Figur ${p.w}×${p.h} in Karte ${p.card}, Panel ${p.panel} ≤ 700 px`);
          await page.close();
        }
        // Vollbild 1000×700 und Seitenpanel 320×700: nichts rollt, die Figur füllt die Karte.
        for (const [w, h] of [[1000, 700], [320, 700]]) {
          const [page, f] = await open(name, input, full(w, h), { viewport: { width: w, height: h } });
          await f.locator(".plot-svg svg").waitFor();
          await page.waitForTimeout(400);
          const p = await plotFigure(f);
          messwerte[`e1-${tag}-${w}x${h}`] = JSON.stringify(p);
          // Breite Figur: schmal die ganze Kartenbreite, breit mindestens 60 %; DC-Platte: die Höhe der
          // Karte — auch schmal (Etappe 5: die Karte passt sich der Platte an; in Etappe 4 war hier die
          // Ausnahme „schmal genügt die Breite“, darunter blieben ~70 px der Karte leer).
          const voll = p.hoch ? p.h >= 0.85 * (p.cardH - 18) : p.w >= (w === 320 ? 0.9 * (p.card - 18) : 0.6 * p.card);
          check(voll && p.sh <= p.ih && p.sw <= p.iw, `E1 ${tag} ${w}×${h}: Figur ${p.w}×${p.h} in Karte ${p.card}×${p.cardH}, kein Rollen`);
          await page.close();
        }
        // Dunkel: Fläche, Achsen und Schrift folgen dem Thema; Datenfarben bleiben.
        {
          const [page, f] = await open(name, input, chat(1000), { colorScheme: "dark", viewport: { width: 1000, height: 1300 } });
          await f.locator(".plot-svg svg").waitFor();
          await page.waitForTimeout(300);
          const d = await f.evaluate(() => {
            const card = document.querySelector(".plot-svg");
            const svg = card.querySelector("svg");
            const lum = (c) => { const m = c.match(/[\d.]+/g); return m ? (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255 : -1; };
            const cs = (el, prop) => (el ? getComputedStyle(el)[prop] : "");
            // Achsenbeschriftung bzw. RDKit-Bindungen: die hellste Kante und Schrift im Bild
            const text = [...svg.querySelectorAll("text")].find((t) => !/fill:/.test(t.getAttribute("style") || ""));
            const ink = svg.querySelector('path[style*="stroke: #000000"], path[style*="stroke:#000000"]');
            const bg = svg.querySelector('path[style*="fill: #ffffff"], rect[style*="fill:#FFFFFF"]');
            const red = svg.querySelector('path[style*="stroke: #d62728"], path[style*="fill:#FF7F7F"]');
            // DC: die Platte bleibt hell, der Fleckname darauf dunkel.
            const fleck = [...svg.querySelectorAll('text[style*="font-size: 8px"]')].find((t) => t.textContent.trim() === "Edukt");
            const platte = svg.querySelector('path[style*="fill: #fbfaf6"]');
            return { fleck: fleck ? lum(cs(fleck, "fill")) : null, platte: platte ? lum(cs(platte, "fill")) : null,
              karte: lum(cs(card, "backgroundColor")), text: text ? lum(cs(text, "fill")) : null, ink: ink ? lum(cs(ink, "stroke")) : null,
              papier: bg ? cs(bg, "fill") : null, rot: red ? (red.getAttribute("style").includes("FF7F7F") ? cs(red, "fill") : cs(red, "stroke")) : null };
          });
          messwerte[`e1-${tag}-dunkel`] = JSON.stringify(d);
          check(d.karte >= 0 && d.karte < 0.3, `E1 ${tag} dunkel: Karte dunkel (Luminanz ${d.karte})`);
          check(d.text === null || d.text > 0.6, `E1 ${tag} dunkel: Schrift hell (${d.text})`);
          check(d.ink === null || d.ink > 0.6, `E1 ${tag} dunkel: Achsen/Striche hell (${d.ink})`);
          if (tag === "tlc") check(d.platte > 0.9 && d.fleck !== null && d.fleck < 0.3, `E1 tlc dunkel: Platte hell (${d.platte}), Fleckname dunkel (${d.fleck})`);
          if (tag === "species") check(d.rot === "rgb(214, 39, 40)", `E1 species dunkel: Spezies-Rot bleibt (${d.rot})`);
          // Markierung bleibt sichtbar, aber nicht im O-Rot (--atom-o #ff7b72 ≈ RDKits #FF7F7F).
          if (tag === "compare") check(d.rot === "rgb(163, 71, 107)", `E1 compare dunkel: Unterschied-Markierung eigene Farbe, nicht O-Rot (${d.rot})`);
          await page.screenshot({ path: join(layoutShots, `e1-${tag}-dark.png`) });
          await page.close();
        }
      }
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
      // Etappe 4 (16.11.2026): Koffein im Chat bei 1000 px höchstens 700 px hoch (vorher 811);
      // Datenblatt: Wert nah am Etikett, Kopierknöpfe leise (Deckkraft 0 ohne Hover), aber
      // im Bedienungshilfen-Baum, bei Hover und Tastaturfokus der Zeile voll sichtbar.
      {
        const [page, f] = await open("generate_molecule", { name_or_smiles: "caffeine" }, chat(1000));
        await settle(f);
        await fitChat(page);
        const size = await page.evaluate(() => window.__panelSizes.at(-1));
        check(size && size.height <= 700, `E4: Koffein im Chat (1000 px) höchstens 700 px hoch (${size?.height})`);
        await page.close();
      }
      // Der Hinweis teilt die Zeile mit den Chips: Vorschau (Hover) und Auswahl dürfen die
      // Panelhöhe nicht ändern — sonst skaliert Desktop das iframe und die Chips wandern unter der Maus.
      for (const width of [1000, 700]) {
        const [page, f] = await open("generate_molecule", morphine, chat(width));
        await settle(f);
        await fitChat(page);
        const hoehe = () => f.evaluate(() => document.documentElement.scrollHeight);
        const ruhe = await hoehe();
        const chips = f.locator("button.functional-group");
        const n = await chips.count();
        const werte = [];
        for (let i = 0; i < n; i++) { await chips.nth(i).hover(); await page.waitForTimeout(120); werte.push(await hoehe()); }
        check(n >= 2 && werte.every((h) => h === ruhe), `E4 ${width}: Hover über die Gruppen ändert die Höhe nicht (Ruhe ${ruhe}, dann ${werte.join(", ")}; ${n} Gruppen)`);
        // Anheften tauscht die Knöpfe der Weiter-Zeile (gewollt); die Gruppen-Zeile selbst bleibt gleich hoch.
        const sektion = () => f.evaluate(() => Math.round(document.querySelector(".group-section").getBoundingClientRect().height));
        await page.mouse.move(2, 2); await page.waitForTimeout(120);
        const vor = await sektion();
        await chips.nth(0).click(); await page.mouse.move(2, 2); await page.waitForTimeout(150);
        const nach = await sektion();
        check(vor === nach, `E4 ${width}: Anheften ändert die Höhe der Gruppen-Zeile nicht (${vor} → ${nach})`);
        await page.close();
      }
      {
        const [page, f] = await open("lookup_molecule_data", { name: "paracetamol" }, chat(1000));
        await settle(f);
        const rowOf = (key) => f.locator(".source-row", { has: f.locator("dt", { hasText: key }) }).first();
        const cas = rowOf("CAS");
        const btn = cas.getByRole("button", { name: "Copy value" });
        const op = () => btn.evaluate((b) => getComputedStyle(b).opacity);
        const hover = await f.evaluate(() => matchMedia("(hover: hover)").matches);
        const ruhe = await op();
        check(await f.getByRole("button", { name: "Copy value" }).count() >= 5, "E4: jede Datenblatt-Zeile hat „Copy value“ im Bedienungshilfen-Baum");
        check(hover ? ruhe === "0" : Number(ruhe) > 0, `E4: Kopierknopf ohne Hover leise (${ruhe}, hover:${hover})`);
        await cas.hover();
        await page.waitForTimeout(200);
        check(await op() === "1", "E4: Hover über die Zeile zeigt den Kopierknopf");
        await page.mouse.move(2, 2);
        await btn.focus();
        await page.waitForTimeout(200);
        check(await op() === "1", "E4: Tastaturfokus zeigt den Kopierknopf");
        const abstand = await cas.evaluate((r) => Math.round(r.querySelector("dd").getBoundingClientRect().left - r.querySelector("dt").getBoundingClientRect().left));
        check(abstand <= 200, `E4: Wert steht nah am Etikett (${abstand} px Versatz; vorher 230, Bild etappe4/vorher)`);
        const subs = await rowOf("Molecular formula").locator("dd sub").count();
        check(subs === 3, `E4: Summenformel im Datenblatt tiefgestellt (${subs} Indizes)`);
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
        await f.locator(".batch-card").nth(2).waitFor();
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
    await f.getByRole("tab", { name: "Overview", exact: true }).waitFor();
    const body = await f.locator("body").innerText();
    check(!body.includes("textbook example") && body.includes(example), `${type}: sichtbarer Titel nennt die gezeichneten Substrate`);
    // Pfeile und Struktur kommen aus echten Renderer-SVGs, nicht aus einem Text-Platzhalter.
    check(await f.locator('svg path').count() > 0 && body.includes("Reactants"), `${type}: Übersicht enthält gezeichnete Strukturen und Schritte`);
    await f.getByRole("tab", { name: "Step by step", exact: true }).click();
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
  check(/drag to rotate/i.test(await spatialFrame.locator("body").innerText()), "3D: Bedienhinweis sichtbar");
  // Etappe 5: Formel und Molmasse aus den Atomen im Untertitel
  check(/C8H10N4O2 · 194\.19 g\/mol/.test(await spatialFrame.locator(".panel-subtitle").innerText()), "3D: Summenformel und Molmasse im Untertitel (Koffein)");
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
  // Etappe 5: „Reset view“ stellt die Ausgangsdrehung wieder her (nach der Einblend-Drehung dieselbe Ruhelage).
  await spatialFrame.getByRole("button", { name: "Reset view" }).click();
  await spatial.waitForTimeout(1600);
  check(JSON.stringify(await geometry()) === ruhe, "3D: Reset view stellt die Ausgangslage wieder her");
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

  // E19: Bildgröße im Proteinpanel (bis Etappe 4 ein Quadrat bis 720 px; seit Etappe 5
  // im Chat 280 px hoch, styles.css `.protein-stage`, mehr Fläche gibt Expand). Wie Desktop: das iframe bekommt die Höhe, die das Panel
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
      scheme: painted(document.querySelector("svg[data-igg-scheme]")),
      // kleinste Schrift des Schemas in Bildschirm-px (font-size × Maßstab der viewBox)
      schemeFont: (() => {
        const svg = document.querySelector("svg[data-igg-scheme]");
        if (!svg) return null;
        const k = svg.getScreenCTM().a;
        return Math.min(...[...svg.querySelectorAll("text")].map((t) => parseFloat(getComputedStyle(t).fontSize) * k));
      })() };
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
    // Etappe 5: feste Höhe im Chat statt Quadrat (vorher bis 720 px — Panel 1171 px bei 1000 px)
    check(m.stage.w >= inhalt - 2 && m.stage.h === 280,
      `E19 lysozyme ${width}px: Bildfläche volle Breite, im Chat 280 px hoch — ${m.stage.w}×${m.stage.h}`);
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
      // Etappe 5: die Fläche ist im Chat 280 px hoch (Panel ≤ 700, vorher ein Quadrat bis 720,
      // Schema ≥ 700) — das Schema füllt ihre Höhe, und die kleinste Schrift bleibt ≥ 8 px.
      check(m.scheme && m.scheme.h >= m.stage.h - 2 && m.schemeFont >= 8,
        `E19 Schema 860px: gemalt ${m.scheme?.w}×${m.scheme?.h} in ${m.stage.w}×${m.stage.h}, kleinste Schrift ${m.schemeFont?.toFixed(1)} px`);
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
  // Etappe 6 (Jay 16.11.2026: „3D ist zu klein, das muss wieder größer werden“): wieder wie am
  // 07.11. — die Kuhle nimmt die volle Breite (höchstens 720 px hoch), die Kernwerte rücken darunter.
  // Etappe 3 hatte sie in die 320-px-Fläche der 2D-Zeichnung gelegt.
  const box3d = (await frame.locator("[data-view-3d]").boundingBox()) ?? { width: 0, height: 0 };
  const breiteZeile = (await frame.locator('[data-view="structure"] .structure-layout').boundingBox())?.width ?? 0;
  prüfe(box3d.width >= breite2d && Math.abs(box3d.width - breiteZeile) <= 1 && Math.abs(box3d.height - Math.min(720, box3d.width)) <= 1,
    `3D-Kuhle über die volle Breite (2D ${Math.round(breite2d)}×320 px → 3D ${Math.round(box3d.width)}×${Math.round(box3d.height)} px, Zeile ${Math.round(breiteZeile)})`);
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
  // E2/Etappe 3: eine Ansicht-Achse direkt über der Kuhle, Stereo und Gruppen in 3D aus
  const achse = (await frame.locator("[data-view-axis]").boundingBox()) ?? { y: Infinity, height: 0 };
  const kuhle = (await frame.locator("[data-view-3d]").boundingBox()) ?? { y: 0, height: 0 };
  const abstand = kuhle.y - (achse.y + achse.height);
  prüfe(await frame.locator("[data-view-axis]").count() === 1 && await frame.locator(".structure-tools").count() === 0
    && abstand >= 0 && abstand <= 24,
    `Ansicht-Achse sitzt ${Math.round(abstand)} px über der Kuhle — genau eine Reihe`);
  prüfe(await frame.locator("[data-testid='stereo-note']").count() === 0 && await frame.locator(".group-section").count() === 0,
    "3D blendet Stereo-Zeile und Gruppen-Chips aus");
  await page.waitForTimeout(1300); // Einblend-Drehung abgeschlossen, Bild zeigt die Ruhelage
  await page.screenshot({ path: join(tmpdir(), "panel-host-3d-button.png") });
  await frame.getByRole("button", { name: "3D", exact: true }).click();
  await frame.locator(".structure-drawing").waitFor({ timeout: 5000 });
  prüfe(await frame.locator("[data-testid='stereo-note']").count() === 1 && await frame.locator(".group-section").count() === 1,
    "Zurück in 2D: Stereo-Zeile und Gruppen-Chips wieder da");
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
  // das gemeinsame Gerüst hell — auf dem damals weißen Bildgrund fast unsichtbar.
  // Seit Etappe 1 (16.11.2026) folgt die Fläche dem Thema: dunkler Grund, Gerüst hell.
  // Gleich bleibt der Kern des Befunds: Grund und Gerüst stehen im Kontrast.
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
  check(scaffold.n > 0 && scaffold.bg < 0.3 && scaffold.maxStroke > 0.6 && (scaffold.maxFill === 0 || scaffold.maxFill > 0.6),
    `Vergleich dunkel: Gerüst hell auf dunklem Grund (${scaffold.n} Pfade, Strich ${scaffold.maxStroke.toFixed(2)}, Schrift ${scaffold.maxFill.toFixed(2)})`);
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
        input: { molecules: ARZNEISTOFFE }, strip: true, karten: 20, karte: ".batch-card" },
      { label: "Vancomycin", tool: "generate_molecule", input: { name_or_smiles: VANCOMYCIN }, strip: false, karten: 1, karte: ".panel-title" },
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
      await f.locator(fall.karte).nth(fall.karten - 1).waitFor({ timeout: 30000 }).catch(() => {});
      const bilder = await f.locator(fall.karte).count();
      // Je Karte eine Zeichnung mit Bindungen (Stapel: das Vorschaubild der Karte; die Schwelle 50 × Karten
      // zählte früher auch Knopf-Symbole der vollen Karten mit, Etappe 2).
      const zeichnung = fall.karte === ".batch-card" ? ".batch-card-structure" : "[data-view='structure'] .structure-canvas";
      const jeKarte = await f.locator(zeichnung).evaluateAll((els) => els.map((e) => e.querySelectorAll("path").length));
      const pfade = jeKarte.reduce((a, b) => a + b, 0);
      check(bilder === fall.karten && jeKarte.length === fall.karten && jeKarte.every((n) => n >= 6) && calls.includes("load_panel_part")
        && calls.every((n) => n === "load_panel_part"),
        `${fall.label}: Panel lädt ${calls.length}× nach und zeigt ${bilder} Karte(n) mit ${pfade} Pfaden (je Zeichnung mind. ${Math.min(...jeKarte)})`);
      await p.screenshot({ path: join(tmpdir(), `panel-host-m2-${fall.tool}.png`) });
      await p.close();
    }
    // Block nicht mehr beim Server (gelöscht, fremder Rechner): Meldung mit den
    // geschriebenen Dateien, nie eine leere Fläche.
    {
      const p = await browser.newPage({ viewport: { width: 720, height: 600 } });
      await p.setContent('<body style="margin:0"></body>');
      await p.addScriptTag({ path: out });
      await p.exposeFunction("__callTool", (req) => client.callTool(req));
      const result = await client.callTool({ name: "batch_generate", arguments: { molecules: ARZNEISTOFFE } });
      const text = JSON.parse(result.content[0].text);
      text._deferred.token = "f".repeat(32);
      const toolResult = { content: [{ type: "text", text: JSON.stringify(text) }], isError: false };
      const tool = tools.find((t) => t.name === "batch_generate");
      const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
      await p.evaluate((a) => window.__startHost(a), { html: resource.contents[0].text, toolInput: {}, toolResult });
      const f = p.frames().at(-1);
      await f.getByRole("alert").waitFor({ timeout: 15000 }).catch(() => {});
      const shown = await f.locator("body").innerText();
      check(await f.getByRole("alert").count() === 1 && shown.includes("could not be loaded")
        && shown.includes("Run the tool again") && /\.png/.test(shown) && await f.locator(".panel-title, .batch-card").count() === 0,
        `Nachladen scheitert: Meldung mit Dateipfaden statt leerer Fläche („${shown.replace(/\s+/g, " ").slice(0, 90)}…“)`);
      await p.screenshot({ path: join(tmpdir(), "panel-host-m2-fehlt.png") });
      await p.close();
    }
  }

  const batchPage = await browser.newPage({ viewport: { width: 720, height: 900 } });
  await batchPage.setContent('<body style="margin:0"></body>');
  await batchPage.addScriptTag({ path: out });
  await batchPage.exposeFunction("__callTool", (req) => client.callTool(req));
  const batch = await mount(batchPage, "batch_generate", { molecules: ["benzene", "toluene", "phenol"] });
  await batch.locator(".batch-card").nth(2).waitFor();
  const names = (await batch.locator(".batch-card-name").allInnerTexts()).map((t) => t.toLowerCase());
  check(["benzene", "toluene", "phenol"].every((n) => names.includes(n)), `Batch: drei Karten im Raster (${names.join(", ")})`);
  check(await batch.locator("article.molecule-panel").count() === 0 && await batch.locator("[data-testid='panel-footer']").count() === 1,
    "Batch: Übersicht ohne volle Molekül-Karten, eine Fußzeile");
  // Etappe 2: Karte öffnen (Tastatur: Enter), Daten über den echten Server, zurück zur Übersicht.
  await batch.getByRole("button", { name: /^phenol, / }).focus();
  await batch.page().keyboard.press("Enter");
  await batch.locator("article.molecule-panel .panel-title").waitFor();
  check((await batch.locator("article.molecule-panel .panel-title").innerText()).toLowerCase() === "phenol"
    && await batch.locator(".batch-card").count() === 0, "Batch: Enter auf der Karte öffnet die volle Ansicht von phenol");
  await batch.getByRole("tab", { name: "Data" }).click();
  await batch.getByText("108-95-2").first().waitFor({ timeout: 30000 });
  check(true, "Batch-Detail: Reiter Data lädt das Datenblatt (CAS 108-95-2)");
  check(await batch.locator("button.export-png").count() === 1, "Batch-Detail: Export-Knopf des Stoffs");
  await batch.getByRole("button", { name: "Back to all structures" }).click();
  await batch.locator(".batch-card").nth(2).waitFor();
  const fokus = await batch.evaluate(() => document.activeElement?.getAttribute("aria-label") || "");
  check(await batch.locator(".batch-card").count() === 3 && /^phenol, /.test(fokus),
    `Batch: zurück in der Übersicht, Fokus auf der geöffneten Karte (${fokus})`);
  await batchPage.close();
} finally {
  await browser?.close();
  await client.close();
}
