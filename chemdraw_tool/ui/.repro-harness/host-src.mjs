// Minimal-Host: spricht das ext-apps-1.x-Protokoll gegen unser Panel-iframe.
import { AppBridge, PostMessageTransport } from "@modelcontextprotocol/ext-apps/app-bridge";

window.__status = "booting";

async function main() {
  const payloadFile = new URLSearchParams(location.search).get("payload") || "payload.json";
  const payload = await (await fetch("/" + payloadFile)).json();
  const iframe = document.getElementById("app");

  const transport = new PostMessageTransport(iframe.contentWindow, iframe.contentWindow);
  const bridge = new AppBridge(
    null,
    { name: "repro-host", version: "1.0.0" },
    {}
  );
  bridge.oninitialized = () => {
    console.log("[host] View hat initialized gesendet — sende toolResult");
    window.__status = "initialized";
    bridge.sendToolResult(payload);
    window.__status = "result-sent";
  };
  console.log("[host] verbinde AppBridge…");
  await bridge.connect(transport);
  window.__status = "bridge-connected";
  iframe.src = "/app.html";
  console.log("[host] AppBridge verbunden, warte auf ui/initialize der View");
}

main().catch((e) => {
  console.error("[host] FEHLER:", e?.message || e);
  window.__status = "error: " + (e?.message || e);
});
