import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { useApp, useHostStyleVariables } from "@modelcontextprotocol/ext-apps/react";
import App from "./App";
import { AppContext, HostContext } from "./AppContext";
import HostDiagnostics from "./components/HostDiagnostics";
import ToolError from "./components/ToolError";
import { extractToolData, extractToolError } from "./utils/toolData";
import { useHostLayout } from "./utils/useHostLayout";
import "./styles.css";

function Root() {
  const [data, setData] = useState(null);
  // Meldung des letzten Tool-Fehlers. Ein Fehler ersetzt das alte Ergebnis:
  // stehen bliebe sonst ein Bild, das zur neuen Anfrage nicht gehört.
  const [toolError, setToolError] = useState(null);
  // Host-Kontext (U2): Größe und Modus → Attribute/Variablen an <html>.
  const { hostContext, attach, sync } = useHostLayout();

  const { app, isConnected, error } = useApp({
    appInfo: { name: "Chem-MCP", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (app) => {
      // Vor connect registrieren: nur dann mischt das SDK Kontextänderungen ein.
      attach(app);
      app.addEventListener("toolresult", (params) => {
        const message = extractToolError(params);
        if (message) {
          setData(null);
          setToolError(message);
          return;
        }
        const payload = extractToolData(params);
        if (payload) {
          setToolError(null);
          setData(payload);
        }
      });
    },
  });

  useHostStyleVariables(app, app?.getHostContext());
  useEffect(() => {
    if (app && isConnected) sync(app);
  }, [app, isConnected, sync]);

  if (data)
    return (
      <AppContext.Provider value={app}>
        <HostContext.Provider value={hostContext}>
          <HostDiagnostics app={app} hostContext={hostContext}>
            <App data={data} />
          </HostDiagnostics>
        </HostContext.Provider>
      </AppContext.Provider>
    );
  if (toolError) return <ToolError message={toolError} />;
  if (error) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connection error</div>;
  if (!isConnected) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connecting…</div>;
  return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Waiting for data…</div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root />);
