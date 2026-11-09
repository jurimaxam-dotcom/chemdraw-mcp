import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { useApp, useHostStyleVariables } from "@modelcontextprotocol/ext-apps/react";
import App from "./App";
import { AppContext } from "./AppContext";
import ToolError from "./components/ToolError";
import { extractToolData, extractToolError } from "./utils/toolData";
import "./styles.css";

function Root() {
  const [data, setData] = useState(null);
  // Meldung des letzten Tool-Fehlers. Ein Fehler ersetzt das alte Ergebnis:
  // stehen bliebe sonst ein Bild, das zur neuen Anfrage nicht gehört.
  const [toolError, setToolError] = useState(null);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "Chem-MCP", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (app) => {
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

  if (data)
    return (
      <AppContext.Provider value={app}>
        <App data={data} />
      </AppContext.Provider>
    );
  if (toolError) return <ToolError message={toolError} />;
  if (error) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connection error</div>;
  if (!isConnected) return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Connecting…</div>;
  return <div style={{ color: "var(--fg-muted)", padding: 16, fontSize: 12 }}>Waiting for data…</div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root />);
