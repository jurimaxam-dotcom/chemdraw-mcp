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

// Fähigkeiten, die der Test-Host ohne eigene Angabe meldet (Stand vor U1).
const DEFAULT_CAPABILITIES = { serverTools: {}, updateModelContext: { text: {} }, message: { text: {} } };

// U1 (11.11.2026): Host-Kontext wie Claude Desktop. Im Chat `inline` mit
// {width, maxHeight}, im Seitenpanel/Vollbild `fullscreen` mit {width, height}.
// Der Host hält den ganzen Kontext selbst und setzt ihn immer vollständig:
// setHostContext schickt nur geänderte Felder, das Panel mischt flach — ein
// Feld, das hier fehlte, bliebe dort sonst stehen.
function fullContext(ctx) {
  return { safeAreaInsets: { top: 0, right: 0, bottom: 0, left: 0 }, ...ctx };
}

// Das iframe bekommt die gemeldete Größe, sonst misst der Test gegen 640×640.
// Bei `maxHeight` (Chat) bleibt die Höhe beim Test: Desktop übernimmt dort die
// Größenmeldung des Panels (__panelSizes).
function sizeFrame(iframe, ctx) {
  const dims = ctx?.containerDimensions;
  if (!dims) return;
  if (typeof dims.width === "number") iframe.style.width = `${dims.width}px`;
  if (typeof dims.height === "number") iframe.style.height = `${dims.height}px`;
}

// U3/U4 (11.11.2026): `hostCapabilities` schaltet `message`/`updateModelContext` an und ab;
// `messageMode` lässt ui/message gelingen ("ok"), ablehnen ("isError") oder scheitern ("reject");
// `holdResult` schickt nur toolinput — das Ergebnis kommt später per __sendToolResult,
// ein Abbruch per __cancelTool; `skipInput` lässt toolinput ganz weg.
// window.__bridgeLog hält Kontext-Updates und Nachrichten in ihrer Reihenfolge.
window.__startHost = async ({ html, toolInput, toolResult, prelude = "", hostContext, hostCapabilities,
  messageMode = "ok", holdResult = false, skipInput = false }) => {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.style.cssText = "width:640px;height:640px;border:0";
  const head = `<meta http-equiv="Content-Security-Policy" content="${CSP}">${prelude ? `<script>${prelude}</script>` : ""}`;
  iframe.srcdoc = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, (m) => m + head) : head + html;
  let context = hostContext ? fullContext(hostContext) : undefined;
  sizeFrame(iframe, context);
  document.body.appendChild(iframe);

  const bridge = new AppBridge(
    null,
    { name: "panel-test-host", version: "0.0.0" },
    hostCapabilities || DEFAULT_CAPABILITIES,
    context ? { hostContext: context } : undefined,
  );
  bridge.oncalltool = async (params) => window.__callTool(params);
  // Größenmeldung des Panels (ui/notifications/size-changed) wie Desktop
  // mitschreiben; die Tests entscheiden selbst, ob sie die Höhe übernehmen.
  window.__panelSizes = window.__panelSizes || [];
  bridge.onsizechange = (size) => { window.__panelSizes.push(size); };
  // Nachrichten und Modellkontext aus dem Panel: annehmen und mitschreiben.
  window.__messages = window.__messages || [];
  window.__bridgeLog = window.__bridgeLog || [];
  const textOf = (params) => (params?.content || []).map((c) => c.text || "").join("");
  bridge.onmessage = async (params) => {
    window.__messages.push(params);
    window.__bridgeLog.push(["message", textOf(params)]);
    if (messageMode === "isError") return { isError: true };
    if (messageMode === "reject") throw new Error("host refuses messages");
    return {};
  };
  window.__modelContexts = window.__modelContexts || [];
  bridge.onupdatemodelcontext = async (params) => {
    window.__modelContexts.push(params);
    window.__bridgeLog.push(["context", textOf(params)]);
    return {};
  };
  // Anzeigemodus: der Test-Host gewährt jede Anfrage und meldet danach den
  // neuen Modus mit passenden Maßen — wie Desktop beim Wechsel ins Seitenpanel.
  window.__displayModeRequests = window.__displayModeRequests || [];
  // Spätere Änderungen (Breite gezogen, Modus gewechselt): neuer Gesamtkontext.
  // Lokal gebunden: auf Seiten mit mehreren Panels gehört das globale
  // window.__setHostContext dem zuletzt gestarteten.
  const setContext = (ctx) => {
    context = fullContext(ctx);
    sizeFrame(iframe, context);
    bridge.setHostContext(context);
  };
  window.__setHostContext = setContext;
  bridge.onrequestdisplaymode = async ({ mode }) => {
    window.__displayModeRequests.push({ mode });
    const width = context?.containerDimensions?.width ?? iframe.clientWidth;
    const dims = mode === "fullscreen"
      ? { width, height: window.__fullscreenHeight ?? Math.max(iframe.clientHeight, 800) }
      : { width, maxHeight: 6000 };
    setContext({ ...(context || {}), displayMode: mode, containerDimensions: dims });
    return { mode };
  };
  // Folge-Ergebnisse im selben Panel (Chat ruft das Tool erneut): Fund b prüft so,
  // dass ein Fehler das alte Ergebnis ersetzt und ein Erfolg den Fehler.
  window.__sendToolResult = (result) => bridge.sendToolResult(result);
  window.__cancelTool = (reason) => bridge.sendToolCancelled({ reason });
  const ready = new Promise((resolve) => {
    bridge.oninitialized = async () => {
      if (!skipInput) await bridge.sendToolInput({ arguments: toolInput });
      if (!holdResult) await bridge.sendToolResult(toolResult);
      resolve();
    };
  });
  await bridge.connect(new PostMessageTransport(iframe.contentWindow, iframe.contentWindow));
  await ready;
};
