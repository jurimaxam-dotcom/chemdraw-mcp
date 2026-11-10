// Nachgebauter Host für den Panel-Test: bettet die gebaute UI wie Claude Desktop in
// ein sandboxed iframe ein (srcdoc, ohne allow-same-origin) und spricht über die
// echte AppBridge des ext-apps-SDK. Tool-Aufrufe der UI (callServerTool) gehen über
// window.__callTool an den echten MCP-Server (Node-Seite, host.e2e.mjs).
import { AppBridge, PostMessageTransport } from "@modelcontextprotocol/ext-apps/app-bridge";

// Standard-CSP eines Hosts für eine Ressource ohne `_meta.ui.csp`
// (ext-apps-Spezifikation 2026-01-26, „default-src 'none' …“): kein eval, keine
// Blob-/Fremd-Skripte, Bilder nur data:. Seit E13 gesetzt, damit der Test die
// Grenzen sieht, die Claude Desktop setzen darf. `prelude` = Script vor dem
// Panel (der Test erzwingt damit z. B. „kein WebGL“).
const CSP = "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
  + "img-src 'self' data:; media-src 'self' data:; connect-src 'none'";

window.__startHost = async ({ html, toolInput, toolResult, prelude = "" }) => {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.style.cssText = "width:640px;height:640px;border:0";
  const head = `<meta http-equiv="Content-Security-Policy" content="${CSP}">${prelude ? `<script>${prelude}</script>` : ""}`;
  iframe.srcdoc = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, (m) => m + head) : head + html;
  document.body.appendChild(iframe);

  const bridge = new AppBridge(
    null,
    { name: "panel-test-host", version: "0.0.0" },
    { serverTools: {}, updateModelContext: { text: {} }, message: { text: {} } },
  );
  bridge.oncalltool = async (params) => window.__callTool(params);
  // Folge-Ergebnisse im selben Panel (Chat ruft das Tool erneut): Fund b prüft so,
  // dass ein Fehler das alte Ergebnis ersetzt und ein Erfolg den Fehler.
  window.__sendToolResult = (result) => bridge.sendToolResult(result);
  const ready = new Promise((resolve) => {
    bridge.oninitialized = async () => {
      await bridge.sendToolInput({ arguments: toolInput });
      await bridge.sendToolResult(toolResult);
      resolve();
    };
  });
  await bridge.connect(new PostMessageTransport(iframe.contentWindow, iframe.contentWindow));
  await ready;
};
