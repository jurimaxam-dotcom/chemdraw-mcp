// README-GIFs aus dem echten Panel: derselbe Host-Aufbau wie host.e2e.mjs (sandboxed
// srcdoc-iframe, echte AppBridge, echter MCP-Server im MVP-Profil), helles und dunkles
// Theme, 600 px Panelbreite wie in Claude Desktop. Aufgenommen wird eine Screenshot-Serie mit
// Zeitstempeln; während das Panel auf den Server wartet (PubChem, 3D-Konformer), läuft die
// Filmuhr nicht — Ladeframes kommen gar nicht erst ins Bild, statt nachträglich
// herausgeschnitten zu werden. ffmpeg baut daraus GIFs mit eigener Palette.
// usage: npm run readme:gifs [-- views 3d molecule] [--theme light|dark] [--molecule NAME]
//        (Netz nötig: PubChem; ohne --theme entstehen beide Fassungen)
// Ausgabe: assets/demo-<szene>-<theme>.gif (helle Fassung zusätzlich als demo-<szene>.gif) — die zwei Hero-Szenen (views, 3d) haben einen
// festen Ausschnitt (HERO), damit sie im README nebeneinander auf gleicher Höhe enden.
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, statSync, writeFileSync, copyFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const assets = join(repo, "assets");
const FFMPEG = existsSync("/opt/homebrew/bin/ffmpeg") ? "/opt/homebrew/bin/ffmpeg" : "ffmpeg";
const FFPROBE = existsSync("/opt/homebrew/bin/ffprobe") ? "/opt/homebrew/bin/ffprobe" : "ffprobe";
const BREITE = 600; // Panelbreite in Claude Desktop
// Seitenhintergrund = Panel-Hintergrund des Themes (styles.css --bg; host.e2e prüft rgb(32, 39, 36))
const THEMES = {
  light: { hintergrund: "#fafbf9", zeiger: "background:rgba(30,36,33,.28);border:2px solid #1e2421;box-shadow:0 1px 4px rgba(0,0,0,.25)" },
  dark: { hintergrund: "#202724", zeiger: "background:rgba(240,240,240,.45);border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.6)" },
};
// Fester Ausschnitt der Hero-Szenen: beide GIFs exakt gleich groß (Jay 07.11.). 812 px =
// das ganze 3D-Panel bei 600 px (Titel, Kuhle 1:1, Achse, Kennwerte, Drag-Hinweis bis 798 px)
// plus 12 px Körperrand unten wie oben — gemessen 07.11., imBild bricht ab, wenn es nicht passt
const HERO = { breite: BREITE, hoehe: Number(process.env.HERO_HOEHE || 812) };
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

async function szene(browser, { name, tool, args, hoehe, fps, ablauf, theme, molecule }) {
  if (molecule) args = { ...args, name_or_smiles: molecule };
  const farbe = THEMES[theme];
  const toolDef = (await client.listTools()).tools.find((t) => t.name === tool);
  const toolResult = neutral(await client.callTool({ name: tool, arguments: args }));
  if (toolResult.isError) throw new Error(`${tool}: ` + JSON.stringify(toolResult.content).slice(0, 300));
  const html = (await client.readResource({ uri: toolDef._meta.ui.resourceUri })).contents[0].text;

  const context = await browser.newContext({ viewport: { width: BREITE, height: hoehe }, colorScheme: theme });
  const page = await context.newPage();
  await page.exposeFunction("__callTool", async (p) => neutral(await client.callTool(p)));
  await page.setContent(`<body style="margin:0;background:${farbe.hintergrund}"></body>`);
  await page.addScriptTag({ path: hostJs });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput: args, toolResult });
  await page.locator("iframe").evaluate((el, [w, h]) => { el.style.width = `${w}px`; el.style.height = `${h}px`; el.style.display = "block"; }, [BREITE, hoehe]);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  // Desktop setzt das Theme als Host-Vorgabe; das Panel liest data-theme (auch "light"
  // ausdrücklich setzen: styles.css schaltet sonst per prefers-color-scheme)
  await frame.locator(".molecule-panel").waitFor({ timeout: 30000 });
  await frame.evaluate((t) => document.documentElement.setAttribute("data-theme", t), theme);
  // Playwright-Screenshots zeigen keinen Mauszeiger: Kreis im Elternfenster über dem iframe
  await page.evaluate((stil) => {
    const c = document.createElement("div");
    c.id = "cursor";
    c.style.cssText = `position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;${stil};pointer-events:none;z-index:9;transition:left .22s ease,top .22s ease,transform .12s`;
    document.body.appendChild(c);
  }, farbe.zeiger);
  await page.waitForTimeout(500); // Schriften und Theme-Übergang setzen sich, bevor die Uhr läuft

  const dir = mkdtempSync(join(tmpdir(), `readme-${name}-${theme}-`));
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

  // Hero-Ausschnitt: was im Bild sein soll, darf nicht unten oder oben angeschnitten sein
  const imBild = async (locator, was) => {
    const b = await locator.boundingBox();
    if (!b || b.y < 0 || b.y + b.height > hoehe) throw new Error(`ROT ${name}-${theme}: ${was} angeschnitten (y ${b?.y.toFixed(0)}…${(b?.y + b?.height).toFixed(0)}, Ausschnitt 0…${hoehe})`);
  };
  await ablauf({ frame, page, halten, zeigeAuf, klick, zeiger, mitte, imBild });
  const ende = uhr.jetzt();
  aufnahme = false;
  await schleife;
  await context.close();
  const werte = gifBauen(`${name}-${theme}`, bilder, ende, fps, dir);
  // Alte Namen ohne Theme bleiben als Kopie der hellen Fassung: PyPI und ältere
  // Release-Notes verlinken sie absolut (nur mit dem Standardmolekül der Szene)
  if (theme === "light" && !molecule) copyFileSync(werte.datei, join(assets, `demo-${name}.gif`));
  return { szene: name, theme, ...werte };
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
  const fps = werte.frames / werte.sekunden;
  if (fps < 11.5 || fps > 15.5) fehler.push(`${fps.toFixed(1)} fps außerhalb 12–15`);
  if (fehler.length) throw new Error(`ROT ${ziel}: ${fehler.join("; ")}`);
  console.log(`✔ ${ziel}: ${(werte.bytes / 1024).toFixed(0)} KB, ${werte.breite}×${werte.hoehe}, ${werte.sekunden.toFixed(2)} s, ${werte.frames} Frames`);
  return werte;
}

// Datenblatt: CAS steht oft unter der Falz — kurz oben zeigen, nötigenfalls weich bis zur CAS-Zeile scrollen,
// dann zeigt der Zeiger auf die Nummer (sonst schwebt er nach dem Scrollen über einer fremden Zeile)
async function datenblattMitCas({ frame, page, halten, zeiger }, gesamtMs) {
  const cas = frame.getByText("CAS No.", { exact: true }).first();
  if (!(await cas.count())) throw new Error("Datenblatt ohne CAS-Zeile");
  await halten(600);
  // Erst nur so weit, dass der Panel-Titel oben anliegt (über ihm steht nach einer
  // Varianten-Auswahl die Rückweg-Leiste): reicht das für die CAS-Zeile, bleibt der Titel
  // ganz im Bild — bis zum Anschlag gescrollt hätte ihn der Hero-Ausschnitt halb angeschnitten
  const höhe = page.viewportSize().height;
  const vorab = await cas.boundingBox();
  const panelOben = (await frame.locator(".molecule-panel").boundingBox()).y - 8;
  if (vorab.y + vorab.height + 24 > höhe) {
    if (panelOben > 0 && vorab.y + vorab.height + 24 - panelOben <= höhe) {
      await frame.evaluate((dy) => window.scrollBy({ top: dy, behavior: "smooth" }), panelOben);
    } else {
      await cas.evaluate((el) => el.scrollIntoView({ behavior: "smooth", block: "center" }));
    }
  }
  // Bis das weiche Scrollen steht: sonst zielt der Zeiger auf die Zeile, die beim Messen
  // gerade vorbeizog (A2-GIFs zeigten auf TPSA statt CAS)
  let b = await cas.boundingBox(), vorher = null, gewartet = 0;
  while (gewartet < 450 || !vorher || Math.abs(vorher.y - b.y) > 0.5) {
    await halten(50); gewartet += 50;
    vorher = b; b = await cas.boundingBox();
    if (gewartet > 2000) break;
  }
  const x = b.x + b.width + 190, y = b.y + b.height / 2;
  await zeiger(x, y);
  await page.mouse.move(x, y, { steps: 4 });
  await halten(Math.max(800, gesamtMs - 600 - gewartet));
}

const SZENEN = {
  // Hero links, Thalidomid: 2D → All H → 2D → Show variants → (S) mit Keil → Datenblatt
  views: {
    tool: "generate_molecule", args: { name_or_smiles: "thalidomide" }, hoehe: HERO.hoehe, fps: 15, hero: true,
    async ablauf(werkzeug) {
      const { frame, halten, klick, imBild } = werkzeug;
      const achse = frame.locator("[data-view-axis]");
      const achsenKnopf = (text) => achse.getByRole("button", { name: text, exact: true });
      const gedrückt = (text) => achse.locator('button[aria-pressed="true"][aria-busy="false"]', { hasText: text });
      await frame.locator(".structure-canvas svg").first().waitFor();
      await imBild(achse, "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await halten(1000);
      await klick(achsenKnopf("All H"), () => gedrückt("All H").waitFor({ timeout: 30000 }));
      await halten(1000);
      await klick(achsenKnopf("2D"), () => gedrückt("2D").waitFor({ timeout: 5000 }));
      await halten(800);
      await klick(frame.getByRole("button", { name: "Show variants" }), () => frame.locator("button.candidate").first().waitFor({ timeout: 30000 }));
      const s = frame.locator("button.candidate").filter({ has: frame.locator(".candidate-label", { hasText: /^\(S\)/ }) });
      if (await s.count() !== 1) throw new Error("views: kein eindeutiger (S)-Kandidat: " + (await frame.locator(".candidate-label").allInnerTexts()).join(" · "));
      await klick(s, () => frame.getByRole("button", { name: "All candidates" }).waitFor({ timeout: 30000 }));
      await halten(1500);
      await klick(frame.getByRole("tab", { name: "Data", exact: true }), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }));
      await datenblattMitCas(werkzeug, 2000);
    },
  },
  // Hero rechts, Thalidomid: 3D-Chip → Einblend-Drehung → zwei Drehzüge per Pointer-Drag → Ruhe
  "3d": {
    tool: "generate_molecule", args: { name_or_smiles: "thalidomide" }, hoehe: HERO.hoehe, fps: 12, hero: true,
    async ablauf({ frame, page, halten, klick, zeiger, mitte, imBild }) {
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(800);
      await klick(frame.getByRole("button", { name: "3D", exact: true }), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }));
      await imBild(frame.locator("[data-view-3d]"), "3D-Kuhle");
      await imBild(frame.locator("[data-view-axis]"), "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".molecule-panel"), "Panel samt Drag-Hinweis");
      await halten(1300); // Einblend-Drehung (1200 ms) läuft zu Ende
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
      await zug([cx - 150, cy], [cx + 150, cy + 20], 1800); // waagerecht: um die senkrechte Achse
      await zug([cx + 20, cy - 130], [cx - 20, cy + 130], 1600); // senkrecht: um die waagerechte Achse
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

// Argumente: Szenennamen, --theme light|dark, --molecule NAME (auch --x=wert)
const gewählt = [], optionen = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  const m = a.match(/^--(theme|molecule)(?:=(.*))?$/);
  if (m) optionen[m[1]] = m[2] ?? process.argv[++i];
  else if (a.startsWith("--")) throw new Error(`unbekannte Option: ${a} (--theme, --molecule)`);
  else gewählt.push(a);
}
if (optionen.theme && !THEMES[optionen.theme]) throw new Error(`--theme light|dark, nicht ${optionen.theme}`);
const themes = optionen.theme ? [optionen.theme] : Object.keys(THEMES);
const szenen = gewählt.length ? gewählt : Object.keys(SZENEN);
for (const name of szenen) if (!SZENEN[name]) throw new Error(`unbekannte Szene: ${name} (views, 3d, molecule)`);
mkdirSync(assets, { recursive: true });
const browser = await chromium.launch();
const ergebnisse = [];
try {
  for (const theme of themes) {
    for (const name of szenen) {
      console.log(`▶ ${name} (${theme})`);
      ergebnisse.push(await szene(browser, { name, theme, molecule: optionen.molecule, ...SZENEN[name] }));
    }
  }
} finally {
  await browser.close();
  await client.close();
}
console.table(ergebnisse.map(({ datei, ...w }) => ({ datei: datei.replace(repo + "/", ""), ...w })));
// Hero-Paar: jede Hero-Fassung hat exakt den HERO-Ausschnitt — damit sind views und 3d
// gleich groß, auch wenn sie in getrennten Läufen entstehen
const falsch = ergebnisse.filter((e) => SZENEN[e.szene].hero && (e.breite !== HERO.breite || e.hoehe !== HERO.hoehe));
if (falsch.length) {
  console.error(`ROT: Hero-GIFs nicht ${HERO.breite}×${HERO.hoehe}: ` + falsch.map((e) => `${e.szene}-${e.theme} ${e.breite}×${e.hoehe}`).join(", "));
  process.exit(1);
}
