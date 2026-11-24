// End-to-End Host-Test für den Remote-Konnektor über echtes Streamable HTTP.
// Startet `python -m chempane.remote` auf einem freien Loopback-Port, ruft
// `/healthz` und `generate_molecule` über StreamableHTTPClientTransport auf
// und rendert das echte Panel in headless Chromium (sandboxed iframe + AppBridge).
import { Client, StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
import { build } from "esbuild";
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const pyBin = join(repo, ".venv", "bin", "python");
if (!existsSync(pyBin)) throw new Error("venv fehlt — erst `uv sync`");

function freePort() {
  return new Promise((resolve, reject) => {
    const s = createServer();
    s.listen(0, "127.0.0.1", () => {
      const { port } = s.address();
      s.close(() => resolve(port));
    });
    s.on("error", reject);
  });
}

async function waitHealth(url, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(url);
      if (r.ok) return await r.json();
    } catch {
      // server still starting
    }
    await new Promise((r) => setTimeout(r, 150));
  }
  throw new Error(`Remote server did not become healthy at ${url}`);
}

const port = await freePort();
const baseUrl = `http://127.0.0.1:${port}`;
const wegwerfHome = mkdtempSync(join(tmpdir(), "chempane-remote-home-"));
const proc = spawn(pyBin, ["-m", "chempane.remote"], {
  cwd: repo,
  env: {
    ...process.env,
    HOME: wegwerfHome,
    CHEMPANE_REMOTE_HOST: "127.0.0.1",
    CHEMPANE_REMOTE_PORT: String(port),
    CHEMPANE_REMOTE_RATE_LIMIT: "60",
  },
  stdio: ["ignore", "pipe", "pipe"],
});

let stderr = "";
proc.stderr.on("data", (d) => { stderr += d.toString(); });

const check = (ok, msg) => {
  if (!ok) throw new Error("ROT: " + msg);
  console.log("✔", msg);
};

let browser;
const client = new Client({ name: "remote-panel-e2e", version: "0.0.0" });

try {
  const health = await waitHealth(`${baseUrl}/healthz`);
  check(health.status === "ok" && health.service === "chempane-remote", `/healthz ok (${health.version})`);

  const transport = new StreamableHTTPClientTransport(new URL(`${baseUrl}/mcp`));
  await client.connect(transport);

  const { tools } = await client.listTools();
  check(tools.length === 1 && tools[0].name === "generate_molecule", "Remote bietet genau 1 Tool: generate_molecule");
  check(tools[0].annotations?.readOnlyHint === true, "generate_molecule ist readOnlyHint=true");
  const resourceUri = tools[0]._meta?.ui?.resourceUri;
  check(resourceUri === "ui://chem-app/index.html", `Panel-Resource registriert (${resourceUri})`);

  const args = { name_or_smiles: "CC(=O)Oc1ccccc1C(=O)O", label: "Aspirin" };
  const result = await client.callTool({ name: "generate_molecule", arguments: args });
  check(!result.isError, "Streamable HTTP: generate_molecule(Aspirin) erfolgreich");
  const sc = result.structuredContent;
  check(sc?.remote === true && Object.keys(sc.files || {}).length === 0, "Payload trägt remote=true und keine lokalen Dateien");
  check((sc.functionalGroups || []).some((g) => g.name === "Carbonsäure"), "Funktionsgruppen vorhanden (Carbonsäure)");

  const resource = await client.readResource({ uri: resourceUri });
  const out = join(mkdtempSync(join(tmpdir(), "remote-host-")), "host.js");
  await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });

  browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1000 } });
  await page.setContent('<body style="margin:0"></body>');
  await page.addScriptTag({ path: out });
  await page.exposeFunction("__callTool", (req) => client.callTool(req));

  const hostContext = {
    displayMode: "inline",
    availableDisplayModes: ["inline", "fullscreen"],
    platform: "web",
    containerDimensions: { width: 860, maxHeight: 6000 },
  };
  await page.evaluate((a) => window.__startHost(a), {
    html: resource.contents[0].text,
    toolInput: args,
    toolResult: result,
    hostContext,
  });

  const frame = page.frames().at(-1);
  await frame.waitForSelector(".structure-canvas svg");
  check(true, "Panel rendert 2D-SVG im sandboxed Host-Iframe");

  const uiState = await frame.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role="tab"]')].map((e) => e.textContent.trim());
    const axis = [...document.querySelectorAll("[data-view-axis] button")].map((e) => e.textContent.trim());
    const groups = [...document.querySelectorAll('[aria-label="Functional groups"] button')].map((e) => e.textContent.trim());
    const hasAnki = Boolean(document.querySelector(".add-anki"));
    const hasFiles = Boolean(document.querySelector(".panel-footer-file"));
    return { tabs, axis, groups, hasAnki, hasFiles };
  });

  check(uiState.groups.length >= 2, `Sichtbare Funktionsgruppen im Panel (${uiState.groups.join(", ")})`);
  check(JSON.stringify(uiState.tabs) === JSON.stringify(["Structure", "Study"]), `Keine Data-Tab im Remote-Panel (${uiState.tabs.join(", ")})`);
  check(uiState.axis.includes("2D") && uiState.axis.includes("All H") && !uiState.axis.includes("3D"), `Ansicht-Achse ohne 3D (${uiState.axis.join(", ")})`);
  check(!uiState.hasAnki && !uiState.hasFiles, "Kein Add-to-Anki und keine lokalen Dateipfade im Panel");

  // Interaktivität: Gruppe anpinnen + All H über Streamable HTTP nachladen
  const firstChip = frame.locator('[aria-label="Functional groups"] button').first();
  await firstChip.click();
  check((await firstChip.getAttribute("aria-pressed")) === "true", "Klick auf Funktionsgruppe pinnt Auswahl im Panel");

  const allH = frame.locator("[data-view-axis] button", { hasText: "All H" });
  await allH.click();
  await frame.waitForFunction(() => {
    const btn = [...document.querySelectorAll("[data-view-axis] button")].find((b) => b.textContent.trim() === "All H");
    return btn?.getAttribute("aria-pressed") === "true";
  });
  check(true, "All-H-Ansicht über Streamable HTTP im Panel nachgeladen");

  console.log("✅ Remote-Host-Test über Streamable HTTP komplett grün.");
} finally {
  await browser?.close();
  await client.close().catch(() => {});
  proc.kill("SIGTERM");
  if (stderr && process.env.DEBUG_REMOTE_E2E) console.error(stderr);
}
