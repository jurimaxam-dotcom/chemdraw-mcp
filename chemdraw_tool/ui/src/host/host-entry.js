// Nachgebauter Host für den Panel-Test: bettet die gebaute UI wie Claude Desktop in
// ein sandboxed iframe ein (srcdoc, ohne allow-same-origin) und spricht über die
// echte AppBridge des ext-apps-SDK. Tool-Aufrufe der UI (callServerTool) gehen über
// window.__callTool an den echten MCP-Server (Node-Seite, host.e2e.mjs).
import { AppBridge, PostMessageTransport } from "@modelcontextprotocol/ext-apps/app-bridge";

window.__startHost = async ({ html, toolInput, toolResult }) => {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.style.cssText = "width:640px;height:640px;border:0";
  iframe.srcdoc = html;
  document.body.appendChild(iframe);

  const bridge = new AppBridge(
    null,
    { name: "panel-test-host", version: "0.0.0" },
    { serverTools: {}, updateModelContext: { text: {} }, message: { text: {} } },
  );
  bridge.oncalltool = async (params) => window.__callTool(params);
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
