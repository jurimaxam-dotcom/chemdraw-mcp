// Panel hinter einem ZWEITEN, fremden Host: dem offiziellen MCP Inspector (Web).
// `test:host` prüft das Panel hinter unserer eigenen AppBridge-Seite — ein Fehler, den
// Panel und Testhost gemeinsam haben, bleibt dort unsichtbar. Hier rendert ein Host, den
// wir nicht geschrieben haben, jedes Panel-Tool einmal: Deep-Link → Tool-Aufruf am echten
// Server (Streamable HTTP, scripts/dev_http.py) → Panel im Sandbox-iframe.
// Rezept: inspector/docs/mcp-app-review.md. Nicht im Gate (npx lädt den Inspector, Netz).
//
//   npm --prefix chemdraw_tool/ui run test:inspector            # alle Panel-Tools
//   npm --prefix chemdraw_tool/ui run test:inspector generate_3d
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtempSync, readFileSync, existsSync, readdirSync } from "node:fs";
import { tmpdir, homedir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const INSPECTOR = "@modelcontextprotocol/inspector@2.15.0"; // exakt gepinnt wie in handshake.sh
const repo = join(dirname(fileURLToPath(import.meta.url)), "../../../..");
const beispiele = JSON.parse(readFileSync(join(repo, "evals/panel-beispiele.json"), "utf8"));
const wahl = process.argv.slice(2);
const unbekannt = wahl.filter((n) => !beispiele[n] || beispiele[n].auslassen);
if (unbekannt.length) { console.error(`ABBRUCH: kein Beispiel für ${unbekannt.join(", ")}`); process.exit(2); }
const tools = Object.entries(beispiele).filter(([n, b]) => !b.auslassen && (!wahl.length || wahl.includes(n)));

const [SERVER, WEB, SANDBOX] = [8765, 6274, 6275];
const token = randomBytes(24).toString("hex");
const wegwerfHome = mkdtempSync(join(tmpdir(), "inspector-home-"));
const shots = mkdtempSync(join(tmpdir(), "inspector-shots-"));
const echtesOutput = join(homedir(), "ChemDraw-Output");
const zaehle = (d) => (existsSync(d) ? readdirSync(d, { recursive: true }).length : 0);
const vorher = zaehle(echtesOutput);

const kinder = [];
const start = (cmd, args, env) => {
  const k = spawn(cmd, args, { cwd: repo, env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "pipe"], detached: true });
  let log = "";
  k.stdout.on("data", (d) => (log += d)); k.stderr.on("data", (d) => (log += d));
  kinder.push(k);
  return () => log;
};
const ende = (code) => { for (const k of kinder) { try { process.kill(-k.pid); } catch { /* schon weg */ } } process.exit(code); };
const wartePort = async (url, name, log) => {
  for (let i = 0; i < 120; i++) {
    try { await fetch(url); return; } catch { await new Promise((r) => setTimeout(r, 500)); }
  }
  console.error(`ABBRUCH: ${name} antwortet nicht auf ${url}\n${log().slice(-800)}`); ende(2);
};

// venv-Binärdatei direkt (uv bräuchte das echte HOME); HOME = Wegwerf-Ordner wie in host.e2e.mjs
const serverLog = start(join(repo, ".venv/bin/python"), ["scripts/dev_http.py"], { HOME: wegwerfHome, CHEMDRAW_PROFILE: "mvp", PORT: String(SERVER) });
const inspLog = start("npx", ["-y", INSPECTOR, "--web"], {
  HOST: "127.0.0.1", CLIENT_PORT: String(WEB), MCP_SANDBOX_PORT: String(SANDBOX),
  MCP_AUTO_OPEN_ENABLED: "false", MCP_INSPECTOR_API_TOKEN: token,
});
await wartePort(`http://127.0.0.1:${SERVER}/mcp`, "Server", serverLog);
await wartePort(`http://127.0.0.1:${WEB}/`, "Inspector", inspLog);

const browser = await chromium.launch();
let rot = 0;
for (const [name, b] of tools) {
  const page = await browser.newPage({ viewport: { width: 1300, height: 1000 } });
  const fehler = [];
  page.on("pageerror", (e) => fehler.push(String(e).slice(0, 200)));
  const args = Buffer.from(JSON.stringify(b.args)).toString("base64url");
  const url = `http://127.0.0.1:${WEB}/?serverUrl=${encodeURIComponent(`http://127.0.0.1:${SERVER}/mcp`)}` +
    `&transport=http&autoConnect=${token}&openApp=${name}&appArgs=${args}&autoOpen=${token}`;
  let grund = "";
  try {
    await page.goto(url);
    await page.waitForSelector('[data-testid="connection-status"][data-status="connected"]', { timeout: 20000 });
    await page.waitForSelector('[data-app-status="ready"]', { timeout: 40000 });
    const panel = page.frameLocator('iframe').frameLocator('iframe');
    await panel.locator(b.bereit).first().waitFor({ timeout: 60000 });
    const text = await panel.locator("body").innerText();
    if (/Waiting for data/i.test(text)) grund = "Panel wartet noch auf Daten";
    else if (await panel.locator('[data-testid="tool-error"]').count()) grund = `Panel zeigt einen Fehler: ${text.replace(/\s+/g, " ").slice(0, 160)}`;
    else if (fehler.length) grund = `JS-Fehler: ${fehler[0]}`;
  } catch (e) {
    const status = await page.locator('[data-testid="connection-status"]').first().getAttribute("data-error-message").catch(() => null);
    grund = `${String(e.message).split("\n")[0].slice(0, 160)}${status ? ` · Inspector: ${status}` : ""}`;
  }
  await page.screenshot({ path: join(shots, `${name}.png`) });
  await page.close();
  rot += Boolean(grund);
  console.log(`${grund ? "✘" : "✔"} ${name}${grund ? `\n    ${grund}` : ""}`);
}
await browser.close();

const nachher = zaehle(echtesOutput);
if (nachher !== vorher) { console.log(`✘ ~/ChemDraw-Output hat sich verändert (${vorher} → ${nachher} Einträge): der Wegwerf-HOME greift nicht`); rot += 1; }
console.log(`\n${tools.length - Math.min(rot, tools.length)}/${tools.length} Panels grün · Screenshots: ${shots}`);
ende(rot ? 1 : 0);
