#!/bin/sh
# Praktikumsrechner im echten Chromium durchspielen (außerhalb des Gates:
# braucht Netz, weil Pyodide vom CDN kommt). Startet einen lokalen Server an
# der Repo-Wurzel, löst eine Aufgabe richtig und eine zweimal falsch.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
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
const t0 = Date.now();
await p.goto("http://127.0.0.1:8765/web/praktikumsrechner/index.html");
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
await b.close();
if (!ok || !wegOffen || !phOk || !mechOk || !loeslOk || fehler.length) { console.error("❌ Rechner rot:", { ok, wegOffen, phOk, mechOk, loeslOk, fehler }); process.exit(1); }
console.log(`✅ Rechner grün: geladen nach ${ms} ms, Titration, Puffer, Mechanismus und Löslichkeit (10^-Schreibweise) richtig erkannt, Rechenweg nach 2 Fehlversuchen offen.`);
JS
