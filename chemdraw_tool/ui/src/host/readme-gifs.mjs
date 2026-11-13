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
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync, statSync, writeFileSync, copyFileSync } from "node:fs";
import { tmpdir, homedir } from "node:os";
import { execFileSync } from "node:child_process";

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
// Fester Ausschnitt der Hero-Szenen: beide GIFs exakt gleich groß (Jay 07.11.). 880 px = 3D-Panel
// mit Kuhle, Achse, Kennwerten, Drag-Hinweis und Fußzeile (seit E3) plus 12 px Rand unten wie oben.
const HERO = { breite: BREITE_DESKTOP, hoehe: Number(process.env.HERO_HOEHE || 880) };
const GRENZEN = { breite: 800, sekunden: 10, bytes: 3 * 1024 * 1024 };

// Argumente: Szenennamen, --theme light|dark, --molecule NAME (auch --x=wert), --video
const gewählt = [], optionen = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  const m = a.match(/^--(theme|molecule)(?:=(.*))?$/);
  if (m) optionen[m[1]] = m[2] ?? process.argv[++i];
  else if (a === "--video") optionen.video = true;
  else if (a.startsWith("--")) throw new Error(`unbekannte Option: ${a} (--theme, --molecule, --video)`);
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
};
const MODUS = optionen.video ? MODI.video : MODI.gif;
const TAKT = MODUS.takt;

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

async function szene(browser, { name, tool, args, hoehe, videoHoehe, fps, ablauf, theme, molecule,
  breite: BREITE = BREITE_DESKTOP, panel = ".molecule-panel", vorlauf, datei, farben = 128, sekunden }) {
  if (optionen.video) { hoehe = videoHoehe ?? hoehe; fps = MODUS.fps; }
  if (molecule) args = { ...args, name_or_smiles: molecule };
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
  await ablauf({ frame, page, halten, zeigeAuf, klick, zeiger, mitte, imBild, marke });
  const ende = uhr.jetzt();
  marke("ende");
  aufnahme = false;
  await schleife;
  await context.close();
  const quellFps = Number((bilder.length / (ende / 1000)).toFixed(1));
  if (optionen.video) return { szene: name, theme, quellFps, ...videoBauen(`${name}-${theme}`, bilder, ende, dir, hoehe, beats, { tool, args }, BREITE) };
  const werte = gifBauen(datei ?? `demo-${name}-${theme}`, bilder, ende, fps, dir, farben, sekunden);
  // Alte Namen ohne Theme bleiben als Kopie der hellen Fassung: PyPI und ältere
  // Release-Notes verlinken sie absolut (nur mit dem Standardmolekül der Szene)
  if (theme === "light" && !molecule && !datei) copyFileSync(werte.datei, join(MODUS.ausgabe, `demo-${name}.gif`));
  return { szene: name, theme, ...werte };
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
async function datenblattMitCas({ frame, page, halten, zeiger, marke }, gesamtMs) {
  const cas = frame.getByText("CAS No.", { exact: true }).first();
  if (!(await cas.count())) throw new Error("Datenblatt ohne CAS-Zeile");
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

// Drehzug per Pointer-Drag, mit sichtbarem Zeiger
async function ziehen({ page, halten, zeiger, marke }, von, nach, ms, ziel) {
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

// Bluesky-Folgeposts (0.10.0): nur hell, nur auf Ansage, 6–12 s, Ausgabe über GIF_AUSGABE
const BLUESKY = { themes: ["light"], fps: 12, nurGif: true, aufAnsage: true, sekunden: [6, 12], breite: 600 };

// README 0.10: eine zusammenhängende Interaktion je GIF, nur hell, Ausgabe unter eigenem Namen
// (assets/<datei>.gif). Breite und Höhe so, dass das ganze Panel samt Export-Knopf im Bild ist —
// abgeschnitten wird nichts; flacher wird das Bild über die Breite, nicht über einen Ausschnitt.
const README_010 = { themes: ["light"], fps: 15, nurGif: true };

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
    async ablauf({ frame, page, halten, klick, zeiger, mitte, imBild, marke }) {
      await frame.locator(".structure-canvas svg").first().waitFor();
      await halten(TAKT.start);
      await klick(frame.getByRole("button", { name: "3D", exact: true }), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }), "3D");
      await imBild(frame.locator("[data-view-3d]"), "3D-Kuhle");
      await imBild(frame.locator("[data-view-axis]"), "Ansicht-Achse");
      await imBild(frame.locator(".key-facts"), "Kennwerte");
      await imBild(frame.locator(".molecule-panel"), "Panel samt Drag-Hinweis");
      await halten(TAKT.vor3D); // Einblend-Drehung (1200 ms) läuft zu Ende
      const [cx, cy] = await mitte(frame.locator("[data-view-3d]"));
      const zug = (von, nach, ms, ziel) => ziehen({ page, halten, zeiger, marke }, von, nach, ms, ziel);
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
    ...README_010, datei: "hero-capsaicin", breite: 800, hoehe: 692,
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
    ...README_010, datei: "hero-caffeine-3d", breite: 600, hoehe: 860, fps: 12,
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
    ...README_010, datei: "lysozyme-cartoon", breite: 600, hoehe: 812, fps: 12, farben: 96, eigenerBrowser: true,
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
  // β-D-Glucose: Ansicht-Achse einmal durch — 2D → Fischer → Haworth → Chair → 3D
  "sugar-views": {
    ...BLUESKY, datei: "sugar-views", hoehe: 1080,
    tool: "generate_molecule", args: { name_or_smiles: "beta-D-glucose" },
    async ablauf({ frame, halten, klick, imBild }) {
      const achse = frame.locator("[data-view-axis]");
      const knopf = (text) => achse.getByRole("button", { name: text, exact: true });
      const gedrückt = (text) => achse.locator('button[aria-pressed="true"][aria-busy="false"]', { hasText: text });
      await frame.locator(".structure-canvas svg").first().waitFor();
      for (const v of ["Fischer", "Haworth", "Chair", "3D"])
        if (!(await knopf(v).count())) throw new Error(`sugar-views: kein Knopf ${v}`);
      await imBild(achse, "Ansicht-Achse");
      await halten(1300);
      for (const v of ["Fischer", "Haworth", "Chair"]) {
        await klick(knopf(v), () => gedrückt(v).waitFor({ timeout: 30000 }), v);
        await halten(1400);
      }
      await klick(knopf("3D"), () => frame.locator("[data-view-3d] svg circle").first().waitFor({ timeout: 30000 }), "3D");
      await imBild(frame.locator("[data-view-3d]"), "3D-Kuhle");
      await imBild(frame.locator(".panel-footer"), "Fußzeile");
      await halten(2000); // Einblend-Drehung (1200 ms) läuft zu Ende
    },
  },
  // SN2 mit (R)-2-Brombutan + Cyanid: Overview → Step by step → mit Next durch alle Schritte
  "mechanism-steps": {
    ...BLUESKY, datei: "mechanism-steps", hoehe: 560, panel: "button:has-text(\"Step by step\")",
    tool: "generate_mechanism", args: { reaction_type: "sn2", substrates: ["(R)-2-bromobutane", "cyanide"] },
    async ablauf({ frame, halten, klick }) {
      await halten(1500);
      await klick(frame.getByRole("button", { name: "Step by step", exact: true }), () => frame.getByText(/^Step 1 \/ \d+$/).waitFor({ timeout: 5000 }), "Step by step");
      const gesamt = Number((await frame.getByText(/^Step 1 \/ \d+$/).innerText()).split("/")[1]);
      await halten(1600);
      for (let i = 2; i <= gesamt; i++) {
        await klick(frame.getByRole("button", { name: "Next →" }), () => frame.getByText(`Step ${i} / ${gesamt}`, { exact: true }).waitFor({ timeout: 5000 }), "Next");
        await halten(i === gesamt ? 2200 : 1600);
      }
    },
  },
  // H₂ + O₂ → H₂O, so gezeichnet nicht ausgeglichen: Badge zeigen, dann „Apply coefficients“
  "reaction-balance": {
    ...BLUESKY, datei: "reaction-balance", hoehe: 236, panel: ".reaction-panel",
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
    ...BLUESKY, datei: "antibody-scheme", hoehe: 912, farben: 96, eigenerBrowser: true,
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
  // Aspirin: zwei Gruppen-Chips, dann „Add to Anki“ → „Saved“ (Testhost: deliver apkg, kein Anki)
  anki: {
    ...BLUESKY, datei: "anki", hoehe: 900,
    tool: "generate_molecule", args: { name_or_smiles: "aspirin" },
    async ablauf({ frame, page, halten, zeigeAuf, klick, zeiger, mitte, imBild }) {
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
      await zeiger(ax - 40, ay - 46); await page.mouse.move(ax - 40, ay - 46, { steps: 4 });
      await halten(1600); // „Saved“ steht 2,5 s ab dem Klick (Echtzeit), danach setzt der Knopf zurück
      if (!(await anki.innerText()).includes("Saved")) throw new Error("ROT anki: am Ende kein „Saved“ mehr");
    },
  },
};

if (optionen.theme && !THEMES[optionen.theme]) throw new Error(`--theme light|dark, nicht ${optionen.theme}`);
const themes = optionen.theme ? [optionen.theme] : Object.keys(THEMES);
const szenen = gewählt.length ? gewählt : Object.keys(SZENEN).filter((n) => !SZENEN[n].aufAnsage && !(optionen.video && SZENEN[n].nurGif));
for (const name of szenen) if (!SZENEN[name]) throw new Error(`unbekannte Szene: ${name} (${Object.keys(SZENEN).join(", ")})`);
mkdirSync(MODUS.ausgabe, { recursive: true });
const browser = await chromium.launch();
const ergebnisse = [];
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
