// README-GIFs aus dem echten Panel: derselbe Host-Aufbau wie host.e2e.mjs (sandboxed
// srcdoc-iframe, echte AppBridge, echter MCP-Server im MVP-Profil), Dark Theme, 600 px
// Panelbreite wie in Claude Desktop. Aufgenommen wird eine Screenshot-Serie mit
// Zeitstempeln; während das Panel auf den Server wartet (PubChem, 3D-Konformer), läuft die
// Filmuhr nicht — Ladeframes kommen gar nicht erst ins Bild, statt nachträglich
// herausgeschnitten zu werden. ffmpeg baut daraus GIFs mit eigener Palette.
// usage: npm run readme:gifs [-- views 3d molecule]   (Netz nötig: PubChem)
// Ausgabe: assets/demo-views.gif, assets/demo-3d.gif, assets/demo-molecule.gif
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const assets = join(repo, "assets");
const FFMPEG = existsSync("/opt/homebrew/bin/ffmpeg") ? "/opt/homebrew/bin/ffmpeg" : "ffmpeg";
const FFPROBE = existsSync("/opt/homebrew/bin/ffprobe") ? "/opt/homebrew/bin/ffprobe" : "ffprobe";
const BREITE = 600; // Panelbreite in Claude Desktop
const DUNKEL = "#202724"; // Panel-Hintergrund im Dark Theme (host.e2e prüft rgb(32, 39, 36))
const GRENZEN = { breite: 800, sekunden: 10, bytes: 3 * 1024 * 1024 };

const hostJs = join(mkdtempSync(join(tmpdir(), "readme-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: hostJs, logLevel: "error" });

const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const wegwerfHome = mkdtempSync(join(tmpdir(), "readme-home-"));
const client = new Client({ name: "readme-gifs", version: "0.0.0" });
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "mvp" }, cwd: repo }));
// Im Bild soll kein Wegwerf-Pfad stehen
const neutral = (r) => JSON.parse(JSON.stringify(r).replaceAll(wegwerfHome, "/Users/demo"));

// Filmuhr: zählt nur, solange nicht auf den Server gewartet wird
function filmuhr() {
  let summe = 0, seit = Date.now(), läuft = true;
  return {
    jetzt: () => summe + (läuft ? Date.now() - seit : 0),
    halt() { if (läuft) { summe += Date.now() - seit; läuft = false; } },
    weiter() { if (!läuft) { seit = Date.now(); läuft = true; } },
    get läuft() { return läuft; },
  };
}

async function szene(browser, { name, tool, args, hoehe, fps, ablauf }) {
  const toolDef = (await client.listTools()).tools.find((t) => t.name === tool);
  const toolResult = neutral(await client.callTool({ name: tool, arguments: args }));
  if (toolResult.isError) throw new Error(`${tool}: ` + JSON.stringify(toolResult.content).slice(0, 300));
  const html = (await client.readResource({ uri: toolDef._meta.ui.resourceUri })).contents[0].text;

  const context = await browser.newContext({ viewport: { width: BREITE, height: hoehe }, colorScheme: "dark" });
  const page = await context.newPage();
  await page.exposeFunction("__callTool", async (p) => neutral(await client.callTool(p)));
  await page.setContent(`<body style="margin:0;background:${DUNKEL}"></body>`);
  await page.addScriptTag({ path: hostJs });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput: args, toolResult });
  await page.locator("iframe").evaluate((el, [w, h]) => { el.style.width = `${w}px`; el.style.height = `${h}px`; el.style.display = "block"; }, [BREITE, hoehe]);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  // Desktop setzt das Theme als Host-Vorgabe; das Panel liest data-theme
  await frame.locator(".molecule-panel").waitFor({ timeout: 30000 });
  await frame.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  // Playwright-Screenshots zeigen keinen Mauszeiger: Kreis im Elternfenster über dem iframe
  await page.evaluate(() => {
    const c = document.createElement("div");
    c.id = "cursor";
    c.style.cssText = "position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;background:rgba(240,240,240,.45);border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.6);pointer-events:none;z-index:9;transition:left .22s ease,top .22s ease,transform .12s";
    document.body.appendChild(c);
  });
  await page.waitForTimeout(500); // Schriften und Theme-Übergang setzen sich, bevor die Uhr läuft

  const dir = mkdtempSync(join(tmpdir(), `readme-${name}-`));
  const uhr = filmuhr();
  const bilder = [];
  let aufnahme = true;
  const schleife = (async () => {
    while (aufnahme) {
      if (!uhr.läuft) { await page.waitForTimeout(10); continue; }
      const t = uhr.jetzt();
      const file = join(dir, `f${String(bilder.length).padStart(4, "0")}.png`);
      await page.screenshot({ path: file, clip: { x: 0, y: 0, width: BREITE, height: hoehe } });
      if (uhr.läuft) bilder.push({ file, t });
    }
  })();

  const zeiger = (x, y, mitÜbergang = true) => page.evaluate(([x, y, ü]) => {
    const s = document.getElementById("cursor").style;
    s.transition = ü ? "left .22s ease,top .22s ease,transform .12s" : "transform .12s";
    s.left = `${x - 9}px`; s.top = `${y - 9}px`;
  }, [x, y, mitÜbergang]);
  const mitte = async (locator) => { const b = await locator.boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
  const halten = (ms) => page.waitForTimeout(ms);
  const zeigeAuf = async (locator) => {
    const [x, y] = await mitte(locator);
    await zeiger(x, y);
    await page.mouse.move(x, y, { steps: 8 });
    await halten(220); // Zeiger-Übergang .22 s
  };
  // Klick mit kurzer Pause davor; bis `fertig` sichtbar ist, steht die Filmuhr
  const klick = async (locator, fertig) => {
    await zeigeAuf(locator);
    await halten(120);
    await page.evaluate(() => { document.getElementById("cursor").style.transform = "scale(.7)"; });
    await halten(100);
    uhr.halt();
    await locator.click();
    await page.evaluate(() => { document.getElementById("cursor").style.transform = ""; });
    const t0 = Date.now();
    if (fertig) await fertig();
    await page.waitForTimeout(150); // Übergänge abschließen, noch ohne Uhr
    console.log(`  ${name}: Wartezeit ${Date.now() - t0} ms herausgenommen`);
    uhr.weiter();
  };

  await ablauf({ frame, page, halten, zeigeAuf, klick, zeiger, mitte });
  const ende = uhr.jetzt();
  aufnahme = false;
  await schleife;
  await context.close();
  return gifBauen(name, bilder, ende, fps, dir);
}

function gifBauen(name, bilder, endeMs, fps, dir) {
  if (bilder.length < 10) throw new Error(`${name}: nur ${bilder.length} Bilder aufgenommen`);
  // concat-Demuxer: jedes Bild steht bis zum nächsten Zeitstempel, das letzte bis zum Szenenende
  const zeilen = ["ffconcat version 1.0"];
  bilder.forEach((b, i) => {
    const bis = i + 1 < bilder.length ? bilder[i + 1].t : endeMs;
    zeilen.push(`file '${b.file}'`, `duration ${((bis - b.t) / 1000).toFixed(3)}`);
  });
  zeilen.push(`file '${bilder.at(-1).file}'`);
  const liste = join(dir, "liste.txt");
  writeFileSync(liste, zeilen.join("\n") + "\n");
  const ziel = join(assets, `demo-${name}.gif`);
  const filter = `fps=${fps},scale='min(${GRENZEN.breite},iw)':-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`;
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", liste, "-vf", filter, "-loop", "0", ziel]);
  return prüfen(ziel);
}

function prüfen(ziel) {
  const probe = JSON.parse(execFileSync(FFPROBE, ["-v", "error", "-count_frames", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,nb_read_frames:format=duration", "-of", "json", ziel]).toString());
  const st = probe.streams[0];
  const werte = { datei: ziel, bytes: statSync(ziel).size, breite: st.width, hoehe: st.height,
    sekunden: Number(probe.format.duration), frames: Number(st.nb_read_frames) };
  const fehler = [];
  if (werte.breite > GRENZEN.breite) fehler.push(`Breite ${werte.breite} px > ${GRENZEN.breite}`);
  if (!(werte.sekunden <= GRENZEN.sekunden)) fehler.push(`Dauer ${werte.sekunden} s > ${GRENZEN.sekunden}`);
  if (werte.bytes > GRENZEN.bytes) fehler.push(`Größe ${(werte.bytes / 1048576).toFixed(2)} MB > 3 MB`);
  if (fehler.length) throw new Error(`ROT ${ziel}: ${fehler.join("; ")}`);
  console.log(`✔ ${ziel}: ${(werte.bytes / 1024).toFixed(0)} KB, ${werte.breite}×${werte.hoehe}, ${werte.sekunden.toFixed(2)} s, ${werte.frames} Frames`);
  return werte;
}

// Datenblatt: CAS steht unter der Falz — kurz oben zeigen, weich bis zur CAS-Zeile scrollen,
// dann zeigt der Zeiger auf die Nummer (sonst schwebt er nach dem Scrollen über einer fremden Zeile)
async function datenblattMitCas({ frame, page, halten, zeiger }, gesamtMs) {
  const cas = frame.getByText("CAS No.", { exact: true }).first();
  if (!(await cas.count())) throw new Error("Datenblatt ohne CAS-Zeile");
  await halten(600);
  await cas.evaluate((el) => el.scrollIntoView({ behavior: "smooth", block: "center" }));
  await halten(450);
  const b = await cas.boundingBox();
  const x = b.x + b.width + 190, y = b.y + b.height / 2;
  await zeiger(x, y);
  await page.mouse.move(x, y, { steps: 4 });
  await halten(gesamtMs - 1050);
}

const SZENEN = {
  // Thalidomid: Skelett → All H → Skelett → Show variants → (S) mit Keil → Datenblatt
  views: {
    tool: "generate_molecule", args: { name_or_smiles: "thalidomide" }, hoehe: 640, fps: 15,
    async ablauf(werkzeug) {
      const { frame, halten, klick } = werkzeug;
      const allH = frame.getByRole("button", { name: "All H", exact: true });
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(1000);
      await klick(allH, () => frame.locator('button.chip-toggle[aria-pressed="true"][aria-busy="false"]', { hasText: "All H" }).waitFor({ timeout: 30000 }));
      await halten(1000);
      await klick(allH, () => frame.locator('button.chip-toggle[aria-pressed="false"]', { hasText: "All H" }).waitFor({ timeout: 5000 }));
      await halten(800);
      await klick(frame.getByRole("button", { name: "Show variants" }), () => frame.locator("button.candidate").first().waitFor({ timeout: 30000 }));
      const s = frame.locator("button.candidate").filter({ has: frame.locator(".candidate-label", { hasText: /^\(S\)/ }) });
      if (await s.count() !== 1) throw new Error("views: kein eindeutiger (S)-Kandidat: " + (await frame.locator(".candidate-label").allInnerTexts()).join(" · "));
      await klick(s, () => frame.getByRole("button", { name: "All candidates" }).waitFor({ timeout: 30000 }));
      await halten(1200);
      await klick(frame.getByRole("tab", { name: "Data", exact: true }), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }));
      await datenblattMitCas(werkzeug, 2000);
    },
  },
  // Morphin: 3D-Chip → Modell steht → zwei Drehzüge per Pointer-Drag → Endstand
  "3d": {
    tool: "generate_molecule", args: { name_or_smiles: "morphine" }, hoehe: 795, fps: 12,
    async ablauf({ frame, page, halten, klick, zeiger, mitte }) {
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(800);
      await klick(frame.getByRole("button", { name: "3D", exact: true }), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }));
      await halten(1000);
      const [cx, cy] = await mitte(frame.locator("[data-view-3d]"));
      const zug = async (von, nach, ms) => {
        await zeiger(...von); await page.mouse.move(...von, { steps: 6 }); await halten(320);
        await page.mouse.down();
        // Nach Uhrzeit statt Schrittzahl: jeder Schritt kostet zwei Protokollrunden
        const start = Date.now();
        for (let a = 0; a < 1;) {
          a = Math.min(1, (Date.now() - start) / ms);
          const x = von[0] + (nach[0] - von[0]) * a, y = von[1] + (nach[1] - von[1]) * a;
          await page.mouse.move(x, y);
          await zeiger(x, y, false);
          await halten(16);
        }
        await page.mouse.up();
      };
      await zug([cx - 150, cy], [cx + 150, cy + 20], 1700); // waagerecht: um die senkrechte Achse
      await zug([cx + 20, cy - 130], [cx - 20, cy + 130], 1500); // senkrecht: um die waagerechte Achse
      await halten(1500);
    },
  },
  // Capsaicin: Maus nacheinander über die Gruppen-Chips (Gruppe leuchtet) → Datenblatt
  molecule: {
    tool: "generate_molecule", args: { name_or_smiles: "capsaicin" }, hoehe: 720, fps: 15,
    async ablauf(werkzeug) {
      const { frame, halten, zeigeAuf, klick } = werkzeug;
      const gruppen = frame.locator("button.functional-group");
      await gruppen.first().waitFor();
      await halten(800);
      const n = Math.min(await gruppen.count(), 5);
      for (let i = 0; i < n; i++) {
        await zeigeAuf(gruppen.nth(i));
        await halten(800);
      }
      await klick(frame.getByRole("tab", { name: "Data", exact: true }), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }));
      await datenblattMitCas(werkzeug, 2000);
    },
  },
};

const gewählt = process.argv.slice(2);
mkdirSync(assets, { recursive: true });
const browser = await chromium.launch();
const ergebnisse = [];
try {
  for (const name of gewählt.length ? gewählt : Object.keys(SZENEN)) {
    if (!SZENEN[name]) throw new Error(`unbekannte Szene: ${name} (views, 3d, molecule)`);
    console.log(`▶ ${name}`);
    ergebnisse.push(await szene(browser, { name, ...SZENEN[name] }));
  }
} finally {
  await browser.close();
  await client.close();
}
console.table(ergebnisse.map(({ datei, ...w }) => ({ datei: datei.replace(repo + "/", ""), ...w })));
