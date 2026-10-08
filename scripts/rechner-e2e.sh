#!/bin/sh
# Praktikumsrechner im echten Chromium durchspielen (außerhalb des Gates:
# braucht Netz, weil Pyodide vom CDN kommt). Startet einen lokalen Server an
# der Repo-Wurzel, löst eine Aufgabe richtig und eine zweimal falsch.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/build-web.sh" >/dev/null
cd "$ROOT/web/dist"
python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT
sleep 1
PW="$ROOT/chemdraw_tool/ui/node_modules/playwright/index.mjs" node --input-type=module <<'JS'
const { chromium } = await import(process.env.PW);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const fehler = [];
p.on("pageerror", (e) => fehler.push(e.message));
// DSGVO: keine einzige Anfrage an fremde Hosts
const fremd = [];
p.on("request", (r) => { const u = new URL(r.url()); if (u.protocol.startsWith("http") && u.host !== "127.0.0.1:8765") fremd.push(u.host); });
const t0 = Date.now();
await p.goto("http://127.0.0.1:8765/index.html");
await p.waitForSelector(".task", { timeout: 90000 });
const ms = Date.now() - t0;
const loesung = await p.evaluate(() => aufgabe.loesung);
await p.fill("#antwort", loesung.toFixed(3).replace(".", ","));
await p.click("button[type=submit]");
const ok = (await p.textContent(".verdict")).startsWith("Richtig");
await p.click("#next"); await p.waitForSelector(".task");
for (const x of ["1", "2"]) { await p.fill("#antwort", x); await p.click("button[type=submit]"); }
const wegOffen = await p.evaluate(() => document.getElementById("weg").open);
// pH-Block: Puffer-Aufgabe wählen und richtig lösen
await p.selectOption("#typ", "ph.puffer_aufgabe"); await p.waitForSelector(".task");
const phText = await p.textContent(".task");
const phLoesung = await p.evaluate(() => aufgabe.loesung);
await p.fill("#antwort", phLoesung.toFixed(2).replace(".", ","));
await p.click("button[type=submit]");
const phOk = (await p.textContent(".verdict")).startsWith("Richtig") && phText.includes("Puffer");
// Mechanismus: Auswahlknopf mit der richtigen Antwort drücken
await p.selectOption("#typ", "mechanismus.weg_aufgabe"); await p.waitForSelector(".choices");
const weg = await p.evaluate(() => aufgabe.loesung);
await p.click(`[data-wahl="${weg}"]`);
const mechOk = (await p.textContent(".verdict")).startsWith("Richtig");
// Löslichkeit: wissenschaftliche Schreibweise mit Komma und 10^
await p.selectOption("#typ", "loeslichkeit.zusatz_aufgabe"); await p.waitForSelector(".task");
const l = await p.evaluate(() => aufgabe.loesung);
const [mant, ex] = l.toExponential(3).split("e");
await p.fill("#antwort", `${mant.replace(".", ",")} · 10^${Number(ex)}`);
await p.click("button[type=submit]");
const loeslOk = (await p.textContent(".verdict")).startsWith("Richtig");
// Lösungsrechnen: Verdünnung richtig lösen
await p.selectOption("#typ", "loesungen.verduennung_aufgabe"); await p.waitForSelector(".task");
const v1 = await p.evaluate(() => aufgabe.loesung);
await p.fill("#antwort", v1.toFixed(2).replace(".", ","));
await p.click("button[type=submit]");
const loesOk = (await p.textContent(".verdict")).startsWith("Richtig");
// Pharmakokinetik: alle sieben Typen richtig lösen (Ionisierung und Akkumulation haben andere Einheiten)
let pkOk = true;
for (const typ of ["halbwertszeit", "konzentration", "steady_state", "aufsaettigung", "akkumulation", "ionisation", "tangente"]) {
  await p.selectOption("#typ", `pharmakokinetik.${typ}_aufgabe`); await p.waitForSelector(".task");
  const x = await p.evaluate(() => aufgabe.loesung);
  await p.fill("#antwort", x.toFixed(4).replace(".", ","));
  await p.click("button[type=submit]");
  if (!(await p.textContent(".verdict")).startsWith("Richtig")) { pkOk = false; console.error("PK rot:", typ, x); }
}
// Hilfsmittel: der Rechenweg der Tangenten-Aufgabe trägt den TI-Tastenweg bis zur Geradengleichung
await p.click("#weg summary");
const tiText = await p.textContent("#weg");
const tiOk = tiText.includes("5:Tangente(") && tiText.includes("y = m·x + b") && (await p.$$("#weg .st-ti")).length === 4;
if (!tiOk) console.error("TI-Tastenweg fehlt im Rechenweg");
// Klausurmodus: 10 Aufgaben, alle richtig beantworten → 10 von 10
await p.click("#klausur"); await p.waitForSelector(".task");
for (let i = 0; i < 10; i++) {
  const a = await p.evaluate(() => klausur.aufgaben[klausur.i]);
  if (a.auswahl) await p.click(`[data-wahl="${a.loesung}"]`);
  else { await p.fill("#antwort", String(a.loesung).replace(".", ",")); await p.click("button[type=submit]"); }
}
await p.waitForSelector("#ergebnis");
const klausurOk = (await p.textContent("#ergebnis")).startsWith("10 von 10");
// Offline: Service Worker abwarten, Netz kappen, neu laden, eine Aufgabe lösen
const swBereit = await p.evaluate(() => Promise.race([
  navigator.serviceWorker.ready.then(() => true),
  new Promise((ok) => setTimeout(() => ok(false), 20000)),
]));
if (!swBereit) { console.error("❌ Service Worker nach 20 s nicht aktiv"); await b.close(); process.exit(1); }
await p.reload(); await p.waitForSelector(".task");  // jetzt kontrolliert der SW die Seite
const ctx = p.context();
await ctx.setOffline(true);
await p.reload(); await p.waitForSelector(".task", { timeout: 60000 });
const offLoesung = await p.evaluate(() => aufgabe.auswahl ? null : aufgabe.loesung);
let offlineOk = false;
if (offLoesung === null) { offlineOk = true; } else {
  await p.fill("#antwort", String(offLoesung).replace(".", ",")); await p.click("button[type=submit]");
  offlineOk = (await p.textContent(".verdict")).startsWith("Richtig");
}
await ctx.setOffline(false);
await b.close();
if (!ok || !wegOffen || !phOk || !mechOk || !loeslOk || !loesOk || !pkOk || !tiOk || !klausurOk || !offlineOk || fehler.length || fremd.length) { console.error("❌ Rechner rot:", { ok, wegOffen, phOk, mechOk, loeslOk, loesOk, pkOk, tiOk, klausurOk, offlineOk, fehler, fremd: [...new Set(fremd)] }); process.exit(1); }
console.log(`✅ Rechner grün: geladen nach ${ms} ms, Titration, Puffer, Mechanismus, Löslichkeit (10^-Schreibweise), Verdünnung und alle sieben Pharmakokinetik-Typen richtig erkannt, TI-Tastenweg bis zur Tangentengleichung sichtbar, Klausur 10 von 10, offline nach Neuladen lauffähig, Rechenweg nach 2 Fehlversuchen offen, 0 Anfragen an fremde Hosts.`);
JS
