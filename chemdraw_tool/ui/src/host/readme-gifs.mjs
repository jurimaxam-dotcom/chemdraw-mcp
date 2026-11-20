// README-GIFs aus dem echten Panel: derselbe Host-Aufbau wie host.e2e.mjs (sandboxed
// srcdoc-iframe, echte AppBridge, echter MCP-Server im MVP-Profil), helles und dunkles
// Theme, 600 px Panelbreite wie in Claude Desktop. Aufgenommen wird eine Screenshot-Serie mit
// Zeitstempeln; während das Panel auf den Server wartet (PubChem, 3D-Konformer), läuft die
// Filmuhr nicht — Ladeframes kommen gar nicht erst ins Bild, statt nachträglich
// herausgeschnitten zu werden. ffmpeg baut daraus GIFs mit eigener Palette.
// usage: npm run readme:gifs [-- views 3d molecule hero-capsaicin hero-caffeine-3d lysozyme-cartoon] [--theme light|dark] [--molecule NAME]
//        npm run panel:clips  (= --video: mp4-Rohmaterial für die Shorts, siehe unten)
//        (Netz nötig: PubChem; ohne --theme entstehen beide Fassungen)
// README-0.10-Szenen (hero-capsaicin, hero-caffeine-3d, lysozyme-cartoon): nur hell, Ausgabe assets/<szene>.gif,
// nicht im --video-Durchlauf ohne Szenennamen (zu kurz für die Shorts).
// Ausgabe: assets/demo-<szene>-<theme>.gif (helle Fassung zusätzlich als demo-<szene>.gif) — die zwei Hero-Szenen (views, 3d) haben einen
// festen Ausschnitt (HERO), damit sie im README nebeneinander auf gleicher Höhe enden.
// Bluesky-Szenen (sugar-views, mechanism-steps, reaction-balance, antibody-scheme, lysozyme-zoom, anki): nur hell,
// nur auf Ansage (nie im Lauf ohne Szenennamen), Ausgabe nach GIF_AUSGABE=<ordner> (sonst assets/), z. B.
//   GIF_AUSGABE=~/Documents/projects/chemdraw-vermarktung/out/bluesky-0.10.0 npm run readme:gifs -- sugar-views
// --video: dieselben Szenen und Klickfolgen als mp4 (H.264, yuv420p, 30 fps, 1080 px breit) für die
// Remotion-Montage in chemdraw-vermarktung — aufgenommen mit deviceScaleFactor 2 (600 → 1200 px, auf
// 1080 skaliert, damit die Schrift im 1080×1920-Short scharf bleibt), längere Haltezeiten, keine
// 10-s-Kappe. Je Clip <szene>-<theme>.mp4, .beats.json (Klickzeiten in Sekunden) und .png (Standbild bei
// 40 %) nach ~/Documents/projects/chemdraw-vermarktung/out/panel-clips/ (dort nicht versioniert).
// --feed: Clips für Feed-Posts (Jay 17.11.2026: „mindestens 60 FPS“, hell, 4:5). Gesteuerte Uhr statt
// Echtzeit-Screenshots: Playwrights page.clock fälscht Timer, rAF und Date auch im srcdoc-iframe, CSS-
// Übergänge werden über document.getAnimations() angehalten und je Bild um 1/60 s vorgerückt, Zeiger und
// Drehzüge rechnet das Skript je Bild. Dadurch ist jedes Bild ein eigener Zustand, egal wie lange der
// Screenshot dauert. 1080×1350 (4:5), Panel 600 px mittig, Rand in Panelfarbe, 6–12 s. Ohne --theme hell.
// --feed --theme dark (20.11.2026): dunkel wie im Chat von Claude Desktop — der Host meldet Desktops Flächen-
// und Textfarben als Stilvariablen (FEED_CHAT.dark, an Chat-Standbildern gemessen) und den Modus `inline`
// (Vergrößern-Knopf im Panelkopf). --bild0 schreibt je Szene nur <clip>.bild0.png (Ruhelage, zum Vergleich
// mit einem Standbild) und nimmt keinen Clip auf.
// Szene mit Molekül als `szene@molekül`; Ausgabe <molekül>-<szene>.mp4 (+ .beats.json, .kontakt.png) nach
// CLIP_AUSGABE (sonst chemdraw-vermarktung/out/clips-60fps-0.11.0). Ein roter Clip bricht den Lauf nicht ab.
//   npm run readme:gifs -- --feed anki@"penicillin G" 3d@geosmin study@serotonin
// Kerntool-Schleifen (kern-molecule, kern-3d, kern-compare, kern-reaction, kern-mechanism): feste Argumente,
// Bild 0 = Ruhelage = letztes Bild; die Naht wird an den Quellbildern gemessen und steht in .beats.json.
//   CLIP_AUSGABE=<ordner> npm run readme:gifs -- --feed [--chat | --theme dark] kern-molecule kern-3d kern-compare kern-reaction kern-mechanism
// Andere Argumente aus einer Datei: --args <datei.json> mit { "<clip>": toolArguments }, genau eine Kern-Szene:
//   CLIP_AUSGABE=<ordner> npm run readme:gifs -- --feed --chat --args wirkstoffe.json kern-3d   → <clip>-3d.*
// Die Argumente sind die, die Claude Desktop am 20.11.2026 im Chat übergeben hat (dieselbe Ansicht wie dort):
// `args` aus dem hellen Chat (abends), `argsDunkel` aus dem dunklen (morgens), wo sie abweichen. --chat: hell im
// Desktop-Stil (Stilvariablen, 622 px) — so blendet der Schnitt vom hellen Chat-Panel nahtlos auf Bild 0.
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, statSync, writeFileSync, copyFileSync, readFileSync } from "node:fs";
import { tmpdir, homedir } from "node:os";
import { execFileSync, spawnSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const assets = join(repo, "assets");
const FFMPEG = existsSync("/opt/homebrew/bin/ffmpeg") ? "/opt/homebrew/bin/ffmpeg" : "ffmpeg";
const FFPROBE = existsSync("/opt/homebrew/bin/ffprobe") ? "/opt/homebrew/bin/ffprobe" : "ffprobe";
const BREITE_DESKTOP = 600; // Panelbreite in Claude Desktop (Vorgabe; README-0.10-Szenen setzen `breite` selbst)
// Seitenhintergrund = Panel-Hintergrund des Themes (styles.css --bg; host.e2e prüft rgb(32, 39, 36))
const THEMES = {
  light: { hintergrund: "#fafbf9", zeiger: "background:rgba(30,36,33,.28);border:2px solid #1e2421;box-shadow:0 1px 4px rgba(0,0,0,.25)" },
  dark: { hintergrund: "#202724", zeiger: "background:rgba(240,240,240,.45);border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.6)" },
};
// Fester Ausschnitt der Hero-Szenen: beide GIFs exakt gleich groß (Jay 07.11.). 936 px = 3D-Panel
// nach dem Umbau 17.11.2026 (Bühne über die volle Breite, Kennwerte darunter, Fußzeile; endet bei
// ~923 px) plus 12 px Rand unten wie oben; vorher 880.
// Feed dunkel: was Claude Desktop dem Panel im dunklen Chat als Host-Stil mitgibt — gemessen an fünf
// Chat-Standbildern vom 20.11.2026 (Panelfläche 46/46/44, Reitergruppe 56/56/54, Nebentext ~203, Linien ~115).
// Gehört in die Aufnahme, nicht ins Panel: styles.css behält seine eigenen Ersatzfarben. Die Schrift des
// Hosts (--font-sans) wird nicht nachgebildet.
// `breite`: so breit stand das Panel im Chat (1244 Gerätepixel bei 2×). Über 619 px gilt das breite Layout
// (Kennwerte in einer Zeile, Bühne 320 px) — mit 600 px zeigte der Clip das schmale, das Desktop dort nicht zeigt.
// Feed hell im Chat-Stil (--chat, 20.11.2026): dasselbe für den hellen Chat, gemessen an fünf hellen
// Chat-Standbildern vom 20.11.2026 (Panelfläche 253, Reitergruppe 242, Trennlinie 178, Titel ~10, Nebentext ~48);
// das Panel steht dort genauso breit (Reitergruppe x 797–1209 in beiden Themen).
const FEED_CHAT = {
  dark: { breite: 622, hintergrund: "#2e2e2c", flaeche: "rgb(46, 46, 44)",
    variablen: { "--color-background-primary": "#2e2e2c", "--color-background-secondary": "#383836",
      "--color-text-primary": "#ffffff", "--color-text-secondary": "#cbcbc9", "--color-border-primary": "#737370" } },
  light: { breite: 622, hintergrund: "#fdfdfd", flaeche: "rgb(253, 253, 253)",
    variablen: { "--color-background-primary": "#fdfdfd", "--color-background-secondary": "#f2f2f2",
      "--color-text-primary": "#0a0a0a", "--color-text-secondary": "#303030", "--color-border-primary": "#b2b2b2" } },
};
const HERO = { breite: BREITE_DESKTOP, hoehe: Number(process.env.HERO_HOEHE || 936) };
const GRENZEN = { breite: 800, sekunden: 10, bytes: 3 * 1024 * 1024 };

// Argumente: Szenennamen, --theme light|dark, --molecule NAME (auch --x=wert), --video
const gewählt = [], optionen = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  const m = a.match(/^--(theme|molecule|args)(?:=(.*))?$/);
  if (m) optionen[m[1]] = m[2] ?? process.argv[++i];
  else if (a === "--video") optionen.video = true;
  else if (a === "--feed") optionen.feed = true;
  else if (a === "--bild0") optionen.bild0 = true;
  else if (a === "--chat") optionen.chat = true;
  else if (a.startsWith("--")) throw new Error(`unbekannte Option: ${a} (--theme, --molecule, --video, --feed, --bild0, --chat, --args)`);
  else gewählt.push(a);
}

// Aufnahmemodus: GIF fürs README oder mp4-Rohmaterial für die Shorts. `takt` sind die Haltezeiten
// der Szenen (ms); die GIF-Werte sind genau die bisherigen, Video hält länger (Klick-Pause 1,2 s,
// Schlussstand 3 s), damit Einblendungen der Montage Platz haben.
const MODI = {
  gif: { scale: 1, ausgabe: process.env.GIF_AUSGABE || assets, bild: "png", screenshot: {},
    takt: { vorKlick: 120, start: 800, startViews: 1000, nachAllH: 1000, nach2D: 800, nachS: 1500, hover: 800, vor3D: 1300, zwischenZügen: 0, schluss3d: 1500, schlussDaten: 2000 } },
  video: { scale: 2, fps: 30, bild: "jpg", screenshot: { type: "jpeg", quality: 95 }, ausgabe: join(homedir(), "Documents", "projects", "chemdraw-vermarktung", "out", "panel-clips"),
    breite: 1080, sekunden: [12, 25],
    takt: { vorKlick: 1200, start: 1500, startViews: 1500, nachAllH: 1200, nach2D: 1200, nachS: 1500, hover: 1200, vor3D: 2000, zwischenZügen: 1200, schluss3d: 3000, schlussDaten: 3000 } },
  feed: { scale: 2, fps: 60, bild: "jpg", screenshot: { type: "jpeg", quality: 95 },
    ausgabe: process.env.CLIP_AUSGABE || join(homedir(), "Documents", "projects", "chemdraw-vermarktung", "out", "clips-60fps-0.11.0"),
    breite: 1080, hoehe: 1350, sekunden: [6, 12], mindestBilder: 55,
    takt: { vorKlick: 250, start: 700, startViews: 800, nachAllH: 900, nach2D: 600, nachS: 1200, hover: 700, vor3D: 1300, zwischenZügen: 300, schluss3d: 1500, schlussDaten: 1800 } },
};
const FEED = !!optionen.feed;
if (FEED && optionen.video) throw new Error("--feed und --video schließen sich aus");
const MODUS = FEED ? MODI.feed : optionen.video ? MODI.video : MODI.gif;
const TAKT = MODUS.takt;

const hostJs = join(mkdtempSync(join(tmpdir(), "readme-host-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: hostJs, logLevel: "error" });

const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const wegwerfHome = mkdtempSync(join(tmpdir(), "readme-home-"));
const client = new Client({ name: "readme-gifs", version: "0.0.0" });
// Matplotlib baut im Wegwerf-HOME seinen Schriftcache neu (35 s, 20.11.2026: erster Toolaufruf lief ins 60-s-Limit);
// der vorhandene Cache des Rechners wird nur gelesen
const mplCache = process.env.MPLCONFIGDIR || (existsSync(join(homedir(), ".matplotlib")) ? join(homedir(), ".matplotlib") : undefined);
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "mvp", ...(mplCache ? { MPLCONFIGDIR: mplCache } : {}) }, cwd: repo }));
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

async function szene(browser, { name, tool, args, hoehe, videoHoehe, fps, ablauf, theme, molecule,
  breite: BREITE = BREITE_DESKTOP, panel = ".molecule-panel", vorlauf, datei, farben = 128, sekunden, feedHoehe, clip, inhalt, festeArgs, nahtlos, argsDunkel }) {
  if (FEED && theme === "dark" && argsDunkel) args = argsDunkel; // dunkler Chat vom 20.11. hatte andere Argumente
  if (FEED) return feedSzene(browser, { theme, nahtlos, name, tool, args, hoehe: feedHoehe ?? videoHoehe ?? hoehe, ablauf, molecule: festeArgs ? undefined : molecule, breite: BREITE, panel, vorlauf, clip, inhalt });
  if (optionen.video) { hoehe = videoHoehe ?? hoehe; fps = MODUS.fps; }
  if (molecule) args = mitName(tool, args, molecule);
  const farbe = THEMES[theme];
  const toolDef = (await client.listTools()).tools.find((t) => t.name === tool);
  const toolResult = neutral(await client.callTool({ name: tool, arguments: args }));
  if (toolResult.isError) throw new Error(`${tool}: ` + JSON.stringify(toolResult.content).slice(0, 300));
  const html = (await client.readResource({ uri: toolDef._meta.ui.resourceUri })).contents[0].text;

  const context = await browser.newContext({ viewport: { width: BREITE, height: hoehe }, deviceScaleFactor: MODUS.scale, colorScheme: theme });
  const page = await context.newPage();
  // Nie Anki starten (wie host.e2e.mjs): der Knopf schickt deliver "open", der Server bekommt "apkg"
  // und schreibt das Deck nur in den Wegwerf-HOME
  await page.exposeFunction("__callTool", async (p) => {
    if (p.name === "export_anki_deck") p = { ...p, arguments: { ...p.arguments, deliver: "apkg" } };
    return neutral(await client.callTool(p));
  });
  await page.setContent(`<body style="margin:0;background:${farbe.hintergrund}"></body>`);
  await page.addScriptTag({ path: hostJs });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput: args, toolResult });
  await page.locator("iframe").evaluate((el, [w, h]) => { el.style.width = `${w}px`; el.style.height = `${h}px`; el.style.display = "block"; }, [BREITE, hoehe]);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  // Desktop setzt das Theme als Host-Vorgabe; das Panel liest data-theme (auch "light"
  // ausdrücklich setzen: styles.css schaltet sonst per prefers-color-scheme)
  await frame.locator(panel).first().waitFor({ timeout: 30000 });
  await frame.evaluate((t) => document.documentElement.setAttribute("data-theme", t), theme);
  // Playwright-Screenshots zeigen keinen Mauszeiger: Kreis im Elternfenster über dem iframe
  await page.evaluate((stil) => {
    const c = document.createElement("div");
    c.id = "cursor";
    c.style.cssText = `position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;${stil};pointer-events:none;z-index:9;transition:left .22s ease,top .22s ease,transform .12s`;
    document.body.appendChild(c);
  }, farbe.zeiger);
  await page.waitForTimeout(500); // Schriften und Theme-Übergang setzen sich, bevor die Uhr läuft
  // Vorlauf ohne Aufnahme: z. B. bis die Protein-Engine steht und ihre Einblend-Drehung ausgelaufen ist
  if (vorlauf) await vorlauf({ frame, page });

  const dir = mkdtempSync(join(tmpdir(), `readme-${name}-${theme}-`));
  const uhr = filmuhr();
  const bilder = [];
  let aufnahme = true;
  const schleife = (async () => {
    while (aufnahme) {
      if (!uhr.läuft) { await page.waitForTimeout(10); continue; }
      const t = uhr.jetzt();
      const file = join(dir, `f${String(bilder.length).padStart(4, "0")}.${MODUS.bild}`);
      // Bricht die Szene mit einem Fehler ab, schließt der Kontext, bevor die Schleife endet —
      // dann darf der Screenshot-Fehler den eigentlichen Szenenfehler nicht verdecken.
      try {
        await page.screenshot({ path: file, clip: { x: 0, y: 0, width: BREITE, height: hoehe }, ...MODUS.screenshot });
      } catch (e) {
        if (!aufnahme || page.isClosed()) break;
        throw e;
      }
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
  // Beats für die Remotion-Montage: Filmzeit (= Sekunde im Clip), weil Wartezeiten herausgeschnitten sind
  const beats = [{ art: "panel", t: 0 }];
  const marke = (art, ziel) => beats.push({ art, t: Math.round(uhr.jetzt()) / 1000, ...(ziel ? { ziel } : {}) });
  const zeigeAuf = async (locator, ziel) => {
    const [x, y] = await mitte(locator);
    await zeiger(x, y);
    await page.mouse.move(x, y, { steps: 8 });
    await halten(220); // Zeiger-Übergang .22 s
    if (ziel) marke("hover", ziel);
  };
  // Klick mit kurzer Pause davor; bis `fertig` sichtbar ist, steht die Filmuhr
  const klick = async (locator, fertig, ziel) => {
    await zeigeAuf(locator);
    await halten(TAKT.vorKlick);
    await page.evaluate(() => { document.getElementById("cursor").style.transform = "scale(.7)"; });
    await halten(100);
    marke("klick", ziel);
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
  const fahreZu = async (x, y) => { await zeiger(x, y); await page.mouse.move(x, y, { steps: 4 }); };
  await ablauf({ frame, page, halten, zeigeAuf, klick, zeiger, mitte, imBild, marke, fahreZu });
  const ende = uhr.jetzt();
  marke("ende");
  aufnahme = false;
  await schleife;
  await context.close();
  const quellFps = Number((bilder.length / (ende / 1000)).toFixed(1));
  if (optionen.video) return { szene: name, theme, quellFps, ...videoBauen(`${name}-${theme}`, bilder, ende, dir, hoehe, beats, { tool, args }, BREITE) };
  // Szene mit eigenem Dateinamen in beiden Themen: <datei>-<theme>.gif, die helle zusätzlich als <datei>.gif
  const beideThemen = datei && (SZENEN[name].themes?.length ?? 0) > 1;
  const werte = gifBauen(datei ? (beideThemen ? `${datei}-${theme}` : datei) : `demo-${name}-${theme}`, bilder, ende, fps, dir, farben, sekunden);
  if (beideThemen && theme === "light" && !molecule) copyFileSync(werte.datei, join(MODUS.ausgabe, `${datei}.gif`));
  // Alte Namen ohne Theme bleiben als Kopie der hellen Fassung: PyPI und ältere
  // Release-Notes verlinken sie absolut (nur mit dem Standardmolekül der Szene)
  if (theme === "light" && !molecule && !datei) copyFileSync(werte.datei, join(MODUS.ausgabe, `demo-${name}.gif`));
  return { szene: name, theme, ...werte };
}

// Feed-Clip mit gesteuerter Uhr: ein Bild = Uhr 1/60 s weiter, CSS-Übergänge 1/60 s weiter, Screenshot.
// Gewartet (Server, PubChem) wird mit tickender Uhr, aber ohne Aufnahme.
const NUR_BILD0 = Symbol("nur Bild 0");
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
// `szene@name`: das Protein-Werkzeug liest `name`, alle anderen `name_or_smiles`
const mitName = (tool, args, name) => (tool === "generate_protein_or_antibody" ? { ...args, name } : { ...args, name_or_smiles: name });
// `clip`: fester Dateiname (Szenen ohne `name_or_smiles`); `inhalt`: Höhe des Panel-iframes, wenn das Panel
// niedriger ist als der 4:5-Ausschnitt — es steht dann senkrecht mittig statt oben mit leerer Fläche darunter.
async function feedSzene(browser, { name, tool, args, hoehe, ablauf, molecule, breite: BREITE, panel, vorlauf, clip, inhalt, nahtlos, theme = "light" }) {
  if (molecule) args = mitName(tool, args, molecule);
  // Chat-Stil: dunkel immer, hell mit --chat. Hell ohne --chat bleibt wie bisher (600 px, ohne Host-Kontext).
  const chat = theme === "dark" || optionen.chat ? FEED_CHAT[theme] : null;
  if (chat) { BREITE = chat.breite; hoehe = Math.max(hoehe, (BREITE * 5) / 4); } // 4:5 muss das Panel in der Breite fassen
  const farbe = chat ? { ...THEMES[theme], hintergrund: chat.hintergrund } : THEMES.light;
  // Host-Kontext wie Desktop im Chat (Stilvariablen, `inline` mit Vergrößern-Knopf)
  const hostContext = chat ? { theme, displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"], platform: "desktop",
    containerDimensions: { width: BREITE, maxHeight: 6000 }, styles: { variables: chat.variablen } } : undefined;
  const clipName = clip ?? `${slug(molecule ?? args.name_or_smiles ?? args.name ?? tool)}-${name}`;
  const H = Math.ceil(Math.max(hoehe, 750) / 5) * 5, W = (H * 4) / 5, rand = (W - BREITE) / 2;
  const toolDef = (await client.listTools()).tools.find((t) => t.name === tool);
  const toolResult = neutral(await client.callTool({ name: tool, arguments: args }));
  if (toolResult.isError) throw new Error(`${tool}: ` + JSON.stringify(toolResult.content).slice(0, 300));
  const html = (await client.readResource({ uri: toolDef._meta.ui.resourceUri })).contents[0].text;

  const context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: MODUS.scale, colorScheme: theme });
  await context.clock.install({ time: 0 });
  await context.clock.pauseAt(1000);
  // Griff auf die Mol*-Engine im Panel (nur Aufnahme): create() wird umwickelt, sobald das Engine-Script
  // window.__chemCartoon setzt — so setzt die Szene `protein` die Kamera Bild für Bild selbst
  await context.addInitScript(() => {
    let engine;
    Object.defineProperty(window, "__chemCartoon", { configurable: true, get: () => engine, set(v) {
      engine = { ...v, async create(...a) { const h = await v.create(...a); (window.__cartoonGriffe ||= []).push(h); return h; } };
    } });
  });
  const page = await context.newPage();
  await page.exposeFunction("__callTool", async (p) => {
    if (p.name === "export_anki_deck") p = { ...p, arguments: { ...p.arguments, deliver: "apkg" } };
    return neutral(await client.callTool(p));
  });
  // Uhr tickt (16 ms je Runde), bis `fertig` erfüllt ist — Timer im Panel laufen weiter, aufgenommen wird nichts
  const mitTick = async (versprechen, ms = 60000) => {
    let da = false, fehler = null;
    versprechen.then(() => { da = true; }, (e) => { fehler = e; da = true; });
    const bis = Date.now() + ms;
    while (!da) {
      if (Date.now() > bis) throw new Error(`${name}: Zeitüberschreitung beim Warten`);
      await context.clock.runFor(16);
      await page.waitForTimeout(10);
    }
    if (fehler) throw fehler;
  };
  await page.setContent(`<body style="margin:0;background:${farbe.hintergrund}"></body>`);
  await page.addScriptTag({ path: hostJs });
  await page.evaluate((a) => window.__startHost(a), { html, toolInput: args, toolResult, hostContext });
  const oben = inhalt ? Math.round((H - inhalt) / 2) : 0;
  if (oben < 0) throw new Error(`${name}: inhalt ${inhalt} höher als der Ausschnitt ${H}`);
  await page.locator("iframe").evaluate((el, [w, h, r, o]) => { Object.assign(el.style, { width: `${w}px`, height: `${h}px`, display: "block", marginLeft: `${r}px`, marginTop: `${o}px` }); }, [BREITE, inhalt ?? H, rand, oben]);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  await mitTick(frame.locator(panel).first().waitFor({ timeout: 60000 }));
  await frame.evaluate((t) => document.documentElement.setAttribute("data-theme", t), theme);
  if (chat) {
    const bg = await frame.evaluate(() => getComputedStyle(document.body).backgroundColor);
    if (bg !== chat.flaeche) throw new Error(`ROT ${name}: Panelfläche ${bg} statt ${chat.flaeche} — Host-Stilvariablen nicht angekommen`);
  }
  await page.evaluate((stil) => {
    const c = document.createElement("div");
    c.id = "cursor";
    c.style.cssText = `position:fixed;left:-40px;top:-40px;width:18px;height:18px;border-radius:50%;${stil};pointer-events:none;z-index:9;transition:none`;
    document.body.appendChild(c);
  }, farbe.zeiger);
  await mitTick(page.waitForTimeout(500)); // Schriften und Theme setzen sich
  if (vorlauf) {
    await mitTick(vorlauf({ frame, page }));
    // Übergänge, die der Vorlauf angestoßen hat, auslaufen lassen: sonst hält `schritt` sie beim ersten Bild an
    // und spielt sie von vorn — Bild 0 wäre nicht die Ruhelage (kern-mechanism: Naht 0,096 statt 0)
    const auslaufen = () => { for (const a of document.getAnimations()) { try { a.finish(); } catch { /* endlose Animation */ } } };
    await frame.evaluate(auslaufen);
    await page.evaluate(auslaufen);
  }

  const dir = mkdtempSync(join(tmpdir(), `feed-${name}-`));
  let nr = 0, sollMs = 0;
  // CSS-Übergänge und -Animationen: neu entdeckte anhalten, dann alle um dt vorrücken
  const schritt = (dt) => {
    for (const a of document.getAnimations()) {
      if (a.__t === undefined) { a.pause(); a.__t = 0; }
      a.__t += dt;
      const ende = a.effect?.getComputedTiming().endTime;
      if (Number.isFinite(ende) && a.__t >= ende) a.finish(); else a.currentTime = a.__t;
    }
  };
  const bild = async () => {
    const neu = Math.round(((nr + 1) * 1000) / MODUS.fps), dt = neu - sollMs;
    sollMs = neu;
    await context.clock.runFor(dt);
    await page.evaluate(schritt, dt);
    await frame.evaluate(schritt, dt);
    await page.screenshot({ path: join(dir, `f${String(nr).padStart(5, "0")}.jpg`), clip: { x: 0, y: 0, width: W, height: H }, ...MODUS.screenshot });
    if (optionen.bild0) {
      await page.screenshot({ path: join(MODUS.ausgabe, `${clipName}.bild0.png`), clip: { x: 0, y: 0, width: W, height: H } });
      throw NUR_BILD0;
    }
    nr++;
  };
  const halten = async (ms) => { for (let i = Math.round((ms * MODUS.fps) / 1000); i > 0; i--) await bild(); };
  let pos = [W + 30, H * 0.6]; // Zeiger kommt von rechts ins Bild
  // Clip-Pixel = CSS-Pixel × Ausgabebreite / Seitenbreite (der 2×-Master: × deviceScaleFactor)
  const k = MODUS.breite / W, px = (v) => Math.round(v * k);
  const rechtecke = {};
  // Rechteck aus einer boundingBox oder einem Locator (fehlt das Element, ist die Szene rot — die Montage schneidet danach)
  const rechteck = async (schlüssel, b) => {
    if (b && typeof b.boundingBox === "function") {
      if (await b.count() < 1) throw new Error(`ROT ${name}: Rechteck ${schlüssel} ohne Element`);
      b = await b.first().boundingBox();
    }
    if (b) rechtecke[schlüssel] = { x: px(b.x), y: px(b.y), width: px(b.width), height: px(b.height) };
  };
  const beats = [{ art: "panel", t: 0, zeiger: pos.map(px) }], bewegungen = [];
  const marke = (art, ziel) => beats.push({ art, t: Number((nr / MODUS.fps).toFixed(3)), ...(ziel ? { ziel } : {}), zeiger: pos.map(px) });
  const zeiger = (x, y) => { pos = [x, y]; return page.evaluate(([x, y]) => { const s = document.getElementById("cursor").style; s.left = `${x - 9}px`; s.top = `${y - 9}px`; }, [x, y]); };
  // Zeigerfahrt Bild für Bild; 70 % Ease + 30 % linear, damit auch die letzten Bilder sich sichtbar bewegen
  const fahreZu = async (x, y) => {
    const [x0, y0] = pos, weg = Math.hypot(x - x0, y - y0);
    if (weg < 1) return;
    const n = Math.round((Math.min(750, Math.max(350, weg * 1.4)) * MODUS.fps) / 1000), von = nr;
    for (let i = 1; i <= n; i++) {
      const a = i / n, e = 0.7 * (0.5 - Math.cos(Math.PI * a) / 2) + 0.3 * a;
      const px = x0 + (x - x0) * e, py = y0 + (y - y0) * e;
      await page.mouse.move(px, py);
      await zeiger(px, py);
      await bild();
    }
    bewegungen.push({ art: "zeiger", von, bis: nr });
  };
  const mitte = async (locator) => { const b = await locator.boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
  const zeigeAuf = async (locator, ziel) => { await fahreZu(...(await mitte(locator))); await halten(120); if (ziel) marke("hover", ziel); };
  const klick = async (locator, fertig, ziel) => {
    await zeigeAuf(locator);
    await halten(TAKT.vorKlick);
    await page.evaluate(() => { document.getElementById("cursor").style.transform = "scale(.7)"; });
    await halten(100);
    marke("klick", ziel);
    await mitTick(locator.click());
    await page.evaluate(() => { document.getElementById("cursor").style.transform = ""; });
    if (fertig) await mitTick(fertig());
  };
  // Drehzug: ein Mausschritt je Bild
  const ziehenFeed = async (von, nach, ms, ziel) => {
    await fahreZu(...von); await halten(320);
    marke("klick", ziel);
    await page.mouse.down();
    const n = Math.round((ms * MODUS.fps) / 1000), start = nr;
    for (let i = 1; i <= n; i++) {
      const x = von[0] + (nach[0] - von[0]) * (i / n), y = von[1] + (nach[1] - von[1]) * (i / n);
      await page.mouse.move(x, y);
      await zeiger(x, y);
      await bild();
    }
    await page.mouse.up();
    bewegungen.push({ art: "drag", von: start, bis: nr });
  };
  // Bewegung ohne Zeiger (z. B. Mol*-Spin): Bilder aufnehmen und als Bewegungsstrecke zählen
  // jeBild(anteil) setzt den Zustand vor dem Bild (anteil 0 … (n−1)/n), nachBild() misst danach
  const drehen = async (ms, jeBild, nachBild, art = "drehung") => {
    const von = nr, n = Math.round((ms * MODUS.fps) / 1000);
    for (let i = 0; i < n; i++) { await jeBild?.(i / n); await bild(); await nachBild?.(); }
    bewegungen.push({ art, von, bis: nr });
  };
  const zeigerStart = [...pos];
  // Weich scrollen, Bild für Bild (scroll-behavior: smooth liefe in Echtzeit)
  const scrollen = async (dy, ms = 600) => {
    const y0 = await frame.evaluate(() => window.scrollY), n = Math.round((ms * MODUS.fps) / 1000), von = nr;
    for (let i = 1; i <= n; i++) {
      const e = 0.5 - Math.cos((Math.PI * i) / n) / 2;
      await frame.evaluate((y) => window.scrollTo(0, y), y0 + dy * e);
      await bild();
    }
    bewegungen.push({ art: "scroll", von, bis: nr });
  };
  const imBild = async (locator, was) => {
    const b = await locator.boundingBox();
    if (!b || b.y < oben || b.y + b.height > oben + (inhalt ?? H)) throw new Error(`ROT ${name}: ${was} angeschnitten (y ${b?.y.toFixed(0)}…${(b?.y + b?.height).toFixed(0)}, Ausschnitt ${oben}…${oben + (inhalt ?? H)})`);
  };
  try {
    await ablauf({ feed: true, oben, hoeheAusschnitt: inhalt ?? H, drehen, zeigerStart, rechteck, frame, page, halten, zeigeAuf, klick, zeiger, mitte, imBild, marke, fahreZu, ziehenFeed, scrollen, bild, mitTick });
    marke("ende");
  } catch (e) {
    if (e !== NUR_BILD0) throw e;
    return { szene: name, theme, datei: join(MODUS.ausgabe, `${clipName}.bild0.png`) };
  } finally {
    await context.close();
  }
  return { szene: name, theme, ...feedVideo(clipName, dir, nr, beats, bewegungen, { tool, args }, rechtecke, nahtlos) };
}

// Verschiedene Bilder je voller Sekunde (mpdecimate „keep pts“) — dieselbe Zählung wie scripts/bilder-je-sekunde.sh
function behalteneBilder(ziel) {
  // mpdecimate schreibt seine Entscheidungen nach stderr
  const r = spawnSync(FFMPEG, ["-hide_banner", "-nostats", "-loglevel", "debug", "-i", ziel, "-vf", "mpdecimate", "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 28 });
  return [...r.stderr.matchAll(/keep pts:\S+ pts_time:([\d.]+)/g)].map((m) => Math.round(Number(m[1]) * MODUS.fps));
}

// Helligkeitsmittel (YAVG, 0–255) des Differenzbilds — je Bildpaar der Folge und für die Naht letztes Bild → Bild 0.
// Gemessen an den Quellbildern, nicht am kodierten Clip.
const yavg = (args) => [...spawnSync(FFMPEG, ["-hide_banner", "-nostats", "-loglevel", "error", ...args, "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 28 })
  .stdout.matchAll(/YAVG=([\d.]+)/g)].map((m) => Number(m[1]));
const DRUCK = "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-";
function nahtMessen(dir, bilder, bewegungen) {
  const bildpfad = (n) => join(dir, `f${String(n).padStart(5, "0")}.jpg`);
  // schritte[i] = Unterschied Bild i → i+1
  const schritte = yavg(["-framerate", String(MODUS.fps), "-i", join(dir, "f%05d.jpg"), "-vf", `tblend=all_mode=difference,${DRUCK}`]);
  const [naht] = yavg(["-i", bildpfad(bilder - 1), "-i", bildpfad(0), "-filter_complex", `blend=all_mode=difference,${DRUCK}`]);
  const bewegt = schritte.filter((_, i) => bewegungen.some((s) => i >= s.von && i + 1 < s.bis)).sort((a, b) => a - b);
  if (naht === undefined || !bewegt.length) throw new Error(`Nahtmessung ohne Werte (naht ${naht}, ${bewegt.length} Schritte)`);
  const r = (v) => Number(v.toFixed(4));
  return { naht: r(naht), schrittMedian: r(bewegt[bewegt.length >> 1]), schrittMax: r(bewegt.at(-1)), einheit: "YAVG des Differenzbilds, 0–255, Quellbilder" };
}

function feedVideo(name, dir, bilder, beats, bewegungen, quelle, rechtecke = {}, nahtlos = false) {
  const ziel = join(MODUS.ausgabe, `${name}.mp4`);
  const naht = nahtMessen(dir, bilder, bewegungen);
  // 2×-Master in nativer Screenshot-Größe für Ausschnitte in der Montage (Vermarktung 18.11.: aus 1080 gezoomt wird es weich)
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-framerate", String(MODUS.fps), "-i", join(dir, "f%05d.jpg"),
    "-vf", "scale=out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
    "-r", String(MODUS.fps), "-movflags", "+faststart", ziel.replace(/\.mp4$/, ".master.mp4")]);
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-framerate", String(MODUS.fps), "-i", join(dir, "f%05d.jpg"),
    "-vf", `scale=${MODUS.breite}:${MODUS.hoehe}:flags=lanczos:out_range=tv,format=yuv420p`,
    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(MODUS.fps), "-movflags", "+faststart", ziel]);
  const werte = prüfenVideo(ziel, MODUS.hoehe);
  const [mb, mh] = execFileSync(FFPROBE, ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
    ziel.replace(/\.mp4$/, ".master.mp4")]).toString().trim().split(",").map(Number);
  const master = { breite: mb, hoehe: mh };
  // Messung: (1) je Bewegungsstrecke Anteil verschiedener Bilder, (2) volle Sekunden ganz in Bewegung ≥ mindestBilder
  const behalten = new Set(behalteneBilder(ziel));
  const inBewegung = (b) => bewegungen.some((s) => b >= s.von && b < s.bis);
  const sekunden = [];
  for (let s = 0; (s + 1) * MODUS.fps <= bilder; s++) {
    let n = 0, voll = true;
    for (let b = s * MODUS.fps; b < (s + 1) * MODUS.fps; b++) { if (behalten.has(b)) n++; if (!inBewegung(b)) voll = false; }
    sekunden.push({ s, verschieden: n, bewegt: voll });
  }
  const strecken = bewegungen.map((st) => {
    let n = 0;
    for (let b = st.von; b < st.bis; b++) if (behalten.has(b)) n++;
    return { ...st, bilder: st.bis - st.von, verschieden: n };
  });
  const fehler = sekunden.filter((x) => x.bewegt && x.verschieden < MODUS.mindestBilder).map((x) => `Sekunde ${x.s}: ${x.verschieden} verschiedene Bilder`);
  const kontakt = ziel.replace(/\.mp4$/, ".kontakt.png");
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-i", ziel, "-vf", `fps=${(12 / werte.sekunden).toFixed(4)},scale=270:-2:flags=lanczos,tile=4x3:padding=6:color=white`, "-frames:v", "1", kontakt]);
  writeFileSync(ziel.replace(/\.mp4$/, ".beats.json"), JSON.stringify({ clip: `${name}.mp4`, tool: quelle.tool, args: quelle.args,
    video: { breite: werte.breite, hoehe: werte.hoehe, fps: MODUS.fps, sekunden: werte.sekunden, bilder },
    master: { datei: `${name}.master.mp4`, ...master, faktor: Number((master.breite / werte.breite).toFixed(4)) }, // Master-Pixel = Clip-Pixel × faktor
    naht, rechtecke, beats, bewegungen: strecken, sekunden }, null, 2) + "\n");
  console.log(`  ${name}: verschiedene Bilder je Sekunde ${sekunden.map((x) => `${x.s}:${x.verschieden}${x.bewegt ? "*" : ""}`).join(" ")} (* = ganz in Bewegung)`);
  console.log(`  ${name}: Bewegungsstrecken ${strecken.map((x) => `${x.art} ${x.verschieden}/${x.bilder}`).join(", ")}`);
  console.log(`  ${name}: Naht letztes Bild → Bild 0 ${naht.naht}, Bewegungsschritt Median ${naht.schrittMedian} / Max ${naht.schrittMax}`);
  // Schleife: die Naht darf nicht größer sein als ein gewöhnlicher Bewegungsschritt
  if (nahtlos && naht.naht > naht.schrittMedian) fehler.push(`Naht ${naht.naht} > Bewegungsschritt (Median ${naht.schrittMedian})`);
  if (fehler.length) throw new Error(`ROT ${ziel}: ${fehler.join("; ")}`);
  return { ...werte, naht: naht.naht, schritt: naht.schrittMedian, kontakt };
}

// concat-Demuxer: jedes Bild steht bis zum nächsten Zeitstempel, das letzte bis zum Szenenende
function concatListe(name, bilder, endeMs, dir) {
  if (bilder.length < 10) throw new Error(`${name}: nur ${bilder.length} Bilder aufgenommen`);
  const zeilen = ["ffconcat version 1.0"];
  bilder.forEach((b, i) => {
    const bis = i + 1 < bilder.length ? bilder[i + 1].t : endeMs;
    zeilen.push(`file '${b.file}'`, `duration ${((bis - b.t) / 1000).toFixed(3)}`);
  });
  zeilen.push(`file '${bilder.at(-1).file}'`);
  const liste = join(dir, "liste.txt");
  writeFileSync(liste, zeilen.join("\n") + "\n");
  return liste;
}

function gifBauen(name, bilder, endeMs, fps, dir, farben, sekunden) {
  const liste = concatListe(name, bilder, endeMs, dir);
  const ziel = join(MODUS.ausgabe, `${name}.gif`);
  const filter = `fps=${fps},scale='min(${GRENZEN.breite},iw)':-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=${farben}:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`;
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", liste, "-vf", filter, "-loop", "0", ziel]);
  return prüfen(ziel, sekunden);
}

// sekunden = [min, max] je Szene (Bluesky 6–12 s), sonst die README-Kappe
function prüfen(ziel, [minS, maxS] = [0, GRENZEN.sekunden]) {
  const probe = JSON.parse(execFileSync(FFPROBE, ["-v", "error", "-count_frames", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,nb_read_frames:format=duration", "-of", "json", ziel]).toString());
  const st = probe.streams[0];
  const werte = { datei: ziel, bytes: statSync(ziel).size, breite: st.width, hoehe: st.height,
    sekunden: Number(probe.format.duration), frames: Number(st.nb_read_frames) };
  const fehler = [];
  if (werte.breite > GRENZEN.breite) fehler.push(`Breite ${werte.breite} px > ${GRENZEN.breite}`);
  if (!(werte.sekunden >= minS && werte.sekunden <= maxS)) fehler.push(`Dauer ${werte.sekunden} s außerhalb ${minS}–${maxS}`);
  if (werte.bytes > GRENZEN.bytes) fehler.push(`Größe ${(werte.bytes / 1048576).toFixed(2)} MB > 3 MB`);
  const fps = werte.frames / werte.sekunden;
  if (fps < 11.5 || fps > 15.5) fehler.push(`${fps.toFixed(1)} fps außerhalb 12–15`);
  if (fehler.length) throw new Error(`ROT ${ziel}: ${fehler.join("; ")}`);
  console.log(`✔ ${ziel}: ${(werte.bytes / 1024).toFixed(0)} KB, ${werte.breite}×${werte.hoehe}, ${werte.sekunden.toFixed(2)} s, ${werte.frames} Frames`);
  return werte;
}

// Shorts-Rohmaterial: mp4 + Beats-Sidecar + Vorschau-Standbild bei 40 %
function videoBauen(name, bilder, endeMs, dir, hoehe, beats, quelle, breite) {
  const liste = concatListe(name, bilder, endeMs, dir);
  const ziel = join(MODUS.ausgabe, `${name}.mp4`);
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", liste,
    "-vf", `fps=${MODUS.fps},scale=${MODUS.breite}:-2:flags=lanczos:out_range=tv,format=yuv420p`,
    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(MODUS.fps), "-movflags", "+faststart", ziel]);
  const werte = prüfenVideo(ziel, Math.round((hoehe * MODUS.breite) / breite / 2) * 2);
  const vorschau = ziel.replace(/\.mp4$/, ".png");
  execFileSync(FFMPEG, ["-y", "-loglevel", "error", "-ss", (werte.sekunden * 0.4).toFixed(2), "-i", ziel,
    "-frames:v", "1", "-vf", "scale=360:-2:flags=lanczos", vorschau]);
  // Flach für Menschen, `beats` in der Form von vermarktung/video/src/lib/beats.ts (Beat[])
  const flach = {};
  for (const b of beats) {
    const basis = b.art === "panel" || b.art === "ende" ? b.art : b.ziel ?? b.art;
    let k = basis;
    for (let n = 2; k in flach; n++) k = `${basis}#${n}`;
    flach[k] = b.t;
  }
  const sidecar = ziel.replace(/\.mp4$/, ".beats.json");
  writeFileSync(sidecar, JSON.stringify({
    clip: `${name}.mp4`, tool: quelle.tool, args: quelle.args,
    video: { breite: werte.breite, hoehe: werte.hoehe, fps: MODUS.fps, sekunden: werte.sekunden },
    marken: flach, beats,
  }, null, 2) + "\n");
  return { ...werte, beats: flach };
}

function prüfenVideo(ziel, sollHoehe) {
  const probe = JSON.parse(execFileSync(FFPROBE, ["-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate:format=duration", "-of", "json", ziel]).toString());
  const st = probe.streams[0];
  const werte = { datei: ziel, bytes: statSync(ziel).size, breite: st.width, hoehe: st.height,
    sekunden: Number(Number(probe.format.duration).toFixed(2)), codec: st.codec_name, pixfmt: st.pix_fmt, fps: st.r_frame_rate };
  const fehler = [];
  if (st.codec_name !== "h264") fehler.push(`Codec ${st.codec_name} statt h264`);
  if (st.pix_fmt !== "yuv420p") fehler.push(`Pixelformat ${st.pix_fmt} statt yuv420p`);
  if (st.r_frame_rate !== `${MODUS.fps}/1` || st.avg_frame_rate !== `${MODUS.fps}/1`) fehler.push(`Bildrate ${st.r_frame_rate}/${st.avg_frame_rate} statt ${MODUS.fps}/1`);
  if (st.width !== MODUS.breite) fehler.push(`Breite ${st.width} statt ${MODUS.breite}`);
  if (st.height !== sollHoehe) fehler.push(`Höhe ${st.height} statt ${sollHoehe}`);
  if (st.height > 1920) fehler.push(`Höhe ${st.height} > 1920 (passt nicht in 9:16)`);
  const [lo, hi] = MODUS.sekunden;
  if (!(werte.sekunden >= lo && werte.sekunden <= hi)) fehler.push(`Dauer ${werte.sekunden} s außerhalb ${lo}–${hi}`);
  if (fehler.length) throw new Error(`ROT ${ziel}: ${fehler.join("; ")}`);
  console.log(`✔ ${ziel}: ${(werte.bytes / 1048576).toFixed(2)} MB, ${werte.breite}×${werte.hoehe}, ${werte.sekunden} s, ${werte.fps}`);
  return werte;
}

// Datenblatt: CAS steht oft unter der Falz — kurz oben zeigen, nötigenfalls weich bis zur CAS-Zeile scrollen,
// dann zeigt der Zeiger auf die Nummer (sonst schwebt er nach dem Scrollen über einer fremden Zeile)
async function datenblattMitCas(werkzeug, gesamtMs) {
  const { frame, page, halten, zeiger, marke } = werkzeug;
  const cas = frame.getByText("CAS No.", { exact: true }).first();
  if (!(await cas.count())) throw new Error("Datenblatt ohne CAS-Zeile");
  if (werkzeug.feed) return datenblattFeed(werkzeug, cas, gesamtMs);
  await halten(600);
  marke("schluss", "data sheet");
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

// Feed: dieselbe Folge mit Bild-für-Bild-Scrollen (Titel oben anlegen oder CAS mittig), dann Zeiger auf die Nummer
async function datenblattFeed({ frame, page, halten, marke, scrollen, fahreZu }, cas, gesamtMs) {
  await halten(600);
  marke("schluss", "data sheet");
  const höhe = page.viewportSize().height;
  const vorab = await cas.boundingBox();
  const panelOben = (await frame.locator(".molecule-panel").boundingBox()).y - 8;
  let dy = 0;
  if (vorab.y + vorab.height + 24 > höhe) dy = panelOben > 0 && vorab.y + vorab.height + 24 - panelOben <= höhe ? panelOben : vorab.y + vorab.height / 2 - höhe / 2;
  if (dy > 0) await scrollen(dy);
  const b = await cas.boundingBox();
  await fahreZu(b.x + b.width + 190, b.y + b.height / 2);
  await halten(Math.max(800, gesamtMs - 600));
}

// Drehzug per Pointer-Drag, mit sichtbarem Zeiger
async function ziehen(werkzeug, von, nach, ms, ziel) {
  if (werkzeug.feed) return werkzeug.ziehenFeed(von, nach, ms, ziel);
  const { page, halten, zeiger, marke } = werkzeug;
  await zeiger(...von); await page.mouse.move(...von, { steps: 6 }); await halten(320);
  marke("klick", ziel);
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
}

// Zoom wie im Panel-Hinweis „⌘/Ctrl+scroll“: Mausrad mit gedrückter Strg-Taste über der Fläche.
// richtung -1 = hinein, +1 = heraus; feste Rastenzahl, damit „heraus“ genau „hinein“ aufhebt
async function zoomen({ page, halten, zeiger, marke }, [x, y], richtung, rasten, ziel) {
  await zeiger(x, y); await page.mouse.move(x, y, { steps: 4 }); await halten(260);
  marke("klick", ziel);
  await page.keyboard.down("Control");
  for (let i = 0; i < rasten; i++) {
    await page.mouse.wheel(0, richtung * 72);
    await halten(20);
  }
  await page.keyboard.up("Control");
}

// Protein-Panel: warten, bis die Mol*-Engine steht und ihre Einblend-Drehung ausgelaufen ist
async function proteinBereit({ frame, page }) {
  await frame.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(1800);
}

// Protein-Feed: warten, bis die Einblend-Drehung zu Ende ist. Läuft ein Kameraübergang noch, nimmt Mol*
// setState(…, 0) nicht sofort, sondern führt den Übergang weiter — Anlauf-Rampe und Bild 0 ≠ Ruhelage
// (Messung der Vermarktung, 18.11.). proteinBereit wartet in Echtzeit, die Uhr kam dabei nur ~50 ms weit.
async function cartoonSteht({ frame, page }, name) {
  for (let i = 0; ; i++) {
    const z = await frame.evaluate(() => {
      const g = window.__cartoonGriffe || [], tr = g[0]?.canvas3d.camera.transition;
      return { griffe: g.length, läuft: tr?.inTransition, t: tr?.t, start: tr?.start, dauer: tr?.durationMs, jetzt: performance.now() };
    });
    if (z.griffe === 1 && !z.läuft) return;
    if (i > 100) throw new Error(`ROT ${name}: Kameraübergang endet nicht ${JSON.stringify(z)}`);
    await page.clock.runFor(50);
  }
}

// Hülle des Proteins auf der Mol*-Fläche im jetzigen Bild (Nicht-Hintergrund-Pixel, CSS-Pixel der Fläche)
const cartoonHülleJetzt = (frame) => frame.evaluate(() => {
  const gl = window.__cartoonGriffe[0].canvas, w = gl.clientWidth, hh = gl.clientHeight;
  const k = document.createElement("canvas"); k.width = w; k.height = hh;
  const g = k.getContext("2d", { willReadFrequently: true }); g.drawImage(gl, 0, 0, w, hh);
  const d = g.getImageData(0, 0, w, hh).data, bg = [d[0], d[1], d[2]];
  let x0 = w, y0 = hh, x1 = -1, y1 = -1;
  for (let y = 0; y < hh; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4;
    if (Math.abs(d[i] - bg[0]) + Math.abs(d[i + 1] - bg[1]) + Math.abs(d[i + 2] - bg[2]) > 24) {
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
  }
  return x1 < 0 ? null : { x0, y0, x1, y1 };
});

// Sichtbarer Zug im Feed: Zeiger hin, greifen (Zeiger kleiner, solange die Taste unten ist), je Bild ein
// Mausschritt — das erste Zugbild ist schon einen Schritt weiter, das letzte steht genau auf `nach`.
// Beats „greifen“ und „loslassen“; die Strecke zählt als Bewegung `drag`.
async function zugFeed({ page, fahreZu, halten, marke, zeiger, drehen }, von, nach, ms, ziel, nachBild) {
  await fahreZu(...von);
  await halten(200);
  const gedrückt = (an) => page.evaluate((an) => { document.getElementById("cursor").style.transform = an ? "scale(.72)" : ""; }, an);
  await gedrückt(true);
  await page.mouse.down();
  await halten(100);
  marke("greifen", ziel);
  const n = Math.round((ms * MODUS.fps) / 1000);
  await drehen(ms, async (anteil) => {
    const a = (Math.round(anteil * n) + 1) / n, x = von[0] + (nach[0] - von[0]) * a, y = von[1] + (nach[1] - von[1]) * a;
    await page.mouse.move(x, y);
    await zeiger(x, y);
  }, nachBild, "drag");
  await page.mouse.up();
  marke("loslassen", ziel);
  await gedrückt(false);
}

// Bluesky-Folgeposts (0.10.0): nur hell, nur auf Ansage, 6–12 s, Ausgabe über GIF_AUSGABE
const BLUESKY = { themes: ["light"], fps: 12, nurGif: true, aufAnsage: true, sekunden: [6, 12], breite: 600 };

// README 0.10: eine zusammenhängende Interaktion je GIF, nur hell, Ausgabe unter eigenem Namen
// (assets/<datei>.gif). Breite und Höhe so, dass das ganze Panel samt Export-Knopf im Bild ist —
// abgeschnitten wird nichts; flacher wird das Bild über die Breite, nicht über einen Ausschnitt.
const README_010 = { themes: ["light"], fps: 15, nurGif: true };
// README-Galerie (17.11.2026): bewegte Fassung der Galerie-Fälle, hell UND dunkel — das README wählt per
// <picture> nach dem Thema des Lesers. Ausgabe assets/<datei>-<theme>.gif, die helle zusätzlich als
// <datei>.gif. Nur auf Ansage; für Bluesky dieselben Szenen mit --theme light und GIF_AUSGABE.
const GALERIE = { themes: ["light", "dark"], fps: 12, nurGif: true, aufAnsage: true, sekunden: [5, 12], breite: 600 };

// Kerntool-Schleifen: nur --feed, feste Argumente (kein `szene@name`), Naht letztes Bild → Bild 0 wird geprüft
const KERN = { themes: ["light"], nurGif: true, aufAnsage: true, festeArgs: true, nahtlos: true };
const nurFeed = (werkzeug, name) => { if (!werkzeug.feed) throw new Error(`Szene ${name} gibt es nur mit --feed`); };
// Zeiger zurück an den Startpunkt rechts außerhalb des Bilds: letztes Bild = erstes
const raus = async ({ fahreZu, halten, zeigerStart }) => { await fahreZu(...zeigerStart); await halten(150); };

const SZENEN = {
  // Hero links, Thalidomid: 2D → All H → 2D → Show variants → (S) mit Keil → Datenblatt
  views: {
    tool: "generate_molecule", args: { name_or_smiles: "thalidomide" }, hoehe: HERO.hoehe, videoHoehe: 890, fps: 15, hero: true, // Video: Datenblatt mit Rückweg-Leiste endet bei ~876 px
    async ablauf(werkzeug) {
      const { frame, halten, klick, imBild } = werkzeug;
      const achse = frame.locator("[data-view-axis]");
      const achsenKnopf = (text) => achse.getByRole("button", { name: text, exact: true });
      const gedrückt = (text) => achse.locator('button[aria-pressed="true"][aria-busy="false"]', { hasText: text });
      await frame.locator(".structure-canvas svg").first().waitFor();
      await imBild(achse, "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await halten(TAKT.startViews);
      await klick(achsenKnopf("All H"), () => gedrückt("All H").waitFor({ timeout: 30000 }), "All H");
      await halten(TAKT.nachAllH);
      await klick(achsenKnopf("2D"), () => gedrückt("2D").waitFor({ timeout: 5000 }), "2D");
      await halten(TAKT.nach2D);
      await klick(frame.getByRole("button", { name: "Show variants" }), () => frame.locator("button.candidate").first().waitFor({ timeout: 30000 }), "Show variants");
      const s = frame.locator("button.candidate").filter({ has: frame.locator(".candidate-label", { hasText: /^\(S\)/ }) });
      if (await s.count() !== 1) throw new Error("views: kein eindeutiger (S)-Kandidat: " + (await frame.locator(".candidate-label").allInnerTexts()).join(" · "));
      await klick(s, () => frame.getByRole("button", { name: "All candidates" }).waitFor({ timeout: 30000 }), "(S)");
      await halten(TAKT.nachS);
      await klick(frame.getByRole("tab", { name: "Data", exact: true }), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }), "Data");
      await datenblattMitCas(werkzeug, TAKT.schlussDaten);
    },
  },
  // Hero rechts, Thalidomid: 3D-Chip → Einblend-Drehung → zwei Drehzüge per Pointer-Drag → Ruhe
  "3d": {
    tool: "generate_molecule", args: { name_or_smiles: "thalidomide" }, hoehe: HERO.hoehe, fps: 12, hero: true,
    async ablauf(werkzeug) {
      const { frame, halten, klick, mitte, imBild, marke } = werkzeug;
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(TAKT.start);
      await klick(frame.getByRole("button", { name: "3D", exact: true }), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }), "3D");
      await imBild(frame.locator("[data-view-3d]"), "3D-Kuhle");
      await imBild(frame.locator("[data-view-axis]"), "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".molecule-panel"), "Panel samt Drag-Hinweis");
      // Feed-Posts zeigen am Ende den Knopf „Quiz me on …“ (S6)
      if (werkzeug.feed) await imBild(frame.getByRole("button", { name: /^Quiz me on / }), "Knopf „Quiz me on …“");
      await halten(TAKT.vor3D); // Einblend-Drehung (1200 ms) läuft zu Ende
      const [cx, cy] = await mitte(frame.locator("[data-view-3d]"));
      const zug = (von, nach, ms, ziel) => ziehen(werkzeug, von, nach, ms, ziel);
      await zug([cx - 150, cy], [cx + 150, cy + 20], 1800, "drag horizontal"); // waagerecht: um die senkrechte Achse
      if (TAKT.zwischenZügen) await halten(TAKT.zwischenZügen);
      await zug([cx + 20, cy - 130], [cx - 20, cy + 130], 1600, "drag vertical"); // senkrecht: um die waagerechte Achse
      marke("schluss", "3D model");
      await halten(TAKT.schluss3d);
    },
  },
  // Capsaicin: Maus nacheinander über die Gruppen-Chips (Gruppe leuchtet) → Datenblatt
  molecule: {
    tool: "generate_molecule", args: { name_or_smiles: "capsaicin" }, hoehe: 720, videoHoehe: 830, fps: 15, // Video: 830 px = ganzes Datenblatt samt Fußzeile (Footer endet bei ~811 px)
    async ablauf(werkzeug) {
      const { frame, halten, zeigeAuf, klick } = werkzeug;
      const gruppen = frame.locator("button.functional-group");
      await gruppen.first().waitFor();
      await halten(TAKT.start);
      const n = Math.min(await gruppen.count(), 5);
      for (let i = 0; i < n; i++) {
        await zeigeAuf(gruppen.nth(i), (await gruppen.nth(i).innerText()).trim().split("\n")[0]);
        await halten(TAKT.hover);
      }
      await klick(frame.getByRole("tab", { name: "Data", exact: true }), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }), "Data");
      await datenblattMitCas(werkzeug, TAKT.schlussDaten);
    },
  },
  // Hero A: Capsaicin — fertige Struktur, Maus über Ether und Amid (Atome leuchten), dann Export-Knopf.
  // Die beiden Chips liegen nebeneinander: der Weg kreuzt keinen dritten Chip, der sonst kurz aufleuchtet.
  "hero-capsaicin": {
    ...README_010, datei: "hero-capsaicin", breite: 800, hoehe: 730, // 730 seit dem Umbau 17.11. (Export-Knopf endet bei ~717 px; vorher 692)
    tool: "generate_molecule", args: { name_or_smiles: "capsaicin" },
    async ablauf({ frame, page, halten, zeigeAuf, zeiger, mitte, imBild }) {
      // Chip-Text samt Zähler („Amide1“): Klasse + Teiltext, Eindeutigkeit wird unten geprüft
      const gruppe = (name) => frame.locator("button.functional-group").filter({ hasText: name });
      await gruppe("Amide").waitFor();
      const exportKnopf = frame.locator("button", { hasText: "Export PNG" });
      await imBild(exportKnopf, "Export-Knopf");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await halten(1400);
      for (const name of ["Ether", "Amide"]) {
        await zeigeAuf(gruppe(name), name);
        if (await gruppe(name).count() !== 1) throw new Error(`hero-capsaicin: kein eindeutiger Chip ${name}`);
        await halten(1700);
      }
      // erst senkrecht unter die Chip-Reihe, dann zum Export-Knopf: kein Chip auf dem Weg
      const [ax, ay] = await mitte(gruppe("Amide"));
      const hy = ay + 55; // Mitte des Hinweiskastens unter der Chip-Reihe
      await zeiger(ax, hy); await page.mouse.move(ax, hy, { steps: 4 }); await halten(240);
      await zeigeAuf(exportKnopf, "Export PNG");
      await halten(1600);
    },
  },
  // Hero B (Kandidat): Koffein — 2D, Klick auf 3D, ein Drehzug. 3D ist ein Quadrat über die volle
  // Panelbreite (styles.css), flacher als hoch geht deshalb nur mit Abschneiden — also 600 breit.
  "hero-caffeine-3d": {
    ...README_010, datei: "hero-caffeine-3d", breite: 600, hoehe: HERO.hoehe, fps: 12, // 3D-Panel seit dem Umbau 17.11. wie die Hero-Szenen (vorher 860)
    tool: "generate_molecule", args: { name_or_smiles: "caffeine" },
    async ablauf(werkzeug) {
      const { frame, halten, klick, mitte, imBild } = werkzeug;
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(1300);
      await klick(frame.getByRole("button", { name: "3D", exact: true }), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }), "3D");
      await imBild(frame.locator("[data-view-3d]"), "3D-Kuhle");
      await imBild(frame.locator(".molecule-panel"), "Panel samt Fußzeile");
      await halten(1300); // Einblend-Drehung (1200 ms) läuft zu Ende
      const [cx, cy] = await mitte(frame.locator("[data-view-3d]"));
      await ziehen(werkzeug, [cx - 140, cy], [cx + 140, cy + 25], 2000, "drag");
      await halten(1300);
    },
  },
  // Lysozym als Cartoon (Mol*, WebGL): 2 s stehen, ein langsamer Drehzug, Endzustand.
  // Kein Bild der SVG-Rückfallspur: die Aufnahme beginnt erst, wenn die Engine steht
  // und ihre Einblend-Drehung ausgelaufen ist; steht am Ende nicht „ready“, ist die Szene rot.
  "lysozyme-cartoon": {
    ...README_010, themes: ["light", "dark"], datei: "lysozyme-cartoon", breite: 600, hoehe: 812, fps: 12, farben: 96, eigenerBrowser: true,
    tool: "generate_protein_or_antibody", args: { name: "lysozyme" }, panel: "[data-protein-viewer]",
    async vorlauf({ frame, page }) {
      await frame.locator('[data-protein-viewer="ready"]').waitFor({ timeout: 60000 });
      await page.waitForTimeout(1800); // Einblend-Drehung 1200 ms + Puffer
    },
    async ablauf(werkzeug) {
      const { frame, halten, mitte, imBild } = werkzeug;
      const bühne = frame.locator('[data-protein-viewer="ready"]');
      await imBild(bühne, "Cartoon-Fläche");
      await imBild(frame.locator("button", { hasText: "Export PNG" }), "Export-Knopf");
      await halten(2000);
      const [cx, cy] = await mitte(bühne);
      await ziehen(werkzeug, [cx - 120, cy + 10], [cx + 120, cy - 10], 2600, "drag");
      await halten(1500);
      if (await frame.locator('[data-protein-viewer="ready"] [data-cartoon-host] canvas').count() !== 1)
        throw new Error("ROT lysozyme-cartoon: am Ende kein Cartoon-Canvas (Rückfallspur?)");
    },
  },
  // β-D-Glucose: Ansicht-Achse einmal durch — 2D → Fischer → Haworth → Chair (ohne 3D: dessen Bühne ist
  // doppelt so hoch, das GIF stünde sonst die meiste Zeit halb leer; 3D zeigt das Hero-GIF)
  "sugar-views": {
    ...GALERIE, datei: "sugar-views", hoehe: 680,
    tool: "generate_molecule", args: { name_or_smiles: "beta-D-glucose" },
    async ablauf({ frame, halten, klick, imBild }) {
      const achse = frame.locator("[data-view-axis]");
      const knopf = (text) => achse.getByRole("button", { name: text, exact: true });
      const gedrückt = (text) => achse.locator('button[aria-pressed="true"][aria-busy="false"]', { hasText: text });
      await frame.locator(".structure-canvas svg").first().waitFor();
      for (const v of ["Fischer", "Haworth", "Chair"])
        if (!(await knopf(v).count())) throw new Error(`sugar-views: kein Knopf ${v}`);
      await imBild(achse, "Ansicht-Achse");
      await halten(1300);
      for (const v of ["Fischer", "Haworth", "Chair"]) {
        await klick(knopf(v), () => gedrückt(v).waitFor({ timeout: 30000 }), v);
        await imBild(frame.locator(".panel-footer"), `Fußzeile (${v})`);
        await halten(v === "Chair" ? 2200 : 1500);
      }
    },
  },
  // SN2 mit (R)-2-Brombutan + Cyanid: Overview → Views → mit Next durch alle drei Ansichten
  "mechanism-steps": {
    ...GALERIE, datei: "mechanism-steps", hoehe: 610, panel: ".mechanism-panel",
    tool: "generate_mechanism", args: { reaction_type: "sn2", substrates: ["(R)-2-bromobutane", "cyanide"] },
    async ablauf({ frame, halten, klick, imBild }) {
      await halten(1500);
      await klick(frame.getByRole("tab", { name: "Views", exact: true }), () => frame.getByText(/^View 1 \/ \d+$/).waitFor({ timeout: 5000 }), "Views");
      const gesamt = Number((await frame.getByText(/^View 1 \/ \d+$/).innerText()).split("/")[1]);
      await halten(1600);
      for (let i = 2; i <= gesamt; i++) {
        await klick(frame.getByRole("button", { name: "Next", exact: true }), () => frame.getByText(`View ${i} / ${gesamt}`, { exact: true }).waitFor({ timeout: 5000 }), "Next");
        await imBild(frame.locator(".panel-footer"), `Fußzeile (Schritt ${i})`);
        await halten(i === gesamt ? 2200 : 1600);
      }
    },
  },
  // H₂ + O₂ → H₂O, so gezeichnet nicht ausgeglichen: Badge zeigen, dann „Apply coefficients“
  "reaction-balance": {
    ...GALERIE, datei: "reaction-balance", hoehe: 236, panel: ".reaction-panel",
    tool: "generate_reaction", args: { reactants: ["hydrogen", "oxygen"], products: ["water"] },
    async ablauf({ frame, page, halten, zeiger, klick }) {
      // Zeiger knapp unter die Badges: mittig darauf verdeckte er genau den Text, um den es geht
      const darunter = async (locator) => {
        const b = await locator.boundingBox();
        const x = b.x + b.width / 2, y = b.y + b.height + 12;
        await zeiger(x, y); await page.mouse.move(x, y, { steps: 6 }); await halten(220);
      };
      const badge = frame.locator('[data-testid="balance-badge"]');
      await badge.waitFor();
      if (await badge.getAttribute("data-state") !== "unbalanced") throw new Error("reaction-balance: Badge nicht „not balanced“");
      await halten(1300);
      await darunter(badge);
      await halten(1500);
      await darunter(frame.locator('[data-testid="balance-suggestion"]'));
      await halten(1300);
      await klick(frame.getByRole("button", { name: "Apply coefficients" }),
        () => frame.locator('[data-testid="balance-badge"][data-state="balanced"]').waitFor({ timeout: 30000 }), "Apply coefficients");
      await halten(2500);
    },
  },
  // Trastuzumab: Structure drehen, hinein- und herauszoomen, dann Scheme und zurück
  "antibody-scheme": {
    ...GALERIE, datei: "antibody-scheme", hoehe: 912, farben: 96, eigenerBrowser: true,
    tool: "generate_protein_or_antibody", args: { name: "trastuzumab" }, panel: "[data-protein-viewer]",
    vorlauf: proteinBereit,
    async ablauf(werkzeug) {
      const { frame, halten, klick, mitte, imBild } = werkzeug;
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      const bühne = frame.locator("[data-protein-viewer]");
      if (await reiter("Structure").getAttribute("aria-selected") !== "true") {
        await halten(1200);
        await klick(reiter("Structure"), () => frame.locator('[role="tab"][aria-selected="true"]', { hasText: "Structure" }).waitFor(), "Structure");
      }
      await imBild(bühne, "Cartoon-Fläche");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      await halten(800);
      const [cx, cy] = await mitte(bühne);
      await ziehen(werkzeug, [cx - 110, cy + 10], [cx + 110, cy - 10], 1500, "drag");
      await zoomen(werkzeug, [cx, cy], -1, 5, "zoom in");
      await halten(500);
      await zoomen(werkzeug, [cx, cy], 1, 7, "zoom out");
      await halten(300);
      await klick(reiter("Scheme"), () => frame.locator("svg[data-igg-scheme]").waitFor({ timeout: 5000 }), "Scheme");
      await imBild(frame.locator(".panel-footer"), "Fußzeile (Schema)");
      await halten(1800);
      await klick(reiter("Structure"), () => frame.locator('[role="tab"][aria-selected="true"]', { hasText: "Structure" }).waitFor(), "Structure");
      await halten(800);
    },
  },
  // Lysozym: drehen, zoomen, Färbung Secondary → Rainbow N→C, Darstellung Cartoon → Trace → Cartoon
  "lysozyme-zoom": {
    ...BLUESKY, datei: "lysozyme-zoom", hoehe: 840, farben: 96, eigenerBrowser: true,
    tool: "generate_protein_or_antibody", args: { name: "lysozyme" }, panel: "[data-protein-viewer]",
    vorlauf: proteinBereit,
    async ablauf(werkzeug) {
      const { frame, halten, klick, mitte, imBild } = werkzeug;
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      const gewählt = (text) => () => frame.locator('[role="tab"][aria-selected="true"]', { hasText: text }).first().waitFor();
      const bühne = frame.locator('[data-protein-viewer="ready"]');
      await imBild(bühne, "Cartoon-Fläche");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      await halten(700);
      const [cx, cy] = await mitte(bühne);
      await ziehen(werkzeug, [cx - 110, cy + 10], [cx + 110, cy - 10], 1300, "drag");
      await zoomen(werkzeug, [cx, cy], -1, 5, "zoom in");
      await halten(500);
      await zoomen(werkzeug, [cx, cy], 1, 7, "zoom out");
      await halten(300);
      await klick(reiter("Rainbow N→C"), gewählt("Rainbow"), "Rainbow");
      await halten(800);
      await klick(reiter("Trace"), gewählt("Trace"), "Trace");
      await halten(900);
      await klick(reiter("Cartoon"), gewählt("Cartoon"), "Cartoon");
      await halten(1000);
    },
  },
  // ── Kerntool-Schleifen (20.11.2026, Auftrag der Vermarktung): je Werkzeug ein Feed-Clip, 8–10 s, Bild 0 =
  // Ruhelage, das letzte Bild führt ohne Sprung auf Bild 0 zurück (Naht wird gemessen, `nahtlos`). Feste
  // Argumente und fester Clipname; nur mit --feed. Rechtecke je Clip: panel, buehne, reiter, legende (+ Extras).
  // generate_molecule, Atorvastatin: zwei Gruppen-Chips (Atome leuchten), Data und zurück auf Structure
  "kern-molecule": {
    ...KERN, clip: "atorvastatin-molecule", feedHoehe: 770,
    tool: "generate_molecule", args: { name_or_smiles: "atorvastatin", label: "Atorvastatin", annotate_stereo: true },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-molecule");
      const { frame, halten, zeigeAuf, klick, imBild, rechteck } = werkzeug;
      const gruppen = frame.locator("button.functional-group");
      await gruppen.first().waitFor();
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".group-section"), "Gruppen");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      await rechteck("panel", frame.locator(".molecule-panel"));
      await rechteck("buehne", frame.locator(".structure-canvas"));
      await rechteck("reiter", frame.locator(".panel-head [role=tablist]"));
      await rechteck("legende", frame.locator(".group-section"));
      await halten(700);
      // Erst über die Kennwerte, dann senkrecht auf den ersten Chip: der direkte Weg von rechts streift fremde Chips
      const [gx, gy] = await werkzeug.mitte(gruppen.nth(0));
      await werkzeug.fahreZu(gx + 20, gy - 70);
      for (const i of [0, 1]) {
        await zeigeAuf(gruppen.nth(i), (await gruppen.nth(i).innerText()).trim().split("\n")[0]);
        await halten(1150);
      }
      await klick(reiter("Data"), () => frame.getByText("IUPAC name", { exact: true }).first().waitFor({ timeout: 30000 }), "Data");
      await rechteck("datenblatt", frame.locator('[data-view="data"]'));
      await halten(1700);
      await klick(reiter("Structure"), () => frame.locator('[data-view="structure"] .structure-canvas svg').first().waitFor({ timeout: 10000 }), "Structure");
      await halten(350);
      await raus(werkzeug);
    },
  },
  // generate_3d, (−)-Menthol: volle Drehung um die Hochachse ab Bild 0 (ein Drehzug über 2π/0,01 px, ohne
  // sichtbaren Zeiger — wie die Proteinserie), dann mit Zeiger in einem Kreiszug kippen und zurück. Einen
  // Stilwechsel hat das Panel nicht (nur „Reset view“; der spränge 40° zurück und gleitet dann — keine Schleife).
  "kern-3d": {
    ...KERN, clip: "menthol-3d", feedHoehe: 840, panel: ".m3d-panel",
    tool: "generate_3d", args: { name_or_smiles: "C[C@@H]1CC[C@H]([C@@H](C1)O)C(C)C", label: "(−)-Menthol (1R,2S,5R)" },
    argsDunkel: { name_or_smiles: "CC(C)[C@@H]1CC[C@@H](C)C[C@H]1O", label: "(−)-Menthol" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-3d");
      const { frame, page, halten, mitte, imBild, rechteck, marke, drehen, fahreZu, zeiger, bild } = werkzeug;
      const modell = frame.locator(".m3d-stage svg").first();
      await modell.waitFor();
      // Einblend-Drehung (1,2 s, rAF) läuft auf der gesteuerten Uhr: vorspulen, bis das Modell steht
      const lage = () => modell.evaluate((el) => el.innerHTML.length + ":" + el.querySelector("circle:last-of-type, line")?.outerHTML + el.innerHTML.slice(-400));
      for (let i = 0, vorher = null; ; i++) {
        await page.clock.runFor(100);
        const jetzt = await lage();
        if (i >= 14 && jetzt === vorher) break;
        if (i > 80) throw new Error("ROT kern-3d: Einblend-Drehung endet nicht");
        vorher = jetzt;
      }
      await imBild(frame.locator(".panel-title"), "Titel");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      await rechteck("panel", frame.locator(".m3d-panel"));
      await rechteck("buehne", modell);
      await rechteck("reiter", frame.locator(".stage-bar"));
      await rechteck("legende", frame.locator(".key-facts"));
      const ruhe = await modell.evaluate((el) => el.innerHTML);
      const [cx, cy] = await mitte(modell);
      // 2π bei 0,01 rad je Pixel = 628,32 px. Start links in der Fläche; die Maus bleibt per Pointer-Capture gefangen.
      const WEG = (2 * Math.PI) / 0.01, x0 = cx - 250, DREH_MS = 4000;
      await page.mouse.move(x0, cy);
      await page.mouse.down();
      marke("drehung", "360°");
      await drehen(DREH_MS, (anteil) => page.mouse.move(x0 + WEG * anteil, cy));
      await page.mouse.move(x0 + WEG, cy);
      await page.mouse.up();
      await page.mouse.move(werkzeug.zeigerStart[0], werkzeug.zeigerStart[1]);
      // Kippen: ein geschlossener Kreis in einem Zug, gleichmäßig schnell (kein Umkehrpunkt, an dem das Bild steht);
      // am Ende dx = dy = 0 → exakt die Lage davor
      const start = [cx + 60, cy - 70], RADIUS = 60, KIPP_MS = 2300;
      await halten(200);
      await fahreZu(...start);
      await halten(250);
      marke("klick", "drag tilt");
      await page.mouse.down();
      await drehen(KIPP_MS, async (anteil) => {
        const a = (anteil * 60 * KIPP_MS / 1000 + 1) / (60 * KIPP_MS / 1000); // letztes Bild steht wieder am Startpunkt
        const x = start[0] + RADIUS * Math.sin(2 * Math.PI * a), y = start[1] + RADIUS * (1 - Math.cos(2 * Math.PI * a));
        await page.mouse.move(x, y);
        await zeiger(x, y);
      });
      await page.mouse.move(...start);
      await page.mouse.up();
      await halten(250);
      await raus(werkzeug);
      await bild();
      // 2π-Lage = Ruhelage? Koordinaten auf 0,1 px vergleichen (Gleitkomma nach einer vollen Drehung)
      const runden = (h) => h.replace(/-?\d+\.\d+/g, (z) => Number(z).toFixed(1));
      if (runden(await modell.evaluate((el) => el.innerHTML)) !== runden(ruhe)) throw new Error("ROT kern-3d: Endlage ≠ Ruhelage (Drehung nicht genau 360°)");
    },
  },
  // compare_molecules, Morphin gegen Codein: das Panel ist ein stehendes Bild (kein Bedienelement an der Figur).
  // Der Zeiger zeigt erst auf das phenolische OH von Morphin, dann auf die markierte Methylgruppe von Codein.
  "kern-compare": {
    ...KERN, clip: "morphine-codeine-compare", feedHoehe: 750, inhalt: 460, panel: ".plot-panel",
    tool: "compare_molecules", args: { structures: ["morphine", "codeine"], labels: ["Morphine", "Codeine (3-O-methylmorphine)"], title: "Morphine vs. codeine: one methyl group" },
    argsDunkel: { structures: ["morphine", "codeine"], labels: ["Morphine", "Codeine"], title: "Morphine vs. Codeine" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-compare");
      const { frame, page, halten, fahreZu, imBild, rechteck, marke } = werkzeug;
      const figur = frame.locator(".plot-svg svg").first();
      await figur.waitFor();
      await imBild(frame.locator(".plot-panel"), "Panel");
      // Markierung (Codein, O–CH3) und das O, das in Morphin an derselben Stelle ein H trägt: in der Figur
      // das rote Atomlabel der linken Hälfte, das am weitesten rechts liegt (phenolisches OH)
      const orte = await figur.evaluate((svg) => {
        const kasten = (el) => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; };
        const huelle = (els) => { const k = els.map(kasten); const x = Math.min(...k.map((b) => b.x)), y = Math.min(...k.map((b) => b.y));
          return { x, y, width: Math.max(...k.map((b) => b.x + b.width)) - x, height: Math.max(...k.map((b) => b.y + b.height)) - y }; };
        const rot = (el) => /#ff7f7f/i.test(el.getAttribute("style") || "") || /#ff7f7f/i.test(el.getAttribute("fill") || "") || /#ff7f7f/i.test(el.getAttribute("stroke") || "");
        const marken = [...svg.querySelectorAll("path, ellipse, circle, rect")].filter(rot);
        const mitteX = kasten(svg).x + kasten(svg).width / 2;
        const labels = {};
        for (const p of svg.querySelectorAll('path[class^="atom-"]')) {
          if (!/#ff0000/i.test(p.getAttribute("fill") || "")) continue;
          const b = kasten(p);
          if (b.x + b.width / 2 < mitteX) (labels[p.getAttribute("class")] ||= []).push(p);
        }
        const o = Object.values(labels).map(huelle).sort((a, b) => b.x - a.x)[0];
        return { marke: marken.length ? huelle(marken) : null, markenZahl: marken.length, morphinOH: o ?? null, figur: kasten(svg) };
      });
      if (!orte.marke || !orte.morphinOH) throw new Error(`ROT kern-compare: Markierung/OH nicht gefunden ${JSON.stringify(orte)}`);
      const versatz = await frame.frameElement().then((el) => el.boundingBox()); // Figur-Koordinaten sind iframe-Koordinaten
      const aufSeite = (b) => ({ x: b.x + versatz.x, y: b.y + versatz.y, width: b.width, height: b.height });
      const m = aufSeite(orte.morphinOH), c = aufSeite(orte.marke), f = aufSeite(orte.figur);
      await rechteck("panel", frame.locator(".plot-panel"));
      await rechteck("buehne", figur);
      await rechteck("reiter", frame.locator(".panel-head"));
      await rechteck("legende", frame.locator(".panel-subtitle"));
      await rechteck("unterschied", c);
      await rechteck("morphin_oh", m);
      await rechteck("links", { x: f.x, y: f.y, width: f.width / 2, height: f.height });
      await rechteck("rechts", { x: f.x + f.width / 2, y: f.y, width: f.width / 2, height: f.height });
      await halten(900);
      // Zeiger knapp unter das Ziel, damit er es nicht verdeckt
      await fahreZu(m.x + m.width / 2 + 4, m.y + m.height + 14);
      marke("hover", "morphine: phenol OH");
      await halten(2400);
      await fahreZu(c.x + c.width / 2, c.y + c.height + 14);
      marke("hover", "codeine: O–CH3 (highlighted)");
      await halten(2900);
      await raus(werkzeug);
      await halten(350);
    },
  },
  // generate_reaction, Fischer-Veresterung Benzoesäure + Methanol: als Gleichgewicht gezeichnet und schon
  // ausgeglichen (kein „Apply coefficients“). Zeiger auf „balanced“, dann Export PNG → Rückmeldung in der
  // Fußzeile, die nach 4 s von selbst wieder verschwindet — Ende = Anfang.
  "kern-reaction": {
    ...KERN, clip: "esterification-reaction", feedHoehe: 750, inhalt: 330, panel: ".reaction-panel",
    tool: "generate_reaction", args: { reactants: ["benzoic acid", "methanol"], products: ["methyl benzoate", "water"],
      arrow: "equilibrium", conditions: "H2SO4 (cat.)", conditions_below: "reflux", name: "Fischer esterification of benzoic acid" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-reaction");
      const { frame, halten, fahreZu, klick, imBild, rechteck, marke } = werkzeug;
      const badge = frame.locator('[data-testid="balance-badge"]');
      await badge.waitFor();
      if (await badge.getAttribute("data-state") !== "balanced") throw new Error("ROT kern-reaction: Gleichung nicht ausgeglichen");
      const fuss = frame.locator(".panel-footer"), exportKnopf = frame.locator("button.export-png");
      await imBild(frame.locator(".reaction-panel"), "Panel");
      await rechteck("panel", frame.locator(".reaction-panel"));
      await rechteck("buehne", frame.locator(".reaction-panel .stage"));
      await rechteck("reiter", fuss);
      await rechteck("legende", frame.locator(".balance-row"));
      const ruhe = (await fuss.innerText()).trim();
      await halten(900);
      const b = await badge.boundingBox();
      await fahreZu(b.x + b.width / 2, b.y + b.height + 12);
      marke("hover", "balanced");
      await halten(1300);
      const rückmeldung = frame.locator(".export-feedback");
      await klick(exportKnopf, () => rückmeldung.waitFor({ timeout: 30000 }), "Export PNG");
      const text = (await rückmeldung.innerText()).trim();
      if (/failed/i.test(text)) throw new Error(`ROT kern-reaction: ${text}`);
      marke("schluss", text);
      // Die Rückmeldung steht 4 s (Timer auf der gesteuerten Uhr); Zeiger vom Knopf weg, dann hinaus
      const k = await exportKnopf.boundingBox();
      await fahreZu(k.x - 60, k.y - 40);
      await halten(1500);
      await raus(werkzeug);
      for (let i = 0; (await rückmeldung.count()) > 0; i++) {
        if (i > 400) throw new Error("ROT kern-reaction: Rückmeldung verschwindet nicht");
        await werkzeug.bild();
      }
      await halten(400);
      if ((await fuss.innerText()).trim() !== ruhe) throw new Error("ROT kern-reaction: Fußzeile am Ende anders als am Anfang");
    },
  },
  // generate_reaction, Zugabe: Verbrennung von Propan, so gezeichnet nicht ausgeglichen → „Apply coefficients“
  // → „Undo“ (Ende = Anfang). Zeigt, was die Veresterung nicht zeigen kann.
  // NICHT AUSLIEFERN, solange der Panel-Fehler offen ist (20.11.2026, plans/mcp-server.md): nach „Apply“
  // läuft die Gleichung bei 600 px rechts aus der Bühne (H2O abgeschnitten, Pfeil über „oxygen“).
  "kern-reaction-balance": {
    ...KERN, clip: "propane-combustion-reaction", feedHoehe: 750, inhalt: 330, panel: ".reaction-panel",
    tool: "generate_reaction", args: { reactants: ["propane", "oxygen"], products: ["carbon dioxide", "water"], name: "Combustion of propane" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-reaction-balance");
      const { frame, halten, fahreZu, klick, imBild, rechteck, marke } = werkzeug;
      const badge = frame.locator('[data-testid="balance-badge"]');
      await badge.waitFor();
      if (await badge.getAttribute("data-state") !== "unbalanced") throw new Error("ROT kern-reaction-balance: Badge nicht „not balanced“");
      await imBild(frame.locator(".reaction-panel"), "Panel");
      await rechteck("panel", frame.locator(".reaction-panel"));
      await rechteck("buehne", frame.locator(".reaction-panel .stage"));
      await rechteck("reiter", frame.locator(".panel-footer"));
      await rechteck("legende", frame.locator(".balance-row"));
      await halten(900);
      const b = await frame.locator('[data-testid="balance-suggestion"]').boundingBox();
      await fahreZu(b.x + b.width / 2, b.y + b.height + 12);
      marke("hover", "suggested coefficients");
      await halten(1300);
      await klick(frame.getByRole("button", { name: "Apply coefficients" }),
        () => frame.locator('[data-testid="balance-badge"][data-state="balanced"]').waitFor({ timeout: 30000 }), "Apply coefficients");
      await imBild(frame.locator(".reaction-panel"), "Panel nach Apply");
      await halten(2300);
      await klick(frame.getByRole("button", { name: "Undo", exact: true }),
        () => frame.locator('[data-testid="balance-badge"][data-state="unbalanced"]').waitFor({ timeout: 10000 }), "Undo");
      await halten(500);
      await raus(werkzeug);
      await halten(300);
    },
  },
  // generate_mechanism, SN2 Brommethan + Hydroxid: Ruhelage = Overview (so öffnet das Panel im Chat bei
  // current_step 0), dann „Views“, mit Next durch alle Ansichten, über den Reiter zurück zur Overview.
  // Rechtecke der Schrittansicht unter eigenen Schlüsseln (panel_schritte, buehne_schritte, navigation, schrittanzeige).
  "kern-mechanism": {
    ...KERN, clip: "sn2-mechanism", feedHoehe: 750, inhalt: 610, panel: ".mechanism-panel",
    tool: "generate_mechanism", args: { reaction_type: "sn2", substrates: ["bromomethane", "hydroxide"], current_step: 0 },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-mechanism");
      const { frame, halten, klick, imBild, rechteck } = werkzeug;
      const feld = frame.locator(".mechanism-panel");
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      if (await feld.getAttribute("data-mode") !== "overview") throw new Error("ROT kern-mechanism: Panel öffnet nicht auf Overview");
      await frame.locator(".mech-overview").waitFor();
      await imBild(feld, "Panel (Overview)");
      await rechteck("panel", feld);
      await rechteck("buehne", frame.locator(".mech-stage"));
      await rechteck("reiter", frame.locator(".panel-head [role=tablist]"));
      await rechteck("legende", frame.locator(".panel-subtitle"));
      await halten(1000);
      await klick(reiter("Views"), () => frame.getByText(/^View 1 \/ \d+$/).waitFor({ timeout: 5000 }), "Views");
      const gesamt = Number((await frame.getByText(/^View 1 \/ \d+$/).innerText()).split("/")[1]);
      if (!(gesamt >= 2)) throw new Error(`ROT kern-mechanism: ${gesamt} Ansichten`);
      const schritt = (i) => () => frame.getByText(`View ${i} / ${gesamt}`, { exact: true }).waitFor({ timeout: 5000 });
      await imBild(feld, "Panel (Schritt 1)");
      await rechteck("panel_schritte", feld);
      await rechteck("buehne_schritte", frame.locator(".mech-stage"));
      await rechteck("navigation", frame.locator(".mech-nav"));
      await rechteck("schrittanzeige", frame.locator(".mech-nav-center"));
      await halten(1300);
      for (let i = 2; i <= gesamt; i++) {
        await klick(frame.locator("button.mech-next"), schritt(i), `Next → view ${i}`);
        await imBild(feld, `Panel (Schritt ${i})`);
        await halten(i === gesamt ? 1700 : 1400);
      }
      await klick(reiter("Overview"), () => frame.locator('.mechanism-panel[data-mode="overview"] .mech-overview').waitFor({ timeout: 5000 }), "Overview");
      await halten(600);
      await raus(werkzeug);
      await frame.evaluate(() => document.activeElement?.blur()); // Fokusrahmen des Reiters gehört nicht zur Ruhelage
      await halten(300);
    },
  },
  // Feed-Protein (18.11.2026, für Autoplay in Schleife): eine volle Drehung um die Hochachse ab dem
  // ersten Bild, dann Färbung wechseln (mehrere Ketten: Chain, sonst Rainbow N→C) und zurück, Zeiger
  // zurück an den Startpunkt — letztes Bild ≈ erstes. Name per `protein@<name>`.
  protein: {
    ...BLUESKY, datei: "protein", hoehe: 840, feedHoehe: 840, eigenerBrowser: true, nahtlos: true,
    tool: "generate_protein_or_antibody", args: { name: "lysozyme" }, panel: "[data-protein-viewer]",
    async vorlauf({ frame, page }) {
      // Antikörper starten teils im Schema: unaufgenommen auf Structure, dann wie immer auf die Engine warten
      const struktur = frame.getByRole("tab", { name: "Structure", exact: true });
      if (await struktur.count() && await struktur.getAttribute("aria-selected") !== "true") await struktur.click();
      await proteinBereit({ frame, page });
    },
    async ablauf(werkzeug) {
      if (!werkzeug.feed) throw new Error("Szene protein gibt es nur mit --feed");
      const { frame, page, halten, klick, imBild, fahreZu, marke } = werkzeug;
      await cartoonSteht(werkzeug, "protein");
      const leinwand = frame.locator('[data-protein-viewer="ready"] [data-cartoon-host] canvas');
      if (await leinwand.count() !== 1) throw new Error("ROT protein: kein Cartoon-Canvas (Rückfallspur?)");
      await imBild(frame.locator(".panel-title"), "Titel");
      await imBild(frame.locator(".panel-subtitle"), "Unterzeile");
      await imBild(frame.locator(".protein-legend"), "Legende");
      await imBild(leinwand, "Cartoon-Fläche");
      // Eine volle Drehung um die Hochachse: Kamera je Bild um 360°·i/n um die y-Achse durch das Ziel gedreht
      // (exakter Winkel je Bild; Mols* eigener Spin kam im ersten Versuch auf ~270°, gemessen bei noch laufender Einblendung).
      const DREH_MS = 3600;
      const griffe = await frame.evaluate(() => (window.__cartoonGriffe || []).length);
      if (griffe !== 1) throw new Error(`ROT protein: ${griffe} Engine-Griffe statt 1`);
      await frame.evaluate(() => { window.__ruhe = window.__cartoonGriffe[0].canvas3d.camera.getSnapshot(); });
      marke("drehung", "360°");
      // Bild 0 = Ruhelage, gleicher Winkelschritt je Bild; das letzte Drehbild steht einen Schritt vor 360°,
      // danach Ruhelage = Bild 0 — in Schleife läuft die Drehung ohne Naht weiter.
      // Nebenbei die Hülle des Proteins auf der Fläche über die ganze Drehung (Nicht-Hintergrund-Pixel)
      const hülle = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
      let schrittNr = 0;
      await werkzeug.drehen(DREH_MS, async (anteil) => {
        await frame.evaluate((w) => {
          const r = window.__ruhe, c = window.__cartoonGriffe[0].canvas3d;
          const ex = r.position[0] - r.target[0], ez = r.position[2] - r.target[2], cos = Math.cos(w), sin = Math.sin(w);
          const position = [r.target[0] + ex * cos + ez * sin, r.position[1], r.target[2] - ex * sin + ez * cos];
          c.camera.setState({ ...r, position }, 0);
          c.requestDraw();
        }, 2 * Math.PI * anteil);
      }, async () => {
        if (schrittNr++ % 4) return;
        const h = await cartoonHülleJetzt(frame);
        if (h) { hülle.x0 = Math.min(hülle.x0, h.x0); hülle.y0 = Math.min(hülle.y0, h.y0); hülle.x1 = Math.max(hülle.x1, h.x1); hülle.y1 = Math.max(hülle.y1, h.y1); }
      });
      await frame.evaluate(() => { const c = window.__cartoonGriffe[0].canvas3d; c.camera.setState(window.__ruhe, 0); c.requestDraw(); });
      const fläche = await leinwand.boundingBox();
      if (!Number.isFinite(hülle.x0)) throw new Error("ROT protein: kein Protein auf der Fläche gefunden");
      await werkzeug.rechteck("buehne", { x: fläche.x + hülle.x0, y: fläche.y + hülle.y0, width: hülle.x1 - hülle.x0 + 1, height: hülle.y1 - hülle.y0 + 1 });
      await werkzeug.rechteck("panel", await frame.locator(".protein-panel").boundingBox());
      await werkzeug.rechteck("reiter", await frame.locator(".protein-bar").boundingBox());
      await werkzeug.rechteck("legende", await frame.locator(".protein-legend").boundingBox());
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      const gewählt = (text) => () => frame.locator('[role="tab"][aria-selected="true"]', { hasText: text }).first().waitFor();
      const start = (await frame.locator('[role="tablist"][aria-label="Colour by"] [role="tab"][aria-selected="true"]').innerText()).trim();
      const mehrereKetten = (await reiter("Chain").count()) > 0;
      const ziel = mehrereKetten && start !== "Chain" ? "Chain" : "Rainbow N→C";
      await halten(150);
      await klick(reiter(ziel), gewählt(ziel), ziel);
      await halten(1700);
      await klick(reiter(start), gewählt(start), start);
      await halten(500);
      await fahreZu(...werkzeug.zeigerStart); // Zeiger rechts aus dem Bild: letztes Bild ≈ erstes
      await halten(150);
    },
  },
  // ── Folgeauftrag der Vermarktung (Tisch-Faden 20261120-080521, 20.11.2026): Ziehen sichtbar machen.
  // Protein mit Zeiger-Zug, hell wie `protein` (gleiche Argumente, Startlage und Rechtecke): ein echter
  // waagerechter Zug über die Mol*-Fläche (Trackball, kein selbst gesetzter Winkel) dreht das Modell genau
  // 360° — die Pixel je Umdrehung werden vor der Aufnahme gemessen. Danach Rainbow N→C und zurück auf die
  // Startfärbung, Zeiger hinaus; letztes Bild → Bild 0 ohne Sprung. Name per `protein-ziehen@<name>`.
  "protein-ziehen": {
    ...BLUESKY, datei: "protein-ziehen", hoehe: 840, feedHoehe: 840, eigenerBrowser: true, nahtlos: true,
    tool: "generate_protein_or_antibody", args: { name: "lysozyme" }, panel: "[data-protein-viewer]",
    async vorlauf({ frame, page }) {
      const struktur = frame.getByRole("tab", { name: "Structure", exact: true });
      if (await struktur.count() && await struktur.getAttribute("aria-selected") !== "true") await struktur.click();
      await proteinBereit({ frame, page });
    },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "protein-ziehen");
      const { frame, page, halten, klick, imBild, fahreZu, rechteck } = werkzeug;
      await cartoonSteht(werkzeug, "protein-ziehen");
      const leinwand = frame.locator('[data-protein-viewer="ready"] [data-cartoon-host] canvas');
      if (await leinwand.count() !== 1) throw new Error("ROT protein-ziehen: kein Cartoon-Canvas (Rückfallspur?)");
      await imBild(frame.locator(".panel-title"), "Titel");
      await imBild(frame.locator(".panel-subtitle"), "Unterzeile");
      await imBild(frame.locator(".protein-legend"), "Legende");
      await imBild(leinwand, "Cartoon-Fläche");
      const griffe = await frame.evaluate(() => (window.__cartoonGriffe || []).length);
      if (griffe !== 1) throw new Error(`ROT protein-ziehen: ${griffe} Engine-Griffe statt 1`);
      await frame.evaluate(() => { window.__ruhe = window.__cartoonGriffe[0].canvas3d.camera.getSnapshot(); });
      const kamera = () => frame.evaluate(() => { const s = window.__cartoonGriffe[0].canvas3d.camera.getSnapshot(); return { p: [...s.position], t: [...s.target], u: [...s.up] }; });
      // Winkel zwischen zwei Blickrichtungen und zwischen den Oben-Vektoren (rad)
      const winkel = (a, b) => {
        const w = (x, y) => { const d = x[0] * y[0] + x[1] * y[1] + x[2] * y[2], n = Math.hypot(...x) * Math.hypot(...y); return Math.acos(Math.max(-1, Math.min(1, d / n))); };
        const e = (k) => k.p.map((v, i) => v - k.t[i]);
        return { blick: w(e(a), e(b)), oben: w(a.u, b.u) };
      };
      const zurRuhe = async () => {
        await frame.evaluate(() => { const c = window.__cartoonGriffe[0].canvas3d; c.camera.setState(window.__ruhe, 0); c.requestDraw(); });
        await page.clock.runFor(50);
      };
      // Messung vor der Aufnahme: 100 px waagerecht ziehen, Drehwinkel ablesen, zurück in die Ruhelage
      const f = await leinwand.boundingBox(), cx = f.x + f.width / 2, cy = f.y + f.height / 2;
      const r0 = await kamera();
      await page.mouse.move(cx - 50, cy);
      await page.mouse.down();
      for (let i = 1; i <= 10; i++) { await page.mouse.move(cx - 50 + 10 * i, cy); await page.clock.runFor(17); }
      await page.mouse.up();
      await page.clock.runFor(50);
      const probe = winkel(r0, await kamera()), radProPx = probe.blick / 100;
      await zurRuhe();
      const zurück = winkel(r0, await kamera());
      if (zurück.blick > 1e-5 || zurück.oben > 1e-5) throw new Error(`ROT protein-ziehen: Ruhelage nach der Messung nicht wiederhergestellt ${JSON.stringify(zurück)}`);
      if (probe.oben > 1e-3) throw new Error(`ROT protein-ziehen: waagerechter Zug kippt die Hochachse (${probe.oben} rad)`);
      const WEG = (2 * Math.PI) / radProPx;
      console.log(`  protein-ziehen: Trackball ${radProPx.toFixed(5)} rad/px → 360° = ${WEG.toFixed(1)} px (Fläche ${f.width.toFixed(0)} px)`);
      if (WEG > f.width - 40) throw new Error(`ROT protein-ziehen: 360° brauchen ${WEG.toFixed(0)} px, die Fläche hat ${f.width.toFixed(0)}`);
      await page.mouse.move(...werkzeug.zeigerStart);
      // Aufnahme: Bild 0 = Ruhelage, Zeiger von rechts, ein Zug über genau 360°, Hülle über den Zug
      await halten(250);
      const hülle = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
      let schrittNr = 0;
      const ZUG_MS = 4000, schrittWinkel = (WEG / Math.round((ZUG_MS * MODUS.fps) / 1000)) * radProPx;
      await zugFeed(werkzeug, [cx - WEG / 2, cy], [cx + WEG / 2, cy], ZUG_MS, "drag 360°", async () => {
        if (schrittNr++ % 4) return;
        const h = await cartoonHülleJetzt(frame);
        if (h) { hülle.x0 = Math.min(hülle.x0, h.x0); hülle.y0 = Math.min(hülle.y0, h.y0); hülle.x1 = Math.max(hülle.x1, h.x1); hülle.y1 = Math.max(hülle.y1, h.y1); }
      });
      // Nach 360° muss die Kamera dort stehen, wo sie anfing (höchstens ein Bildschritt daneben), dann einrasten
      const rest = winkel(r0, await kamera());
      console.log(`  protein-ziehen: Restwinkel nach dem Zug ${rest.blick.toFixed(5)} rad (Bildschritt ${schrittWinkel.toFixed(5)}), Oben ${rest.oben.toFixed(5)}`);
      if (rest.blick > schrittWinkel || rest.oben > schrittWinkel) throw new Error(`ROT protein-ziehen: nach dem Zug ${JSON.stringify(rest)} rad neben der Ruhelage`);
      await frame.evaluate(() => { const c = window.__cartoonGriffe[0].canvas3d; c.camera.setState(window.__ruhe, 0); c.requestDraw(); });
      if (!Number.isFinite(hülle.x0)) throw new Error("ROT protein-ziehen: kein Protein auf der Fläche gefunden");
      await rechteck("buehne", { x: f.x + hülle.x0, y: f.y + hülle.y0, width: hülle.x1 - hülle.x0 + 1, height: hülle.y1 - hülle.y0 + 1 });
      await rechteck("panel", await frame.locator(".protein-panel").boundingBox());
      await rechteck("reiter", await frame.locator(".protein-bar").boundingBox());
      await rechteck("legende", await frame.locator(".protein-legend").boundingBox());
      await rechteck("flaeche", f);
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      const gewählt = (text) => () => frame.locator('[role="tab"][aria-selected="true"]', { hasText: text }).first().waitFor();
      const start = (await frame.locator('[role="tablist"][aria-label="Colour by"] [role="tab"][aria-selected="true"]').innerText()).trim();
      if (start === "Rainbow N→C") throw new Error("ROT protein-ziehen: startet schon in Rainbow N→C");
      await halten(200);
      await klick(reiter("Rainbow N→C"), gewählt("Rainbow"), "Rainbow N→C");
      await halten(1500);
      await klick(reiter(start), gewählt(start), start);
      await halten(400);
      await fahreZu(...werkzeug.zeigerStart);
      await frame.evaluate(() => document.activeElement?.blur());
      await halten(150);
    },
  },
  // generate_molecule dunkel, Naproxen (ein Stereozentrum): 2D → All H → 3D → Zug mit Zeiger (halbe Drehung) → 2D.
  // Der 3D-Zustand verfällt beim Rückweg, Ende = Anfang.
  "kern-darstellungen": {
    ...KERN, clip: "naproxen-views", feedHoehe: 960,
    tool: "generate_molecule", args: { name_or_smiles: "naproxen", label: "Naproxen" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-darstellungen");
      const { frame, halten, klick, imBild, rechteck, mitte } = werkzeug;
      const achse = frame.locator("[data-view-axis]");
      const knopf = (t) => achse.getByRole("button", { name: t, exact: true });
      const gedrückt = (t) => () => achse.locator('button[aria-pressed="true"][aria-busy="false"]', { hasText: t }).waitFor({ timeout: 30000 });
      await frame.locator(".structure-canvas svg").first().waitFor();
      if (await frame.locator('[data-testid="stereo-note"]').count()) throw new Error("ROT kern-darstellungen: Stereo-Hinweis im Panel (Stereozentrum offen?)");
      for (const v of ["2D", "All H", "3D"]) if (!(await knopf(v).count())) throw new Error(`ROT kern-darstellungen: kein Knopf ${v}`);
      await imBild(achse, "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".panel-footer"), "Fußzeile (2D)");
      await rechteck("panel", frame.locator(".molecule-panel"));
      await rechteck("buehne", frame.locator(".structure-canvas"));
      await rechteck("reiter", achse);
      await rechteck("legende", frame.locator(".group-section"));
      await halten(800);
      await klick(knopf("All H"), gedrückt("All H"), "All H");
      await imBild(frame.locator(".panel-footer"), "Fußzeile (All H)");
      await halten(1100);
      await klick(knopf("3D"), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }), "3D");
      const fläche = frame.locator("[data-view-3d]");
      await imBild(fläche, "3D-Fläche");
      await imBild(frame.locator(".panel-footer"), "Fußzeile (3D)");
      await rechteck("buehne_3d", fläche);
      await rechteck("panel_3d", frame.locator(".molecule-panel"));
      await halten(1300); // Einblend-Drehung (1,2 s) läuft sichtbar zu Ende
      const [cx, cy] = await mitte(fläche);
      const HALB = Math.PI / 0.01; // 0,01 rad je Pixel (Ball3DCanvas) → halbe Drehung
      await zugFeed(werkzeug, [cx - HALB / 2, cy + 20], [cx + HALB / 2, cy + 20], 2600, "drag 3D");
      await halten(600);
      await klick(knopf("2D"), gedrückt("2D"), "2D");
      await raus(werkzeug);
      await frame.evaluate(() => document.activeElement?.blur());
      await halten(300);
    },
  },
  // generate_molecule dunkel, Lidocain: „Add to Anki“ → Rückmeldung (Testhost: deliver apkg → „Saved“, Desktop zeigt
  // „Added“) → Study-Reiter, ein Feld aufdecken → zurück auf Structure. Ende = Anfang (Knopf wieder „Add to Anki“).
  "kern-anki": {
    ...KERN, clip: "lidocaine-anki", feedHoehe: 900,
    tool: "generate_molecule", args: { name_or_smiles: "lidocaine", label: "Lidocaine" },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-anki");
      const { frame, halten, klick, imBild, rechteck, mitte, fahreZu, marke } = werkzeug;
      const reiter = (text) => frame.getByRole("tab", { name: text, exact: true });
      const anki = frame.locator("button.add-to-anki");
      await frame.locator(".structure-canvas svg").first().waitFor();
      await imBild(anki, "Anki-Knopf");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      const ruhe = (await anki.innerText()).trim();
      if (ruhe !== "Add to Anki") throw new Error(`ROT kern-anki: Knopf zeigt „${ruhe}“`);
      await rechteck("panel", frame.locator(".molecule-panel"));
      await rechteck("buehne", frame.locator(".structure-canvas"));
      await rechteck("reiter", frame.locator(".panel-head [role=tablist]"));
      await rechteck("legende", frame.locator(".group-section"));
      await rechteck("anki_knopf", anki);
      await halten(900);
      await klick(anki, () => frame.locator("button.add-to-anki", { hasText: /^(Saved|Added)$/ }).waitFor({ timeout: 30000 }), "Add to Anki");
      marke("schluss", (await anki.innerText()).trim());
      const [ax, ay] = await mitte(anki);
      await fahreZu(ax - 40, ay - 46); // Zeiger vom Knopf weg, damit die Rückmeldung lesbar ist
      await halten(1300);
      await klick(reiter("Study"), () => frame.locator('[data-view="study"]').waitFor({ timeout: 10000 }), "Study");
      const ansicht = frame.locator('[data-view="study"]');
      await imBild(frame.locator(".study-actions"), "Reveal all");
      await rechteck("study", ansicht);
      await halten(700);
      const decken = ansicht.locator("button.study-cover"), n = await decken.count();
      if (!n) throw new Error("ROT kern-anki: im Study-Reiter nichts verdeckt");
      await klick(decken.first(), async () => { while ((await decken.count()) >= n) await new Promise((r) => setTimeout(r, 20)); }, "reveal");
      await halten(1300);
      await klick(reiter("Structure"), () => frame.locator('[data-view="structure"] .structure-canvas svg').first().waitFor({ timeout: 10000 }), "Structure");
      for (let i = 0; (await anki.innerText()).trim() !== ruhe; i++) {
        if (i > 400) throw new Error("ROT kern-anki: Knopf kehrt nicht zu „Add to Anki“ zurück");
        await werkzeug.bild();
      }
      await halten(300);
      await raus(werkzeug);
      await frame.evaluate(() => document.activeElement?.blur());
      await halten(300);
    },
  },
  // export_anki_deck dunkel: Deck aus drei Lokalanästhetika (Struktur → Name und Typ). Das Panel ist eine
  // stehende Vorschau ohne Bedienelement an den Karten: der Zeiger fährt die drei Karten ab, dann die APKG-Zeile.
  "kern-anki-deck": {
    ...KERN, clip: "local-anesthetics-anki-deck", feedHoehe: 780, panel: ".anki-panel",
    tool: "export_anki_deck", args: { deck_name: "Local anesthetics", deliver: "apkg", cards: [
      { front: { structure: "lidocaine", text: "Name this local anesthetic" }, back: { text: "Lidocaine<br>amide type" } },
      { front: { structure: "procaine", text: "Name this local anesthetic" }, back: { text: "Procaine<br>ester type" } },
      { front: { structure: "bupivacaine", text: "Name this local anesthetic" }, back: { text: "Bupivacaine<br>amide type" } },
    ] },
    async ablauf(werkzeug) {
      nurFeed(werkzeug, "kern-anki-deck");
      const { frame, halten, imBild, rechteck, fahreZu, marke } = werkzeug;
      const karten = frame.locator("li.anki-card");
      await karten.first().waitFor();
      if (await karten.count() !== 3) throw new Error(`ROT kern-anki-deck: ${await karten.count()} Karten statt 3`);
      const datei = frame.locator(".anki-file");
      await imBild(frame.locator(".anki-panel"), "Panel");
      await rechteck("panel", frame.locator(".anki-panel"));
      await rechteck("buehne", frame.locator(".anki-cards"));
      await rechteck("reiter", frame.locator(".panel-head"));
      await rechteck("legende", datei);
      for (let i = 0; i < 3; i++) await rechteck(`karte${i + 1}`, karten.nth(i));
      await halten(900);
      for (let i = 0; i < 3; i++) {
        const b = await karten.nth(i).locator('[data-side="back"]').boundingBox();
        await fahreZu(b.x + 30, b.y + b.height / 2 + 18); // links auf die Rückseite, Text bleibt lesbar
        marke("hover", `card ${i + 1}`);
        await halten(950);
      }
      const d = await datei.boundingBox();
      await fahreZu(d.x + d.width * 0.45, d.y + d.height + 14);
      marke("hover", "APKG");
      await halten(1200);
      await raus(werkzeug);
      await halten(300);
    },
  },
  // Aspirin: zwei Gruppen-Chips, dann „Add to Anki“ → „Saved“ (Testhost: deliver apkg, kein Anki)
  anki: {
    ...BLUESKY, datei: "anki", hoehe: 900,
    tool: "generate_molecule", args: { name_or_smiles: "aspirin" },
    async ablauf({ frame, halten, zeigeAuf, klick, mitte, imBild, fahreZu }) {
      const gruppen = frame.locator("button.functional-group");
      await gruppen.first().waitFor();
      const anki = frame.locator("button.add-to-anki");
      await imBild(anki, "Anki-Knopf");
      await halten(1200);
      for (let i = 0; i < Math.min(2, await gruppen.count()); i++) {
        await zeigeAuf(gruppen.nth(i), "group");
        await halten(1100);
      }
      await zeigeAuf(anki, "Add to Anki");
      await halten(700);
      await klick(anki, () => frame.locator("button.add-to-anki", { hasText: "Saved" }).waitFor({ timeout: 30000 }), "Add to Anki");
      // Zeiger vom Knopf weg, damit „Saved“ lesbar ist
      const [ax, ay] = await mitte(anki);
      await fahreZu(ax - 40, ay - 46);
      await halten(1600); // „Saved“ steht 2,5 s ab dem Klick (Echtzeit), danach setzt der Knopf zurück
      if (!(await anki.innerText()).includes("Saved")) throw new Error("ROT anki: am Ende kein „Saved“ mehr");
    },
  },
  // Study-Reiter: zwei verdeckte Kennwerte, dann eine Gruppe einzeln aufdecken, zum Schluss „Reveal all“
  study: {
    ...BLUESKY, datei: "study", hoehe: 900,
    tool: "generate_molecule", args: { name_or_smiles: "serotonin" },
    async ablauf({ frame, halten, klick, imBild }) {
      const reiter = frame.getByRole("tab", { name: "Study", exact: true });
      await reiter.waitFor();
      await halten(TAKT.start);
      await klick(reiter, () => frame.locator('[data-view="study"]').waitFor({ timeout: 10000 }), "Study");
      const ansicht = frame.locator('[data-view="study"]');
      await imBild(frame.locator(".study-actions"), "Reveal all");
      await imBild(ansicht.locator('[aria-label="Key facts"]'), "Kennwerte");
      await imBild(ansicht.locator('[aria-label="Functional groups"]'), "Gruppen");
      await halten(900);
      // aufdecken und warten, bis die Zahl der verdeckten Felder sinkt
      const aufdecken = async (verdeckt, ziel) => {
        const n = await verdeckt.count();
        if (!n) throw new Error(`study: nichts verdeckt für ${ziel}`);
        await klick(verdeckt.first(), async () => { while ((await verdeckt.count()) >= n) await new Promise((r) => setTimeout(r, 20)); }, ziel);
        await halten(900);
      };
      const decken = ansicht.locator("button.study-cover");
      await aufdecken(decken, "fact");
      await aufdecken(decken, "fact");
      await aufdecken(ansicht.locator("button.functional-group.is-covered"), "group");
      await klick(frame.getByRole("button", { name: "Reveal all", exact: true }),
        () => frame.locator("button.study-name").waitFor({ state: "detached", timeout: 10000 }), "Reveal all");
      if (await decken.count()) throw new Error("ROT study: nach Reveal all noch verdeckte Felder");
      await halten(2000);
    },
  },
};

if (optionen.theme && !THEMES[optionen.theme]) throw new Error(`--theme light|dark, nicht ${optionen.theme}`);
if (optionen.bild0 && !FEED) throw new Error("--bild0 gibt es nur mit --feed");
if (optionen.chat && !FEED) throw new Error("--chat gibt es nur mit --feed");
// --args DATEI (20.11.2026, Wirkstoff-3D- und Proteinserie): JSON-Objekt { "<clip>": { …toolArguments } } — eine
// Szene läuft einmal je Eintrag, Ausgabe <clip>-<szene ohne kern->, z. B. caffeine-3d, luciferase-protein. So kommen die
// Argumente, die Desktop im Chat übergeben hat, unverändert in den Clip (auch SMILES mit @).
let argsDatei = null;
if (optionen.args) {
  if (!FEED) throw new Error("--args gibt es nur mit --feed");
  argsDatei = JSON.parse(readFileSync(optionen.args, "utf8"));
  if (!argsDatei || typeof argsDatei !== "object" || Array.isArray(argsDatei) || !Object.keys(argsDatei).length) throw new Error("--args: JSON-Objekt { clip: toolArguments } erwartet");
  if (gewählt.length !== 1 || gewählt[0].includes("@") || !SZENEN[gewählt[0]]) throw new Error("--args braucht genau eine Szene ohne @, z. B. kern-3d oder protein");
  for (const [clip, a] of Object.entries(argsDatei)) {
    if (!/^[a-z0-9-]+$/.test(clip)) throw new Error(`--args: Clipname „${clip}“ nur aus a–z, 0–9, -`);
    if (!a || typeof a !== "object" || Array.isArray(a)) throw new Error(`--args: Argumente für ${clip} sind kein Objekt`);
  }
}
const themes = FEED ? [optionen.theme ?? "light"] : optionen.theme ? [optionen.theme] : Object.keys(THEMES);
if (FEED && !gewählt.length) throw new Error("--feed braucht Szenen, z. B. 3d@geosmin");
const szenen = gewählt.length ? gewählt : Object.keys(SZENEN).filter((n) => !SZENEN[n].aufAnsage && !(optionen.video && SZENEN[n].nurGif));
for (const name of szenen) if (!SZENEN[FEED ? name.split("@")[0] : name]) throw new Error(`unbekannte Szene: ${name} (${Object.keys(SZENEN).join(", ")})`);
mkdirSync(MODUS.ausgabe, { recursive: true });
const browser = await chromium.launch();
const ergebnisse = [];
if (FEED) {
  // Feed: je Clip eigener Browser (sauberer Kontext); ein roter Clip wird gemeldet, der Lauf geht weiter
  const rot = [];
  try {
    const läufe = argsDatei
      ? Object.entries(argsDatei).map(([clip, a]) => ({ eintrag: `${szenen[0]}:${clip}`, name: szenen[0], extra: { args: a, argsDunkel: undefined, clip: `${clip}-${szenen[0].replace(/^kern-/, "")}` } }))
      : szenen.map((eintrag) => { const [name, mol] = eintrag.split("@"); return { eintrag, name, mol, extra: {} }; });
    for (const { eintrag, name, mol, extra } of läufe) {
      console.log(`▶ feed ${name} (${extra.clip ?? mol ?? optionen.molecule ?? "Standard"}, ${themes[0]})`);
      // WebGL-Szenen in eigenem Browser: im gemeinsamen lief GFP nach Insulin mit ~7 s je Bild (18.11.)
      const eigener = SZENEN[name].eigenerBrowser ? await chromium.launch() : null;
      try {
        ergebnisse.push(await szene(eigener ?? browser, { name, ...SZENEN[name], ...extra, theme: themes[0], molecule: mol ?? optionen.molecule }));
      } catch (e) {
        console.error(String(e.message ?? e));
        rot.push(eintrag);
      } finally {
        await eigener?.close();
      }
    }
  } finally {
    await browser.close();
    await client.close();
  }
  console.table(ergebnisse.map(({ datei, kontakt, ...w }) => ({ datei: datei.replace(MODUS.ausgabe + "/", ""), ...w })));
  if (rot.length) { console.error(`ROT: ${rot.join(", ")}`); process.exit(1); }
  process.exit(0);
}
try {
  for (const theme of themes) {
    for (const name of szenen) {
      // README-0.10-Szenen gibt es nur hell (keine Hell/Dunkel-Dubletten im README)
      if (SZENEN[name].themes && !SZENEN[name].themes.includes(theme)) continue;
      console.log(`▶ ${name} (${theme})`);
      // Große WebGL-Flächen in eigenem Browser: danach lieferte der gemeinsame Browser in
      // host.e2e.mjs keine Screenshots mehr (Page.captureScreenshot, 10.11.)
      const eigener = SZENEN[name].eigenerBrowser ? await chromium.launch() : null;
      try {
        ergebnisse.push(await szene(eigener ?? browser, { name, theme, molecule: optionen.molecule, ...SZENEN[name] }));
      } finally {
        await eigener?.close();
      }
    }
  }
} finally {
  await browser.close();
  await client.close();
}
console.table(ergebnisse.map(({ datei, beats, ...w }) => ({ datei: datei.replace(repo + "/", "").replace(MODUS.ausgabe + "/", ""), ...w })));
if (optionen.video) for (const e of ergebnisse) console.log(`  ${e.szene}-${e.theme} Beats: ${JSON.stringify(e.beats)}`);
// Hero-Paar: jede Hero-Fassung hat exakt den HERO-Ausschnitt — damit sind views und 3d
// gleich groß, auch wenn sie in getrennten Läufen entstehen
const falsch = ergebnisse.filter((e) => !optionen.video && SZENEN[e.szene].hero && (e.breite !== HERO.breite || e.hoehe !== HERO.hoehe));
if (falsch.length) {
  console.error(`ROT: Hero-GIFs nicht ${HERO.breite}×${HERO.hoehe}: ` + falsch.map((e) => `${e.szene}-${e.theme} ${e.breite}×${e.hoehe}`).join(", "));
  process.exit(1);
}
